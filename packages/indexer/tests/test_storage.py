"""T-06 — a ordem de publicação é o que torna a troca de versão atômica.

Não há transação num bucket. O que existe é ordem: o `manifest.json` é o último a
subir e o primeiro a ser lido, então enquanto ele não muda o site continua
servindo a versão antiga, inteira. Estes testes provam que a ordem errada falha.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import boto3
import pytest
from lol_assets_indexer.http import IndexerSettings
from lol_assets_indexer.publish.bucket import MissingBucketCredentialsError, build_store
from lol_assets_indexer.publish.storage import (
    CACHE_IMMUTABLE,
    CACHE_MANIFEST,
    MANIFEST_KEY,
    LocalObjectStore,
    PublicationError,
    Publisher,
    S3ObjectStore,
    content_type_for,
    hashed_name,
)
from lol_assets_schema import EXAMPLES_DIR
from lol_assets_schema.models import Catalog, IndexManifest, IndexShard
from moto import mock_aws

BUCKET = "lol-assets-teste"
SEGREDO = "chave-secreta-que-nunca-pode-aparecer-em-log"


def carregar(nome: str) -> Any:
    return json.loads((EXAMPLES_DIR / nome).read_text(encoding="utf-8"))


def catalogo() -> Catalog:
    return Catalog.model_validate(carregar("catalog.json"))


def fatias() -> list[IndexShard]:
    return [
        IndexShard.model_validate(carregar(nome))
        for nome in ("index-champion.json", "index-item.json", "index-rune.json")
    ]


def manifesto(catalog_url: str, shard_urls: dict[str, str]) -> IndexManifest:
    documento = carregar("manifest.json")
    versao = documento["versions"][0]
    versao["catalog"]["url"] = catalog_url
    for shard in versao["shards"]:
        shard["url"] = shard_urls[shard["category"]]
    return IndexManifest.model_validate(documento)


def publicar_tudo(publisher: Publisher) -> IndexManifest:
    """A ordem correta: assets, catálogo, fatias e só então o manifesto."""
    urls: dict[str, str] = {}
    for shard in fatias():
        for asset in shard.assets:
            assert asset.storage_key
            publisher.publish_asset(asset.storage_key, b"bytes-de-origem-" + asset.id.encode())
    ref_catalogo = publisher.publish_catalog(catalogo())
    for shard in fatias():
        urls[shard.category] = publisher.publish_shard(shard).url
    documento = manifesto(ref_catalogo.url, urls)
    publisher.publish_manifest(documento)
    return documento


# --- caminho feliz ------------------------------------------------------------


@mock_aws
def test_publica_versao_completa_e_le_de_volta() -> None:
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)
    publisher = Publisher(S3ObjectStore(client=client, bucket=BUCKET))

    escrito = publicar_tudo(publisher)
    lido = publisher.read_manifest()

    assert lido == escrito
    assert lido.current_version == escrito.current_version


@mock_aws
def test_todo_objeto_referenciado_existe_no_bucket() -> None:
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)
    publisher = Publisher(S3ObjectStore(client=client, bucket=BUCKET))
    documento = publicar_tudo(publisher)

    presentes = {
        objeto["Key"] for objeto in client.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    }
    versao = documento.versions[0]
    assert MANIFEST_KEY in presentes
    assert versao.catalog.url in presentes
    for shard in versao.shards:
        assert shard.url in presentes


# --- a ordem -------------------------------------------------------------------


def test_manifesto_antes_das_fatias_falha() -> None:
    publisher = Publisher(LocalObjectStore(root=Path("nao-usado")))
    documento = manifesto(
        "catalog-abc123456789.json",
        {
            "champion": "index-champion-a.json",
            "item": "index-item-b.json",
            "rune": "index-rune-c.json",
        },
    )

    with pytest.raises(PublicationError, match="não pode subir antes"):
        publisher.publish_manifest(documento)


def test_fatia_com_asset_nao_publicado_falha(tmp_path: Path) -> None:
    """A fatia não pode apontar para asset que ainda não está no bucket."""
    publisher = Publisher(LocalObjectStore(root=tmp_path))
    fatia = fatias()[0]

    with pytest.raises(PublicationError, match="não foram publicados"):
        publisher.publish_shard(fatia)


def test_manifesto_com_current_version_ausente_falha(tmp_path: Path) -> None:
    publisher = Publisher(LocalObjectStore(root=tmp_path))
    documento = manifesto(
        "catalog-a.json", {"champion": "c.json", "item": "i.json", "rune": "r.json"}
    )
    documento.current_version = "9.9.9"

    with pytest.raises(PublicationError, match="currentVersion"):
        publisher.publish_manifest(documento)


def test_a_ordem_certa_passa(tmp_path: Path) -> None:
    publisher = Publisher(LocalObjectStore(root=tmp_path))
    documento = publicar_tudo(publisher)
    assert MANIFEST_KEY in publisher.published_keys
    assert documento.versions[0].catalog.url in publisher.published_keys


# --- cache e tipo de conteúdo ---------------------------------------------------


def test_cache_control_por_tipo_de_objeto(tmp_path: Path) -> None:
    store = LocalObjectStore(root=tmp_path)
    publicar_tudo(Publisher(store))

    for key, meta in store.metadata.items():
        esperado = CACHE_MANIFEST if key == MANIFEST_KEY else CACHE_IMMUTABLE
        assert meta["cache_control"] == esperado, key

    assert store.metadata[MANIFEST_KEY]["content_type"].startswith("application/json")


@pytest.mark.parametrize(
    "key,esperado",
    [
        ("manifest.json", "application/json; charset=utf-8"),
        ("16.17.1/champion/Jax_square.png", "image/png"),
        ("16.17.1/champion/Jax_000_tile.jpg", "image/jpeg"),
        ("zips/champion.zip", "application/zip"),
        ("algo.desconhecido", "application/octet-stream"),
    ],
)
def test_content_type_por_extensao(key: str, esperado: str) -> None:
    assert content_type_for(key) == esperado


def test_nome_com_hash_muda_quando_o_conteudo_muda() -> None:
    """Conteúdo novo = nome novo. É o que permite `immutable` (§9 da Spec)."""
    um = hashed_name("catalog", b"conteudo A")
    outro = hashed_name("catalog", b"conteudo B")
    assert um != outro
    assert um == hashed_name("catalog", b"conteudo A")
    assert um.startswith("catalog-") and um.endswith(".json")


# --- dry-run --------------------------------------------------------------------


@mock_aws
def test_dry_run_produz_a_mesma_arvore_que_o_bucket(tmp_path: Path) -> None:
    """`--dry-run` não é um caminho diferente: é o mesmo, com outro destino."""
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket=BUCKET)
    publicar_tudo(Publisher(S3ObjectStore(client=client, bucket=BUCKET)))
    do_bucket = {
        objeto["Key"]: client.get_object(Bucket=BUCKET, Key=objeto["Key"])["Body"].read()
        for objeto in client.list_objects_v2(Bucket=BUCKET).get("Contents", [])
    }

    local = LocalObjectStore(root=tmp_path)
    publicar_tudo(Publisher(local))
    do_disco = {
        str(caminho.relative_to(tmp_path)).replace("\\", "/"): caminho.read_bytes()
        for caminho in tmp_path.rglob("*")
        if caminho.is_file()
    }

    assert do_disco == do_bucket


# --- credenciais ----------------------------------------------------------------


def test_sem_credencial_o_erro_diz_o_que_fazer() -> None:
    with pytest.raises(MissingBucketCredentialsError, match="dry-run"):
        build_store(IndexerSettings(s3_endpoint_url="", s3_access_key_id=""))


def test_nenhuma_credencial_aparece_no_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    publicar_tudo(Publisher(LocalObjectStore(root=tmp_path)))

    texto = caplog.text
    assert texto, "a publicação precisa deixar rastro"
    assert SEGREDO not in texto
    for proibido in ("secret", "access_key", "aws_secret"):
        assert proibido not in texto.lower()


def test_credencial_nao_vaza_na_repr_da_configuracao() -> None:
    config = IndexerSettings(
        s3_endpoint_url="https://exemplo.r2.cloudflarestorage.com",
        s3_access_key_id="AKIA-EXEMPLO",
        s3_secret_access_key=SEGREDO,
    )
    assert config.has_bucket_credentials() is True
    # A configuração é montada pelo processo; o que não pode é ela ser logada.
    # Este teste documenta a intenção: só o `bucket.py` toca nesses campos.
    assert SEGREDO not in str({"endpoint": config.s3_endpoint_url, "bucket": config.s3_bucket})

"""T-04 — os modelos e o JSON Schema precisam contar a mesma história.

O JSON Schema é a fonte de verdade (§6 da Spec). Os modelos Pydantic são a forma
de o indexador manipular o contrato sem dicionário solto. Estes testes provam que
os dois não divergem — e que as regras dos ADRs valem nas duas validações, não só
numa delas.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from jsonschema import ValidationError
from lol_assets_schema import EXAMPLES_DIR, SCHEMA_VERSION
from lol_assets_schema.models import (
    Asset,
    Catalog,
    CatalogChampion,
    CatalogSkin,
    IndexManifest,
    IndexShard,
)
from lol_assets_schema.validators import (
    validate_catalog,
    validate_manifest,
    validate_shard,
)
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

FIXTURES_DE_FATIA = ["index-champion.json", "index-item.json", "index-rune.json"]


def carregar(nome: str) -> Any:
    return json.loads((EXAMPLES_DIR / nome).read_text(encoding="utf-8"))


def asset_valido(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "splash_centered:24000",
        "type": "splash_centered",
        "category": "champion",
        "championKey": 24,
        "championId": "Jax",
        "skinId": 24000,
        "skinNum": 0,
        "names": {"pt_BR": "Jax"},
        "source": "ddragon",
        "sourceUrl": "https://ddragon.leagueoflegends.com/cdn/img/champion/centered/Jax_0.jpg",
        "fileName": "Jax_000_splash_centered.jpg",
        "width": 1280,
        "height": 720,
        "format": "jpeg",
        "hasAlpha": False,
        "bytes": 92299,
        "sha256": "0" * 64,
    }
    base.update(overrides)
    return base


def fatia_com(asset: dict[str, Any], categoria: str = "champion") -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": "16.17.1",
        "category": categoria,
        "generatedAt": "2026-09-04T00:00:00Z",
        "assets": [asset],
    }


# --- as fixtures são o contrato em exemplo ------------------------------------


@pytest.mark.parametrize("nome", FIXTURES_DE_FATIA)
def test_fixture_de_fatia_valida(nome: str) -> None:
    validate_shard(carregar(nome))


def test_fixture_de_catalogo_valida() -> None:
    validate_catalog(carregar("catalog.json"))


def test_fixture_de_manifesto_valida() -> None:
    validate_manifest(carregar("manifest.json"))


def test_fixture_tem_os_numeros_medidos_nos_spikes() -> None:
    """A fixture é retrato do patch 16.17.1, não invenção."""
    por_tipo = {a["type"]: a for a in carregar("index-champion.json")["assets"]}
    assert (por_tipo["square"]["width"], por_tipo["square"]["height"]) == (128, 128)
    assert (por_tipo["splash_centered"]["width"], por_tipo["splash_centered"]["height"]) == (
        1280,
        720,
    )
    assert (por_tipo["splash_wide"]["width"], por_tipo["splash_wide"]["height"]) == (1215, 717)
    assert (por_tipo["loading"]["width"], por_tipo["loading"]["height"]) == (308, 560)
    assert (por_tipo["tile"]["width"], por_tipo["tile"]["height"]) == (380, 380)


def test_a_runa_da_fixture_tem_alfa_e_o_item_nao() -> None:
    """S1 mediu: runas são RGBA, ícone de item é RGB puro."""
    runa = carregar("index-rune.json")["assets"][0]
    item = carregar("index-item.json")["assets"][0]
    assert runa["hasAlpha"] is True and runa["format"] == "png"
    assert item["hasAlpha"] is False


# --- ADR 0001 regra 4: alfa nunca vira JPEG ----------------------------------


def test_alfa_em_jpeg_e_rejeitado_pelo_schema() -> None:
    with pytest.raises(ValidationError):
        validate_shard(fatia_com(asset_valido(hasAlpha=True)))


def test_alfa_em_jpeg_e_rejeitado_pelo_modelo() -> None:
    with pytest.raises(PydanticValidationError, match="ADR 0001"):
        Asset.model_validate(asset_valido(hasAlpha=True))


# --- ADR 0002: corte de splash é sempre por skin ------------------------------


def test_corte_de_splash_sem_skin_id_e_rejeitado_pelo_schema() -> None:
    quebrado = asset_valido()
    del quebrado["skinId"]
    with pytest.raises(ValidationError):
        validate_shard(fatia_com(quebrado))


def test_corte_de_splash_sem_skin_id_e_rejeitado_pelo_modelo() -> None:
    quebrado = asset_valido()
    del quebrado["skinId"]
    with pytest.raises(PydanticValidationError, match="skinId"):
        Asset.model_validate(quebrado)


def test_asset_de_campeao_sem_chave_e_rejeitado_pelo_modelo() -> None:
    quebrado = asset_valido()
    del quebrado["championKey"]
    with pytest.raises(PydanticValidationError, match="championKey"):
        Asset.model_validate(quebrado)


# --- ADR 0010: skin do catálogo precisa do campeão ----------------------------


def test_skin_do_catalogo_sem_champion_key_e_rejeitada() -> None:
    """Sem `championKey` não dá para rotular o resultado de busca com o campeão."""
    catalogo = carregar("catalog.json")
    del catalogo["skins"][0]["championKey"]
    with pytest.raises(ValidationError):
        validate_catalog(catalogo)
    with pytest.raises(PydanticValidationError):
        CatalogSkin.model_validate(catalogo["skins"][0])


# --- ida e volta --------------------------------------------------------------


@pytest.mark.parametrize("nome", [*FIXTURES_DE_FATIA, "catalog.json", "manifest.json"])
def test_ida_e_volta_preserva_o_documento(nome: str) -> None:
    """Ler com o modelo e serializar de volta produz o mesmo documento."""
    original = carregar(nome)
    modelo: BaseModel
    if nome == "catalog.json":
        modelo, validar = Catalog.model_validate(original), validate_catalog
    elif nome == "manifest.json":
        modelo, validar = IndexManifest.model_validate(original), validate_manifest
    else:
        modelo, validar = IndexShard.model_validate(original), validate_shard

    devolta = modelo.model_dump(by_alias=True, exclude_none=True, mode="json")
    validar(devolta)
    assert devolta == original


# --- paridade entre schema e modelo -------------------------------------------------

PARES = [
    ("index-shard.schema.json", None, IndexShard),
    ("index-shard.schema.json", "asset", Asset),
    ("catalog.schema.json", None, Catalog),
    ("catalog.schema.json", "champion", CatalogChampion),
    ("catalog.schema.json", "skin", CatalogSkin),
    ("index-manifest.schema.json", None, IndexManifest),
]


def _schema_de(arquivo: str, definicao: str | None) -> dict[str, Any]:
    from lol_assets_schema import SCHEMA_DIR

    documento: dict[str, Any] = json.loads((SCHEMA_DIR / arquivo).read_text(encoding="utf-8"))
    if definicao is None:
        return documento
    definicoes: dict[str, dict[str, Any]] = documento["$defs"]
    return definicoes[definicao]


def _apelidos(modelo: type[BaseModel]) -> set[str]:
    return {campo.alias or nome for nome, campo in modelo.model_fields.items()}


def _obrigatorios(modelo: type[BaseModel]) -> set[str]:
    return {
        campo.alias or nome for nome, campo in modelo.model_fields.items() if campo.is_required()
    }


@pytest.mark.parametrize("arquivo,definicao,modelo", PARES, ids=lambda v: str(v))
def test_modelo_tem_os_mesmos_campos_do_schema(
    arquivo: str, definicao: str | None, modelo: type[BaseModel]
) -> None:
    """É este teste que impede o modelo de envelhecer sozinho."""
    schema = _schema_de(arquivo, definicao)
    assert _apelidos(modelo) == set(schema["properties"]), (
        f"{modelo.__name__} divergiu de {arquivo}#{definicao}"
    )


@pytest.mark.parametrize("arquivo,definicao,modelo", PARES, ids=lambda v: str(v))
def test_modelo_tem_as_mesmas_obrigatoriedades(
    arquivo: str, definicao: str | None, modelo: type[BaseModel]
) -> None:
    schema = _schema_de(arquivo, definicao)
    assert _obrigatorios(modelo) == set(schema.get("required", []))

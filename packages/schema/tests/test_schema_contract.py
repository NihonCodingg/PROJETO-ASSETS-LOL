"""O contrato precisa ser válido antes de qualquer código depender dele."""

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from lol_assets_schema import (
    ALIASES_FILE,
    CATALOG_SCHEMA,
    MANIFEST_SCHEMA,
    SCHEMA_VERSION,
    SHARD_SCHEMA,
)

SCHEMAS = [MANIFEST_SCHEMA, CATALOG_SCHEMA, SHARD_SCHEMA]


def test_schema_version_is_exposed() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", SCHEMA_VERSION)


@pytest.mark.parametrize("caminho", SCHEMAS, ids=lambda p: p.name)
def test_json_schema_e_valido(caminho: Path) -> None:
    documento = json.loads(caminho.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(documento)


def test_apelidos_estao_bem_formados() -> None:
    documento = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    apelidos = documento["aliases"]
    assert apelidos, "a tabela não pode estar vazia"
    for apelido, champion_id in apelidos.items():
        # a chave é o que a pessoa digita, já normalizado
        assert re.fullmatch(r"[a-z0-9]+", apelido), apelido
        # o valor é o id interno do ddragon
        assert re.fullmatch(r"[A-Za-z]+", champion_id), (apelido, champion_id)


def test_shard_valida_um_asset_de_exemplo() -> None:
    validador = Draft202012Validator(json.loads(SHARD_SCHEMA.read_text(encoding="utf-8")))
    fatia = {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": "16.17.1",
        "category": "champion",
        "generatedAt": "2026-09-03T12:00:00Z",
        "assetsBaseUrl": "https://assets.example/lol",
        "assets": [
            {
                "id": "splash_centered:24000",
                "type": "splash_centered",
                "category": "champion",
                "championKey": 24,
                "championId": "Jax",
                "skinId": 24000,
                "skinNum": 0,
                "isBaseSkin": True,
                "names": {"pt_BR": "Jax", "en_US": "Jax"},
                "source": "ddragon",
                "sourceUrl": "https://ddragon.leagueoflegends.com/cdn/img/champion/centered/Jax_0.jpg",
                "storageKey": "16.17.1/champion/Jax_000_splash_centered.jpg",
                "fileName": "Jax_000_splash_centered.jpg",
                "width": 1280,
                "height": 720,
                "format": "jpeg",
                "hasAlpha": False,
                "bytes": 123478,
                "sha256": "0" * 64,
            }
        ],
    }
    validador.validate(fatia)


def test_shard_rejeita_alfa_em_jpeg() -> None:
    """ADR 0001 regra 4: o que tem canal alfa nunca pode ser JPEG."""
    validador = Draft202012Validator(json.loads(SHARD_SCHEMA.read_text(encoding="utf-8")))
    fatia = {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": "16.17.1",
        "category": "rune",
        "generatedAt": "2026-09-03T12:00:00Z",
        "assets": [
            {
                "id": "rune_icon:8005",
                "type": "rune_icon",
                "category": "rune",
                "refId": "8005",
                "names": {"pt_BR": "Ataque Certeiro"},
                "source": "ddragon",
                "sourceUrl": "https://ddragon.leagueoflegends.com/cdn/img/perk-images/x.png",
                "fileName": "Rune_8005.png",
                "width": 256,
                "height": 256,
                "format": "jpeg",
                "hasAlpha": True,
                "bytes": 101234,
                "sha256": "0" * 64,
            }
        ],
    }
    assert not validador.is_valid(fatia)


def test_catalog_valida_navegacao_e_busca() -> None:
    """ADR 0010: campeões para navegar, skins para buscar, no mesmo documento."""
    validador = Draft202012Validator(json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8")))
    catalogo = {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": "16.17.1",
        "generatedAt": "2026-09-03T12:00:00Z",
        "assetsBaseUrl": "https://assets.example/lol",
        "champions": [
            {
                "championKey": 24,
                "championId": "Jax",
                "names": {"pt_BR": "Jax", "en_US": "Jax"},
                "title": {"pt_BR": "o Grão-Mestre das Armas"},
                "tags": ["Fighter"],
                "skinCount": 18,
                "chromaCount": 31,
                "baseSkinId": 24000,
                "thumbnailKey": "16.17.1/champion/Jax_square.png",
            }
        ],
        "skins": [
            {
                "skinId": 24000,
                "skinNum": 0,
                "championKey": 24,
                "names": {"pt_BR": "Jax"},
                "isBase": True,
            },
            {
                "skinId": 24004,
                "skinNum": 4,
                "championKey": 24,
                "names": {"pt_BR": "Jax Deus da Guerra"},
                "isBase": False,
                "chromaCount": 5,
                "thumbnailKey": "16.17.1/champion/Jax_004_tile.jpg",
            },
        ],
    }
    validador.validate(catalogo)


def test_catalog_rejeita_skin_sem_campeao() -> None:
    """Sem `championKey` não dá para rotular o resultado de busca com o campeão."""
    validador = Draft202012Validator(json.loads(CATALOG_SCHEMA.read_text(encoding="utf-8")))
    catalogo = {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": "16.17.1",
        "generatedAt": "2026-09-03T12:00:00Z",
        "champions": [],
        "skins": [{"skinId": 24004, "skinNum": 4, "names": {"pt_BR": "x"}, "isBase": False}],
    }
    assert not validador.is_valid(catalogo)


def test_manifesto_exige_catalogo_em_cada_versao() -> None:
    """ADR 0010: sem catálogo o front não tem como desenhar a home nem buscar."""
    validador = Draft202012Validator(json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8")))
    versao = {
        "gameVersion": "16.17.1",
        "indexedAt": "2026-09-03T12:00:00Z",
        "assetsCopied": True,
        "shards": [
            {"category": "champion", "url": "index-champion-abc.json", "assets": 10, "bytes": 100}
        ],
    }
    manifesto = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": "2026-09-03T12:00:00Z",
        "currentVersion": "16.17.1",
        "versions": [versao],
    }
    assert not validador.is_valid(manifesto), "versão sem catálogo deveria falhar"

    versao["catalog"] = {
        "url": "catalog-abc123.json",
        "champions": 173,
        "skins": 2149,
        "bytes": 340000,
    }
    validador.validate(manifesto)

"""T-05 — o menor recorte possível do caminho fonte → registro de asset.

Um campeão, dois tipos. O que estes testes protegem não é o volume: é a inversão
de nomes do ADR 0002 e a promessa do ADR 0001 de que o indexador nunca re-encoda.
Nenhum toca a rede.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from lol_assets_indexer import adapters
from lol_assets_indexer.adapters.ddragon import (
    SOURCE_FOLDER_TO_TYPE,
    build_champion_assets,
    latest_version,
)
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_schema.validators import validate_shard
from PIL import Image

DDRAGON = "https://ddragon.leagueoflegends.com"
VERSAO = "16.17.1"


def png(largura: int, altura: int, *, alfa: bool = False) -> bytes:
    imagem = Image.new(
        "RGBA" if alfa else "RGB", (largura, altura), (10, 20, 30, 0 if alfa else 255)
    )
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg(largura: int, altura: int) -> bytes:
    imagem = Image.new("RGB", (largura, altura), (60, 70, 80))
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG")
    return buffer.getvalue()


def ficha_do_campeao(nome: str) -> dict[str, Any]:
    return {
        "data": {
            "Jax": {
                "id": "Jax",
                "key": "24",
                "name": nome,
                "title": "o Grão-Mestre das Armas",
                "tags": ["Fighter", "Assassin"],
                "skins": [
                    {"id": "24000", "num": 0, "name": "default", "chromas": False},
                    {"id": "24001", "num": 1, "name": "O Super Jax", "chromas": False},
                ],
            }
        }
    }


SQUARE = png(128, 128)
CENTERED = jpeg(1280, 720)
WIDE = jpeg(1215, 717)


def montar_rotas() -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(
        return_value=httpx.Response(200, json=[VERSAO, "16.16.1"])
    )
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/data/pt_BR/champion/Jax.json").mock(
        return_value=httpx.Response(200, json=ficha_do_campeao("Jax"))
    )
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/data/en_US/champion/Jax.json").mock(
        return_value=httpx.Response(200, json=ficha_do_campeao("Jax"))
    )
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/img/champion/Jax.png").mock(
        return_value=httpx.Response(200, content=SQUARE)
    )
    respx.get(f"{DDRAGON}/cdn/img/champion/centered/Jax_0.jpg").mock(
        return_value=httpx.Response(200, content=CENTERED)
    )
    # A pasta `splash/` existe e serve o corte ABERTO. Se o adaptador confundir
    # os dois, este conteúdo é o que vai aparecer no lugar errado.
    respx.get(f"{DDRAGON}/cdn/img/champion/splash/Jax_0.jpg").mock(
        return_value=httpx.Response(200, content=WIDE)
    )


def cliente() -> SourceClient:
    return SourceClient(IndexerSettings(indexer_max_retries=1))


@respx.mock
async def test_descobre_a_versao_mais_recente() -> None:
    montar_rotas()
    async with cliente() as http:
        assert await latest_version(http) == VERSAO


@respx.mock
async def test_produz_exatamente_dois_registros_validos() -> None:
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    assert len(assets) == 2
    validate_shard(
        {
            "schemaVersion": "1.1.0",
            "gameVersion": VERSAO,
            "category": "champion",
            "generatedAt": "2026-09-04T00:00:00Z",
            "assets": [a.model_dump(by_alias=True, exclude_none=True, mode="json") for a in assets],
        }
    )


@respx.mock
async def test_splash_centered_vem_de_centered_e_nao_de_splash() -> None:
    """ADR 0002: o `centered` do ddragon é o splash_centered, 1280x720."""
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    centered = next(a for a in assets if a.type == "splash_centered")
    assert "/img/champion/centered/" in centered.source_url
    assert "/img/champion/splash/" not in centered.source_url
    assert (centered.width, centered.height) == (1280, 720)


def test_o_mapa_de_pastas_nao_troca_os_cortes() -> None:
    """A trava do ADR 0002 em uma linha: se alguém inverter, este teste morre."""
    assert SOURCE_FOLDER_TO_TYPE["centered"] == "splash_centered"
    assert SOURCE_FOLDER_TO_TYPE["splash"] == "splash_wide"


@respx.mock
async def test_square_e_png_sem_alfa_e_do_tamanho_medido() -> None:
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    square = next(a for a in assets if a.type == "square")
    assert (square.width, square.height) == (128, 128)
    assert square.format == "png"
    assert square.has_alpha is False


@respx.mock
async def test_sha256_e_bytes_batem_com_o_arquivo_baixado() -> None:
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    esperado = {"square": SQUARE, "splash_centered": CENTERED}
    for asset in assets:
        dados = esperado[asset.type]
        assert asset.sha256 == hashlib.sha256(dados).hexdigest()
        assert asset.bytes == len(dados)


@respx.mock
async def test_nomes_de_arquivo_seguem_a_convencao() -> None:
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    nomes = {a.type: a.file_name for a in assets}
    assert nomes["square"] == "Jax_square.png"
    assert nomes["splash_centered"] == "Jax_000_splash_centered.jpg"


@respx.mock
async def test_identidade_e_chaves_de_fusao() -> None:
    montar_rotas()
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    por_tipo = {a.type: a for a in assets}
    assert por_tipo["square"].id == "square:24"
    assert por_tipo["splash_centered"].id == "splash_centered:24000"
    assert all(a.champion_key == 24 and a.champion_id == "Jax" for a in assets)
    assert por_tipo["splash_centered"].skin_id == 24000
    assert por_tipo["splash_centered"].skin_num == 0


@respx.mock
async def test_nomes_vem_dos_dois_idiomas() -> None:
    montar_rotas()
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/data/en_US/champion/Jax.json").mock(
        return_value=httpx.Response(200, json=ficha_do_campeao("Jax (en)"))
    )
    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax")

    assert assets[0].names.pt_BR == "Jax"
    assert assets[0].names.en_US == "Jax (en)"


@respx.mock
async def test_versao_fixada_nao_consulta_a_lista_de_versoes() -> None:
    montar_rotas()
    rota_versoes = respx.get(f"{DDRAGON}/api/versions.json")

    async with cliente() as http:
        assets = await build_champion_assets(http, "Jax", version=VERSAO)

    assert not rota_versoes.called, "com a versão fixada, versions.json é dispensável"
    assert all(a.storage_key is not None for a in assets)
    assert all(a.storage_key.startswith(f"{VERSAO}/champion/") for a in assets if a.storage_key)


# --- a garantia do ADR 0001 --------------------------------------------------


def test_o_adaptador_nunca_reencoda_imagem() -> None:
    """ADR 0001: o indexador copia bytes. Pillow só mede.

    Varredura de fonte, não de comportamento: é o tipo de regra que se perde num
    refactor bem-intencionado, e o teste é o que a segura.
    """
    modulos = list(Path(adapters.__file__).parent.glob("*.py"))
    assert modulos, "nenhum adaptador encontrado"
    for modulo in modulos:
        codigo = modulo.read_text(encoding="utf-8")
        assert not re.search(r"\.save\s*\(", codigo), f"{modulo.name} parece re-encodar imagem"
        assert "Image.new" not in codigo, f"{modulo.name} parece criar imagem"


def test_a_medicao_le_mas_nao_escreve() -> None:
    from lol_assets_indexer import imaging

    codigo = Path(imaging.__file__).read_text(encoding="utf-8")
    assert not re.search(r"\.save\s*\(", codigo)


# --- erro ---------------------------------------------------------------------


@respx.mock
async def test_campeao_inexistente_falha_alto() -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(200, json=[VERSAO]))
    respx.get(re.compile(rf"{re.escape(DDRAGON)}/cdn/.*/champion/NaoExiste\.json")).mock(
        return_value=httpx.Response(404)
    )
    async with cliente() as http:
        with pytest.raises(httpx.HTTPStatusError):
            await build_champion_assets(http, "NaoExiste")


def test_a_ficha_de_campeao_e_lida_do_json_e_nao_adivinhada() -> None:
    """`key` é string no ddragon e precisa virar int — KICKOFF §B.1.5."""
    ficha = json.loads(json.dumps(ficha_do_campeao("Jax")))
    assert ficha["data"]["Jax"]["key"] == "24"

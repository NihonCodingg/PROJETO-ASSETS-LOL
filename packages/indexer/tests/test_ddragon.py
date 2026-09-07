"""O que o indexador ainda pede ao ddragon fora do tarball, e as duas travas.

Depois do T-09 a ingestão inteira passa pelo tarball (`test_tarball.py`). Sobrou
para cá o que vem de fora dele — a descoberta de versão e a URL do tarball — mais
as duas regras que não podem se perder num refactor: a inversão de nomes do
ADR 0002 e a promessa do ADR 0001 de que o indexador nunca re-encoda.

Nenhum teste aqui toca a rede.
"""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest
import respx
from lol_assets_indexer import adapters
from lol_assets_indexer.adapters.ddragon import (
    SOURCE_FOLDER_TO_TYPE,
    latest_version,
    tarball_url,
)
from lol_assets_indexer.http import IndexerSettings, SourceClient

DDRAGON = "https://ddragon.leagueoflegends.com"
VERSAO = "16.17.1"


def cliente() -> SourceClient:
    return SourceClient(IndexerSettings(indexer_max_retries=1))


# --- descoberta de versão ------------------------------------------------------


@respx.mock
async def test_descobre_a_versao_mais_recente() -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(
        return_value=httpx.Response(200, json=[VERSAO, "16.16.1"])
    )
    async with cliente() as http:
        assert await latest_version(http) == VERSAO


@respx.mock
async def test_lista_de_versoes_vazia_falha_alto() -> None:
    """Seguir com uma versão inventada publicaria um índice apontando para o nada."""
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(200, json=[]))
    async with cliente() as http:
        with pytest.raises(ValueError, match="lista de versões"):
            await latest_version(http)


# --- o tarball -----------------------------------------------------------------


def test_url_do_tarball_e_versionada() -> None:
    assert tarball_url(DDRAGON, VERSAO) == f"{DDRAGON}/cdn/dragontail-{VERSAO}.tgz"


def test_url_do_tarball_tolera_barra_no_fim() -> None:
    assert tarball_url(f"{DDRAGON}/", VERSAO) == f"{DDRAGON}/cdn/dragontail-{VERSAO}.tgz"


# --- a trava do ADR 0002 --------------------------------------------------------


def test_o_mapa_de_pastas_nao_troca_os_cortes() -> None:
    """A trava do ADR 0002 em quatro linhas: se alguém inverter, este teste morre."""
    assert SOURCE_FOLDER_TO_TYPE["centered"] == "splash_centered"
    assert SOURCE_FOLDER_TO_TYPE["splash"] == "splash_wide"
    assert SOURCE_FOLDER_TO_TYPE["loading"] == "loading"
    assert SOURCE_FOLDER_TO_TYPE["tiles"] == "tile"


def test_o_mapa_de_pastas_existe_uma_vez_so() -> None:
    """Duas cópias do mapa seriam duas chances de inverter. ADR 0002."""
    definicoes = [
        modulo.name
        for modulo in Path(adapters.__file__).parent.glob("*.py")
        if "FOLDER_TO_TYPE: dict[str, AssetType] = {" in modulo.read_text(encoding="utf-8")
    ]
    assert definicoes == ["ddragon.py"], definicoes


# --- a garantia do ADR 0001 -----------------------------------------------------


def test_o_adaptador_nunca_reencoda_imagem() -> None:
    """ADR 0001: o indexador mede bytes. Pillow só lê.

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


# --- a garantia do ADR 0012 -----------------------------------------------------


def test_nenhum_adaptador_monta_storage_key() -> None:
    """ADR 0012: nada é copiado, então nenhum registro pode nascer com `storageKey`."""
    for modulo in Path(adapters.__file__).parent.glob("*.py"):
        codigo = modulo.read_text(encoding="utf-8")
        assert "storage_key(" not in codigo, f"{modulo.name} monta storageKey"

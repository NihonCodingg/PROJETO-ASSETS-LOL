"""T-18 — testes de contrato das fontes. **Tocam a rede de verdade.**

Descobrir que uma fonte mudou **antes** que o catálogo quebre em silêncio. É a
única suíte do projeto que sai da máquina, e por isso ela:

- roda agendada, num workflow próprio, **não em PR** — falha aqui é alerta, não
  bloqueio, porque uma queda do ddragon não pode travar merge;
- está toda marcada `network`, e a suíte padrão a exclui por configuração.

Os números conferidos são os do S1 e do S2. Se um deles mudar, o teste diz
**qual e onde** — é essa mensagem que economiza a hora de investigação.

Rodar de propósito:

    uv run pytest -m network
"""

from __future__ import annotations

import json

import httpx
import pytest
from lol_assets_indexer.adapters.cdragon import asset_url, champion_json_url, declared_assets
from lol_assets_indexer.adapters.ddragon import latest_version
from lol_assets_indexer.http import IndexerSettings, SourceClient, user_agent
from lol_assets_indexer.imaging import measure
from lol_assets_schema import ALIASES_FILE

pytestmark = pytest.mark.network

#: Os três do S2, e os mesmos do §12 da Spec.
CAMPEOES = {"Jax": 24, "Lux": 99, "Nunu": 20}

#: Dimensões medidas no S1 e no S2. Mudou aqui, mudou na fonte.
DIMENSOES = {
    "splash_centered": (1280, 720),
    "splash_wide": (1215, 717),
    "loading": (308, 560),
    "tile": (380, 380),
    "square": (128, 128),
    "passive_icon": (64, 64),
    "ability_icon": (64, 64),
    "chroma": (270, 303),
    "loading_vintage": (308, 560),
}


def settings() -> IndexerSettings:
    return IndexerSettings()


@pytest.fixture(scope="module")
def config() -> IndexerSettings:
    return settings()


# --- CORS: a base técnica do ADR 0001 --------------------------------------------------


@pytest.mark.parametrize("champion_id", sorted(CAMPEOES))
async def test_ddragon_ainda_manda_cors_aberto(config: IndexerSettings, champion_id: str) -> None:
    """Sem `Access-Control-Allow-Origin: *`, o PNG no cliente para de funcionar.

    O ADR 0001 inteiro depende de o navegador conseguir ler os bytes da fonte
    para desenhar no canvas. Sem CORS, o canvas fica *tainted* e `toBlob` falha.
    """
    url = f"{config.ddragon_base_url}/cdn/img/champion/centered/{champion_id}_0.jpg"
    async with httpx.AsyncClient(headers={"User-Agent": user_agent(config)}) as client:
        resposta = await client.head(url, follow_redirects=True)

    assert resposta.status_code == 200, url
    assert resposta.headers.get("access-control-allow-origin") == "*", (
        f"{url} parou de mandar CORS aberto — o ADR 0001 depende disso"
    )


async def test_cdragon_ainda_manda_cors_aberto(config: IndexerSettings) -> None:
    url = champion_json_url(config.cdragon_base_url, 24)
    async with httpx.AsyncClient(headers={"User-Agent": user_agent(config)}) as client:
        resposta = await client.get(url, follow_redirects=True)

    assert resposta.status_code == 200
    assert resposta.headers.get("access-control-allow-origin") == "*", (
        f"{url} parou de mandar CORS aberto"
    )


# --- as dimensões do ddragon ------------------------------------------------------------


@pytest.mark.parametrize("champion_id", sorted(CAMPEOES))
async def test_as_dimensoes_do_ddragon_nao_mudaram(
    config: IndexerSettings, champion_id: str
) -> None:
    """ADR 0002: `centered` é 1280x720 e `splash` é 1215x717. Nunca o contrário."""
    async with SourceClient(config) as client:
        versao = await latest_version(client)
        arte = f"{config.ddragon_base_url}/cdn/img/champion"
        alvos = {
            "splash_centered": f"{arte}/centered/{champion_id}_0.jpg",
            "splash_wide": f"{arte}/splash/{champion_id}_0.jpg",
            "loading": f"{arte}/loading/{champion_id}_0.jpg",
            "tile": f"{arte}/tiles/{champion_id}_0.jpg",
            "square": f"{config.ddragon_base_url}/cdn/{versao}/img/champion/{champion_id}.png",
        }
        for tipo, url in alvos.items():
            medida = measure(await client.get_bytes(url))
            esperado = DIMENSOES[tipo]
            assert (medida.width, medida.height) == esperado, (
                f"{tipo} de {champion_id} virou {medida.width}x{medida.height}, "
                f"esperado {esperado[0]}x{esperado[1]} — {url}"
            )


async def test_o_corte_centrado_continua_maior_que_o_aberto(config: IndexerSettings) -> None:
    """A inversão do ADR 0002 em uma asserção: se trocarem, isto pega."""
    base = f"{config.ddragon_base_url}/cdn/img/champion"
    async with SourceClient(config) as client:
        centrado = measure(await client.get_bytes(f"{base}/centered/Jax_0.jpg"))
        aberto = measure(await client.get_bytes(f"{base}/splash/Jax_0.jpg"))

    assert centrado.width > aberto.width
    assert centrado.height > aberto.height


# --- o cdragon ----------------------------------------------------------------------------


async def test_o_cdragon_continua_declarando_os_caminhos(config: IndexerSettings) -> None:
    """A regra do T-16: o JSON declara, a gente lê. Se ele parar de declarar, isto pega."""
    async with SourceClient(config) as client:
        documento = await client.get_json(champion_json_url(config.cdragon_base_url, 24))

    paths = declared_assets(documento)
    tipos = {declarado.type for declarado in paths.assets}
    assert {"square", "splash_centered", "splash_wide", "tile", "loading"} <= tipos
    assert "chroma" in tipos, "o Jax tem chroma; se sumiu, o formato mudou"


@pytest.mark.parametrize("tipo", ["chroma", "loading_vintage"])
async def test_a_cobertura_exclusiva_do_cdragon_continua_de_pe(
    config: IndexerSettings, tipo: str
) -> None:
    """É por isto que a segunda fonte existe. Sem ela, não há chroma nem vintage."""
    async with SourceClient(config) as client:
        documento = await client.get_json(champion_json_url(config.cdragon_base_url, 24))
        declarado = next(d for d in declared_assets(documento).assets if d.type == tipo)
        url = asset_url(config.cdragon_base_url, declarado.declared)
        assert url is not None
        medida = measure(await client.get_bytes(url))

    esperado = DIMENSOES[tipo]
    assert (medida.width, medida.height) == esperado, (
        f"{tipo} virou {medida.width}x{medida.height}, esperado {esperado[0]}x{esperado[1]} — {url}"
    )


# --- a tabela de apelidos (ADR 0009) --------------------------------------------------------


async def test_todo_apelido_aponta_para_um_campeao_que_existe(config: IndexerSettings) -> None:
    """Id de campeão muda de grafia entre patches — `Fiddlesticks` contra `FiddleSticks`.

    Um apelido apontando para um id morto é busca que não acha, em silêncio.
    """
    apelidos = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))["aliases"]

    async with SourceClient(config) as client:
        versao = await latest_version(client)
        documento = await client.get_json(
            f"{config.ddragon_base_url}/cdn/{versao}/data/pt_BR/champion.json"
        )

    existentes = set(documento["data"])
    mortos = {
        apelido: champion_id
        for apelido, champion_id in apelidos.items()
        if champion_id not in existentes
    }
    assert not mortos, f"apelidos apontando para campeão que não existe no patch {versao}: {mortos}"


async def test_a_contagem_de_campeoes_nao_despencou(config: IndexerSettings) -> None:
    """173 no patch 16.17.1. Cair muito abaixo disso é sintoma, não novidade."""
    async with SourceClient(config) as client:
        versao = await latest_version(client)
        documento = await client.get_json(
            f"{config.ddragon_base_url}/cdn/{versao}/data/pt_BR/champion.json"
        )

    quantos = len(documento["data"])
    assert quantos >= 173, f"o patch {versao} traz {quantos} campeões; o S1 mediu 173"

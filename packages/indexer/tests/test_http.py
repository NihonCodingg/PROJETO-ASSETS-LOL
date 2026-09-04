"""T-03 — o cliente HTTP é o único lugar por onde toda fonte externa passa.

A regra 4 do CLAUDE.md (User-Agent identificado, concorrência ≤ 4, backoff em
429/5xx) e a regra 3 (nada de wiki sem consentimento) são impostas aqui, por
código. Estes testes é que provam isso. Nenhum toca a rede.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable

import httpx
import pytest
import respx
from lol_assets_indexer.http import (
    REPO_URL,
    IndexerSettings,
    SourceClient,
    WikiAccessBlockedError,
    user_agent,
)

URL = "https://ddragon.leagueoflegends.com/api/versions.json"


def settings(**overrides: object) -> IndexerSettings:
    """Configuração explícita: nenhum teste depende do `.env` da máquina."""
    base: dict[str, object] = {
        "indexer_contact": f"{REPO_URL}/issues",
        "indexer_max_concurrency": 4,
        "indexer_timeout_seconds": 5.0,
        "indexer_max_retries": 5,
        "wiki_consent_granted": False,
    }
    base.update(overrides)
    return IndexerSettings(**base)  # type: ignore[arg-type]


class RelogioFalso:
    """Registra as esperas em vez de dormir, para o teste ser instantâneo."""

    def __init__(self) -> None:
        self.esperas: list[float] = []

    async def __call__(self, segundos: float) -> None:
        self.esperas.append(segundos)


def cliente(
    *,
    config: IndexerSettings | None = None,
    sleep: Callable[[float], Awaitable[None]] | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> SourceClient:
    return SourceClient(
        config or settings(),
        sleep=sleep or RelogioFalso(),
        jitter=lambda: 0.0,
        transport=transport,
    )


# --- backoff -----------------------------------------------------------------


@respx.mock
async def test_repete_em_429_e_termina_em_200() -> None:
    rota = respx.get(URL).mock(
        side_effect=[httpx.Response(429), httpx.Response(200, json={"ok": True})]
    )
    relogio = RelogioFalso()
    async with cliente(sleep=relogio) as http:
        resposta = await http.request("GET", URL)

    assert resposta.status_code == 200
    assert rota.call_count == 2
    assert len(relogio.esperas) == 1


@respx.mock
async def test_desiste_depois_do_limite_e_a_espera_cresce() -> None:
    rota = respx.get(URL).mock(return_value=httpx.Response(500))
    relogio = RelogioFalso()
    async with cliente(config=settings(indexer_max_retries=4), sleep=relogio) as http:
        with pytest.raises(httpx.HTTPStatusError):
            await http.request("GET", URL)

    assert rota.call_count == 4, "4 tentativas no total"
    assert len(relogio.esperas) == 3, "3 esperas entre as 4 tentativas"
    assert relogio.esperas == sorted(relogio.esperas), "o backoff nunca encolhe"
    assert relogio.esperas[-1] > relogio.esperas[0], "e cresce de verdade"


@respx.mock
async def test_respeita_retry_after() -> None:
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json={}),
        ]
    )
    relogio = RelogioFalso()
    async with cliente(sleep=relogio) as http:
        await http.request("GET", URL)

    assert relogio.esperas == [pytest.approx(2.0)]


@respx.mock
async def test_erro_de_transporte_tambem_e_repetido() -> None:
    rota = respx.get(URL).mock(
        side_effect=[httpx.ConnectError("caiu"), httpx.Response(200, json={})]
    )
    async with cliente() as http:
        resposta = await http.request("GET", URL)

    assert resposta.status_code == 200
    assert rota.call_count == 2


@respx.mock
async def test_404_nao_e_repetido() -> None:
    """Só 429 e 5xx merecem repetição; 404 é resposta, não falha temporária."""
    rota = respx.get(URL).mock(return_value=httpx.Response(404))
    relogio = RelogioFalso()
    async with cliente(sleep=relogio) as http:
        resposta = await http.request("GET", URL)

    assert resposta.status_code == 404
    assert rota.call_count == 1
    assert relogio.esperas == []


# --- concorrência ------------------------------------------------------------


async def test_concorrencia_nunca_passa_do_limite() -> None:
    em_voo = 0
    pico = 0

    async def manipulador(request: httpx.Request) -> httpx.Response:
        nonlocal em_voo, pico
        em_voo += 1
        pico = max(pico, em_voo)
        await asyncio.sleep(0.01)
        em_voo -= 1
        return httpx.Response(200, json={})

    async with cliente(transport=httpx.MockTransport(manipulador)) as http:
        await asyncio.gather(
            *(
                http.request("GET", f"https://ddragon.leagueoflegends.com/{i}.json")
                for i in range(12)
            )
        )

    assert pico <= 4, f"pico de {pico} requisições simultâneas passou do limite de 4"


async def test_o_limite_de_concorrencia_e_por_host() -> None:
    """Dois hosts diferentes não competem pelo mesmo semáforo."""
    por_host: dict[str, int] = {}
    pico_por_host: dict[str, int] = {}

    async def manipulador(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        por_host[host] = por_host.get(host, 0) + 1
        pico_por_host[host] = max(pico_por_host.get(host, 0), por_host[host])
        await asyncio.sleep(0.01)
        por_host[host] -= 1
        return httpx.Response(200, json={})

    hosts = ["ddragon.leagueoflegends.com", "raw.communitydragon.org"]
    async with cliente(transport=httpx.MockTransport(manipulador)) as http:
        await asyncio.gather(
            *(http.request("GET", f"https://{host}/{i}.json") for host in hosts for i in range(8))
        )

    assert set(pico_por_host) == set(hosts)
    assert all(pico <= 4 for pico in pico_por_host.values())


# --- regra 3: a wiki ---------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://wiki.leagueoflegends.com/en-us/api.php",
        "https://WIKI.leagueoflegends.com/en-us/",
        "https://leagueoflegends.fandom.com/wiki/Jax",
    ],
)
async def test_wiki_bloqueada_sem_consentimento(url: str) -> None:
    async with cliente() as http:
        with pytest.raises(WikiAccessBlockedError, match="regra 3"):
            await http.request("GET", url)


async def test_wiki_liberada_com_consentimento_documentado() -> None:
    """A trava é uma flag, não uma proibição eterna — ADR 0004."""

    async def manipulador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    async with cliente(
        config=settings(wiki_consent_granted=True),
        transport=httpx.MockTransport(manipulador),
    ) as http:
        resposta = await http.request("GET", "https://wiki.leagueoflegends.com/en-us/api.php")

    assert resposta.status_code == 200


# --- regra 4: a etiqueta -----------------------------------------------------


def test_user_agent_segue_o_formato_da_regra_4() -> None:
    agente = user_agent(settings())
    assert re.fullmatch(
        r"lol-assets-indexer/\d+\.\d+\.\d+ \(\+https://github\.com/\S+; .+\)", agente
    ), agente


def test_contato_padrao_nao_e_dado_pessoal() -> None:
    """O padrão é a URL de issues do repositório, nunca e-mail de ninguém.

    Lê o default declarado no campo em vez de instanciar sem argumento: um `.env`
    local (copiado do `.env.example`, que traz "seu-email-ou-url-de-contato") não
    pode decidir se este teste passa.
    """
    padrao = IndexerSettings.model_fields["indexer_contact"].default
    assert padrao == f"{REPO_URL}/issues"

    agente = user_agent(settings(indexer_contact=padrao))
    assert agente.endswith(f"; {REPO_URL}/issues)")
    assert "@" not in agente


@respx.mock
async def test_toda_requisicao_leva_o_user_agent() -> None:
    rota = respx.get(URL).mock(return_value=httpx.Response(200, json={}))
    async with cliente() as http:
        await http.request("GET", URL)

    assert rota.calls[0].request.headers["User-Agent"] == user_agent(settings())


# --- configuração ------------------------------------------------------------


def test_configuracao_vem_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INDEXER_MAX_CONCURRENCY", "2")
    monkeypatch.setenv("INDEXER_CONTACT", "https://exemplo.invalido/contato")
    monkeypatch.setenv("WIKI_CONSENT_GRANTED", "true")
    config = IndexerSettings()

    assert config.indexer_max_concurrency == 2
    assert config.indexer_contact == "https://exemplo.invalido/contato"
    assert config.wiki_consent_granted is True


def test_concorrencia_acima_de_quatro_e_rejeitada() -> None:
    """A regra 4 diz ≤ 4. Configuração não pode furar a regra."""
    with pytest.raises(ValueError):
        IndexerSettings(indexer_max_concurrency=8)


# --- atalhos -----------------------------------------------------------------


@respx.mock
async def test_get_json_e_get_bytes() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, json={"a": 1}))
    respx.get("https://ddragon.leagueoflegends.com/x.png").mock(
        return_value=httpx.Response(200, content=b"\x89PNG")
    )
    async with cliente() as http:
        assert await http.get_json(URL) == {"a": 1}
        assert await http.get_bytes("https://ddragon.leagueoflegends.com/x.png") == b"\x89PNG"


@respx.mock
async def test_get_json_levanta_em_erro() -> None:
    respx.get(URL).mock(return_value=httpx.Response(404))
    async with cliente() as http:
        with pytest.raises(httpx.HTTPStatusError):
            await http.get_json(URL)

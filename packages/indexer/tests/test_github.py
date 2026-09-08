"""T-12 — a issue automática, que é o canal de alerta inteiro do projeto.

Duas coisas podem estragá-la, e as duas são silenciosas: abrir issue repetida a
cada reexecução, e vazar credencial no corpo. O resto é detalhe.

Nenhum teste toca a rede.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from lol_assets_indexer.github import (
    ISSUE_LABEL,
    REDACTED,
    IssueReporter,
    already_reported,
    build_issue,
    marker,
    redact,
    reporter_from_env,
)
from lol_assets_indexer.status import build_status
from lol_assets_schema.models import IndexStatus

API = "https://api.github.invalido"
REPO = "NihonCodingg/PROJETO-ASSETS-LOL"
SEGREDO = "ghp_UmTokenBemLongoQueNaoPodeVazar"


def status_de_falha(run_id: str | None = "42", mensagem: str = "ddragon fora do ar") -> IndexStatus:
    return build_status(
        started_at="2026-09-08T00:00:00Z",
        finished_at="2026-09-08T00:00:02Z",
        duration_seconds=2.0,
        game_version="16.17.1",
        run_id=run_id,
        failure=RuntimeError(mensagem),
    )


def reporter(client: httpx.Client) -> IssueReporter:
    return IssueReporter(REPO, SEGREDO, client=client, api_base=API)


# --- redação: o corpo carrega mensagem de exceção, que é onde credencial vaza ---------


def test_o_valor_da_variavel_sensivel_some_do_texto() -> None:
    texto = f"falhou autenticando com {SEGREDO} no endpoint"
    assert (
        redact(texto, {"GITHUB_TOKEN": SEGREDO})
        == f"falhou autenticando com {REDACTED} no endpoint"
    )


def test_valor_curto_nao_e_apagado() -> None:
    """`S3_REGION=auto` não pode transformar toda ocorrência de "auto" em [redigido]."""
    assert redact("modo auto ligado", {"S3_ACCESS_KEY_ID": "auto"}) == "modo auto ligado"


def test_todas_as_variaveis_sensiveis_sao_cobertas() -> None:
    ambiente = {
        "GITHUB_TOKEN": "token_do_github_bem_longo",
        "S3_ACCESS_KEY_ID": "chave_de_acesso_longa",
        "S3_SECRET_ACCESS_KEY": "segredo_de_acesso_longo",
        "S3_ENDPOINT_URL": "https://conta.r2.cloudflarestorage.com",
    }
    texto = " ".join(ambiente.values())
    assert redact(texto, ambiente) == " ".join([REDACTED] * len(ambiente))


def test_o_corpo_da_issue_sai_redigido(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", SEGREDO)
    payload = build_issue(status_de_falha(mensagem=f"401 usando {SEGREDO}"))

    assert SEGREDO not in payload.body
    assert REDACTED in payload.body


# --- o formato da issue ---------------------------------------------------------------


def test_o_titulo_nao_carrega_o_texto_do_erro() -> None:
    """Texto de erro muda a cada execução e faria issue parecida não ser achada."""
    a = build_issue(status_de_falha(mensagem="timeout depois de 30s"))
    b = build_issue(status_de_falha(mensagem="timeout depois de 45s"))

    assert a.title == b.title == "Indexação falhou em 16.17.1: RuntimeError"


def test_a_issue_leva_o_rotulo_e_o_carimbo() -> None:
    payload = build_issue(status_de_falha("99"), run_url="https://exemplo/actions/runs/99")

    assert payload.as_json()["labels"] == [ISSUE_LABEL]
    assert marker("99") in payload.body
    assert "https://exemplo/actions/runs/99" in payload.body


def test_o_corpo_traz_o_motivo_da_falha() -> None:
    assert "ddragon fora do ar" in build_issue(status_de_falha()).body


# --- idempotência ----------------------------------------------------------------------


def test_reconhece_issue_ja_aberta_para_a_mesma_execucao() -> None:
    abertas = [{"body": f"qualquer coisa\n{marker('42')}"}]
    assert already_reported(abertas, "42") is True
    assert already_reported(abertas, "43") is False


def test_issue_sem_corpo_nao_quebra_a_verificacao() -> None:
    assert already_reported([{"body": None}, {}], "42") is False


@respx.mock
def test_reexecucao_do_mesmo_run_id_nao_abre_segunda_issue() -> None:
    """O `schedule` roda a cada 6 h e o Actions reexecuta com um clique."""
    respx.get(f"{API}/repos/{REPO}/issues").mock(
        return_value=httpx.Response(200, json=[{"body": marker("42")}])
    )
    criacao = respx.post(f"{API}/repos/{REPO}/issues")

    with httpx.Client() as client:
        assert reporter(client).report(status_de_falha("42")) is None

    assert not criacao.called


@respx.mock
def test_execucao_nova_abre_a_issue() -> None:
    respx.get(f"{API}/repos/{REPO}/issues").mock(
        return_value=httpx.Response(200, json=[{"body": marker("41")}])
    )
    criacao = respx.post(f"{API}/repos/{REPO}/issues").mock(
        return_value=httpx.Response(201, json={"html_url": "https://exemplo/issues/7"})
    )

    with httpx.Client() as client:
        assert reporter(client).report(status_de_falha("42")) == "https://exemplo/issues/7"

    assert criacao.called
    enviado = criacao.calls[0].request
    assert b'"labels": ["indexacao"]' in enviado.content
    assert enviado.headers["Authorization"] == f"Bearer {SEGREDO}"


# --- falhar ao avisar não pode virar uma segunda falha ------------------------------------


@respx.mock
def test_api_fora_do_ar_nao_derruba_a_indexacao() -> None:
    """A falha da indexação já está no código de saída. Perder o aviso não pode dobrar."""
    respx.get(f"{API}/repos/{REPO}/issues").mock(return_value=httpx.Response(500))

    with httpx.Client() as client:
        assert reporter(client).report(status_de_falha()) is None


@respx.mock
def test_token_sem_permissao_nao_derruba_a_indexacao() -> None:
    respx.get(f"{API}/repos/{REPO}/issues").mock(return_value=httpx.Response(200, json=[]))
    respx.post(f"{API}/repos/{REPO}/issues").mock(return_value=httpx.Response(403))

    with httpx.Client() as client:
        assert reporter(client).report(status_de_falha()) is None


# --- fora do Actions, ninguém abre issue ---------------------------------------------------


def test_sem_token_nao_ha_reporter() -> None:
    assert reporter_from_env({"GITHUB_REPOSITORY": REPO}) is None


def test_sem_repositorio_nao_ha_reporter() -> None:
    assert reporter_from_env({"GITHUB_TOKEN": SEGREDO}) is None


def test_com_os_dois_ha_reporter() -> None:
    assert reporter_from_env({"GITHUB_REPOSITORY": REPO, "GITHUB_TOKEN": SEGREDO}) is not None

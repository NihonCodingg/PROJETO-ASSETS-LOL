"""Issue automática quando a indexação falha (T-12).

O canal de alerta do projeto é uma issue no próprio repositório: não há serviço
externo, não há e-mail configurado, e não vai haver (§11 da Spec).

Duas coisas importam mais que o resto aqui:

**Idempotência.** O Actions reexecuta job com um clique, e o `schedule` roda a
cada 6 h. Uma falha que persiste por um dia abriria quatro issues iguais. A chave
é o `GITHUB_RUN_ID`, carimbado num marcador HTML no corpo: se já existe issue
aberta com aquele marcador, não abre outra.

**Redação.** O corpo carrega a mensagem da exceção, e mensagem de exceção é
exatamente onde credencial vaza. Tudo que passa por aqui é filtrado contra os
valores das variáveis sensíveis do ambiente antes de sair.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from lol_assets_schema.models import IndexStatus

from lol_assets_indexer.http import IndexerSettings, user_agent
from lol_assets_indexer.status import render_summary

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
ISSUE_LABEL = "indexacao"

#: Nomes de variável cujo **valor** nunca pode aparecer em log nem em issue.
#: Não é lista de nomes proibidos: é lista de valores a apagar do texto.
SECRET_ENV_VARS = (
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_ENDPOINT_URL",
)

REDACTED = "[redigido]"

#: Comprimento abaixo do qual um valor de variável não é apagado do texto. Sem
#: isto, `S3_REGION=auto` transformaria toda ocorrência de "auto" em `[redigido]`.
_MIN_SECRET_LENGTH = 8


def redact(text: str, environ: dict[str, str] | None = None) -> str:
    """Apaga do texto o valor de qualquer variável sensível presente no ambiente."""
    ambiente = os.environ if environ is None else environ
    for nome in SECRET_ENV_VARS:
        valor = (ambiente.get(nome) or "").strip()
        if len(valor) >= _MIN_SECRET_LENGTH:
            text = text.replace(valor, REDACTED)
    return text


def marker(run_id: str) -> str:
    """O carimbo que torna a abertura idempotente. Invisível no Markdown."""
    return f"<!-- lol-assets-indexer:run:{run_id} -->"


@dataclass(frozen=True, slots=True)
class IssuePayload:
    title: str
    body: str

    def as_json(self) -> dict[str, Any]:
        return {"title": self.title, "body": self.body, "labels": [ISSUE_LABEL]}


def build_issue(status: IndexStatus, *, run_url: str | None = None) -> IssuePayload:
    """Título curto e estável; corpo com o resumo inteiro, já redigido.

    O título repete o tipo da exceção e a versão em vez do texto do erro: texto
    de erro muda a cada execução e faria a busca por issue parecida não achar nada.
    """
    versao = status.game_version or "versão não resolvida"
    tipo = status.failure.kind if status.failure else "falha"
    corpo = [render_summary(status)]
    if run_url:
        corpo.append(f"\n[Execução no Actions]({run_url})\n")
    if status.run_id:
        corpo.append(marker(status.run_id))
    return IssuePayload(
        title=f"Indexação falhou em {versao}: {tipo}",
        body=redact("\n".join(corpo)),
    )


def already_reported(issues: list[dict[str, Any]], run_id: str) -> bool:
    """`True` se alguma issue aberta já carrega o carimbo desta execução."""
    carimbo = marker(run_id)
    return any(carimbo in (issue.get("body") or "") for issue in issues)


class IssueReporter:
    """Fala com a API do GitHub. Falhar aqui **não** pode derrubar a indexação.

    A issue é o aviso de que algo deu errado; se o aviso falhar, o que importa
    continua sendo o código de saída do processo, que já é diferente de zero.
    """

    def __init__(
        self,
        repository: str,
        token: str,
        *,
        client: httpx.Client | None = None,
        api_base: str = GITHUB_API,
    ) -> None:
        self._repository = repository
        self._token = token
        self._api = api_base.rstrip("/")
        self._client = client or httpx.Client(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": user_agent(IndexerSettings()),
        }

    def open_issues(self) -> list[dict[str, Any]]:
        resposta = self._client.get(
            f"{self._api}/repos/{self._repository}/issues",
            params={"state": "open", "labels": ISSUE_LABEL, "per_page": 100},
            headers=self._headers(),
        )
        resposta.raise_for_status()
        documento = resposta.json()
        return documento if isinstance(documento, list) else []

    def create(self, payload: IssuePayload) -> str:
        resposta = self._client.post(
            f"{self._api}/repos/{self._repository}/issues",
            content=json.dumps(payload.as_json()).encode("utf-8"),
            headers={**self._headers(), "Content-Type": "application/json"},
        )
        resposta.raise_for_status()
        url = str(resposta.json().get("html_url", ""))
        return url

    def report(self, status: IndexStatus, *, run_url: str | None = None) -> str | None:
        """Abre a issue se ainda não houver uma para esta execução.

        Devolve a URL da issue criada, ou `None` se não criou — por já existir ou
        por a API ter recusado.
        """
        try:
            if status.run_id and already_reported(self.open_issues(), status.run_id):
                logger.info("issue já aberta para esta execução", extra={"runId": status.run_id})
                return None
            url = self.create(build_issue(status, run_url=run_url))
        except (httpx.HTTPError, ValueError) as erro:
            # De propósito engolido: a falha da indexação já está no código de
            # saída, e perder o aviso não pode virar uma segunda falha.
            logger.error(
                "não consegui abrir a issue de falha",
                extra={"kind": type(erro).__name__, "failure": redact(str(erro))},
            )
            return None
        logger.info("issue de falha aberta", extra={"url": url})
        return url


def reporter_from_env(environ: dict[str, str] | None = None) -> IssueReporter | None:
    """Monta o repórter a partir do ambiente do Actions, ou devolve `None`.

    Fora do Actions não há token nem repositório, e abrir issue à mão da máquina
    de alguém não é o comportamento desejado.
    """
    ambiente = dict(os.environ) if environ is None else environ
    repositorio = ambiente.get("GITHUB_REPOSITORY", "").strip()
    token = (ambiente.get("GITHUB_TOKEN") or ambiente.get("GH_TOKEN") or "").strip()
    if not repositorio or not token:
        return None
    return IssueReporter(repositorio, token)

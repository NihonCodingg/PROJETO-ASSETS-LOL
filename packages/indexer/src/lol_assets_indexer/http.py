"""Cliente HTTP — o único ponto por onde o indexador fala com fonte externa.

A etiqueta da regra 4 do CLAUDE.md (User-Agent identificado, concorrência ≤ 4 por
host, backoff exponencial em 429/5xx) e a trava da regra 3 (nada de wiki sem
consentimento documentado) vivem aqui, impostas por código e cobertas por teste.

Este módulo não sabe o que é ddragon nem cdragon. Ele só sabe pedir educadamente.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from lol_assets_indexer import __version__

REPO_URL = "https://github.com/NihonCodingg/PROJETO-ASSETS-LOL"

#: Regra 3 do CLAUDE.md. Só sai daqui com consentimento documentado — ver ADR 0004.
BLOCKED_HOSTS = frozenset({"wiki.leagueoflegends.com", "leagueoflegends.fandom.com"})

#: A regra 4 fala em ≤ 4 requisições simultâneas. Configuração não fura a regra.
MAX_CONCURRENCY_ALLOWED = 4

_BASE_DELAY_SECONDS = 1.0
_MAX_DELAY_SECONDS = 60.0


class WikiAccessBlockedError(RuntimeError):
    """Tentativa de acessar a wiki sem `WIKI_CONSENT_GRANTED`."""


class IndexerSettings(BaseSettings):
    """As variáveis documentadas em `.env.example`.

    Argumentos passados na construção têm precedência sobre o ambiente, que tem
    precedência sobre o `.env` — que é o que mantém os testes determinísticos.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    #: Contato público no User-Agent. O padrão é a URL de issues; nunca dado pessoal.
    indexer_contact: str = f"{REPO_URL}/issues"
    indexer_max_concurrency: int = Field(default=4, ge=1, le=MAX_CONCURRENCY_ALLOWED)
    indexer_timeout_seconds: float = Field(default=30.0, gt=0)
    indexer_max_retries: int = Field(default=5, ge=1)
    ddragon_base_url: str = "https://ddragon.leagueoflegends.com"
    cdragon_base_url: str = "https://raw.communitydragon.org"

    #: Bucket compatível com S3 (Cloudflare R2 — ADR 0005). Vazio = só `--dry-run`.
    s3_endpoint_url: str = ""
    s3_region: str = "auto"
    s3_bucket: str = "lol-assets"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    #: Base pública servida por CDN, usada para montar as URLs do índice.
    assets_public_base_url: str = ""

    def has_bucket_credentials(self) -> bool:
        """Sem isto só dá para rodar `--dry-run`."""
        return bool(self.s3_endpoint_url and self.s3_access_key_id and self.s3_secret_access_key)

    #: Só vira `True` depois de o consentimento estar registrado em `docs/SPIKES.md`.
    wiki_consent_granted: bool = False


def user_agent(settings: IndexerSettings) -> str:
    """O formato exato da regra 4."""
    return f"lol-assets-indexer/{__version__} (+{REPO_URL}; {settings.indexer_contact})"


def _should_retry(response: httpx.Response) -> bool:
    """429 e 5xx são temporários. 404 é resposta, não falha."""
    return response.status_code == 429 or response.status_code >= 500


class SourceClient:
    """Cliente com etiqueta. Use como gerenciador de contexto assíncrono."""

    def __init__(
        self,
        settings: IndexerSettings | None = None,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = random.random,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings or IndexerSettings()
        self._sleep = sleep
        self._jitter = jitter
        # Um semáforo por host: o limite da regra 4 é por host, não global.
        self._gates: dict[str, asyncio.Semaphore] = {}
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent(self._settings)},
            timeout=self._settings.indexer_timeout_seconds,
            follow_redirects=True,
            transport=transport,
        )

    @property
    def settings(self) -> IndexerSettings:
        return self._settings

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Uma requisição, com a etiqueta inteira aplicada."""
        self._guard(url)
        async with self._gate_for(url):
            return await self._with_retry(method, url, headers)

    async def get_json(self, url: str) -> Any:
        response = await self.request("GET", url)
        response.raise_for_status()
        return response.json()

    async def get_bytes(self, url: str) -> bytes:
        response = await self.request("GET", url)
        response.raise_for_status()
        return response.content

    # --- interno -------------------------------------------------------------

    def _guard(self, url: str) -> None:
        host = (httpx.URL(url).host or "").lower()
        if host in BLOCKED_HOSTS and not self._settings.wiki_consent_granted:
            raise WikiAccessBlockedError(
                f"regra 3 do CLAUDE.md: acesso automatizado a {host} exige consentimento "
                "prévio da Weird Gloop, registrado em docs/SPIKES.md com data e evidência. "
                "Ligue WIKI_CONSENT_GRANTED só depois disso (ADR 0004)."
            )

    def _gate_for(self, url: str) -> asyncio.Semaphore:
        host = (httpx.URL(url).host or "").lower()
        gate = self._gates.get(host)
        if gate is None:
            gate = asyncio.Semaphore(self._settings.indexer_max_concurrency)
            self._gates[host] = gate
        return gate

    def _delay_for(self, response: httpx.Response | None, current: float) -> float:
        """`Retry-After` numérico manda; senão, exponencial com jitter."""
        if response is not None:
            retry_after = (response.headers.get("Retry-After") or "").strip()
            if retry_after.isdigit():
                return float(retry_after)
        return current + self._jitter()

    async def _with_retry(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None,
    ) -> httpx.Response:
        delay = _BASE_DELAY_SECONDS
        last_response: httpx.Response | None = None
        last_error: httpx.TransportError | None = None

        for attempt in range(1, self._settings.indexer_max_retries + 1):
            try:
                response = await self._client.request(method, url, headers=headers)
            except httpx.TransportError as error:
                last_error, last_response = error, None
            else:
                last_error, last_response = None, response
                if not _should_retry(response):
                    return response

            if attempt == self._settings.indexer_max_retries:
                break
            await self._sleep(self._delay_for(last_response, delay))
            delay = min(delay * 2, _MAX_DELAY_SECONDS)

        if last_response is not None:
            last_response.raise_for_status()
            return last_response
        assert last_error is not None
        raise last_error

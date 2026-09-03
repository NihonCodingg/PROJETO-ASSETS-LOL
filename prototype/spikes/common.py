"""Utilitários compartilhados pelos spikes S1-S3.

Descartável: existe só para produzir os números de `docs/SPIKES.md`.
Respeita a regra 4 do CLAUDE.md — User-Agent identificado, concorrência <= 4 e
backoff exponencial em 429/5xx. NÃO acessa wiki.leagueoflegends.com (regra 3).
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import random
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx
from PIL import Image

SPIKE_VERSION = "0.0.0-spike"
REPO_URL = "https://github.com/NihonCodingg/PROJETO-ASSETS-LOL"

#: Contato público do mantenedor. Nunca use dado pessoal aqui sem pedir.
CONTACT = os.environ.get("INDEXER_CONTACT", f"{REPO_URL}/issues")
USER_AGENT = f"lol-assets-indexer/{SPIKE_VERSION} (+{REPO_URL}; {CONTACT})"

MAX_CONCURRENCY = int(os.environ.get("INDEXER_MAX_CONCURRENCY", "4"))
TIMEOUT = float(os.environ.get("INDEXER_TIMEOUT_SECONDS", "60"))
MAX_RETRIES = int(os.environ.get("INDEXER_MAX_RETRIES", "5"))

HERE = Path(__file__).parent
CACHE_DIR = HERE / ".cache"
RESULTS_DIR = HERE / "results"

BLOCKED_HOSTS = ("wiki.leagueoflegends.com", "leagueoflegends.fandom.com")


def client() -> httpx.AsyncClient:
    """Cliente HTTP com a etiqueta exigida pela regra 4."""
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=MAX_CONCURRENCY),
    )


def _guard(url: str) -> None:
    if any(host in url for host in BLOCKED_HOSTS):
        raise RuntimeError(f"Regra 3: acesso automatizado à wiki é proibido sem consentimento: {url}")


async def request(
    http: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Requisição com backoff exponencial em 429/5xx e respeito a Retry-After."""
    _guard(url)
    delay = 1.0
    last: httpx.Response | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await http.request(method, url, headers=headers)
        except httpx.TransportError:
            if attempt == MAX_RETRIES - 1:
                raise
            await asyncio.sleep(delay + random.random())
            delay *= 2
            continue
        if response.status_code == 429 or response.status_code >= 500:
            last = response
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else delay
            await asyncio.sleep(wait + random.random())
            delay *= 2
            continue
        return response
    assert last is not None
    return last


@dataclass
class Measurement:
    """Uma imagem medida de verdade."""

    url: str
    status: int
    content_type: str = ""
    bytes: int = 0
    format: str = ""
    width: int = 0
    height: int = 0
    mode: str = ""
    note: str = ""


def measure_image_bytes(data: bytes) -> tuple[str, int, int, str]:
    """Formato, largura, altura e modo de cor a partir dos bytes da imagem."""
    with Image.open(io.BytesIO(data)) as image:
        return (image.format or "", image.width, image.height, image.mode)


async def measure_url(http: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore) -> Measurement:
    """Baixa e mede uma imagem. Usa Range quando o servidor suporta, para poupar banda."""
    async with semaphore:
        head = await request(http, "HEAD", url)
        if head.status_code >= 400:
            return Measurement(url=url, status=head.status_code, note="ausente")

        content_type = head.headers.get("Content-Type", "")
        total = int(head.headers.get("Content-Length", "0") or 0)

        partial = await request(http, "GET", url, headers={"Range": "bytes=0-65535"})
        data = partial.content
        try:
            fmt, width, height, mode = measure_image_bytes(data)
        except Exception:
            full = await request(http, "GET", url)
            data = full.content
            total = total or len(data)
            try:
                fmt, width, height, mode = measure_image_bytes(data)
            except Exception as exc:
                return Measurement(
                    url=url,
                    status=head.status_code,
                    content_type=content_type,
                    bytes=total,
                    note=f"não é imagem legível: {type(exc).__name__}",
                )

        return Measurement(
            url=url,
            status=head.status_code,
            content_type=content_type,
            bytes=total or len(data),
            format=fmt,
            width=width,
            height=height,
            mode=mode,
        )


@dataclass
class Report:
    """Saída de um spike, salva como JSON em `results/`."""

    spike: str
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    user_agent: str = USER_AGENT
    data: dict = field(default_factory=dict)

    def save(self) -> Path:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        path = RESULTS_DIR / f"{self.spike}.json"
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

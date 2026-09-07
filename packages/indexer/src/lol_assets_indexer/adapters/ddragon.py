"""Adaptador do Data Dragon — descoberta de versão e as formas normalizadas.

O caminho de ingestão passou a ser o tarball: `tarball.py` mede, `records.py`
monta. O que sobra aqui é o que vem de fora dele — a lista de versões, a URL do
tarball — e as duas formas, `ChampionSnapshot` e `SkinSnapshot`, em que o resto
do código lê um campeão.

O mapa de pastas mora aqui e **só aqui**. É a parte perigosa: ddragon e cdragon
usam `splash` e `centered` com sentidos trocados (ADR 0002). O que o ddragon
chama de `centered` é o corte de 1280x720 — o nosso `splash_centered`. Duas
cópias desse mapa seria convidar a inversão de volta.
"""

from __future__ import annotations

from dataclasses import dataclass

from lol_assets_schema.models import AssetType, LocalizedName

from lol_assets_indexer.http import SourceClient

#: Pasta do ddragon → nome canônico. **Não inverta.** ADR 0002.
SOURCE_FOLDER_TO_TYPE: dict[str, AssetType] = {
    "centered": "splash_centered",
    "splash": "splash_wide",
    "loading": "loading",
    "tiles": "tile",
}

LANGUAGES = ("pt_BR", "en_US")

BASE_SKIN_NUM = 0


@dataclass(frozen=True, slots=True)
class SkinSnapshot:
    """Uma skin de verdade. Chroma não entra aqui — KICKOFF §B.1.4."""

    num: int
    names: LocalizedName
    chroma_count: int


@dataclass(frozen=True, slots=True)
class ChampionSnapshot:
    """A ficha do campeão, já normalizada, para alimentar o catálogo (ADR 0010)."""

    key: int
    champion_id: str
    names: LocalizedName
    title: LocalizedName
    tags: list[str]
    skins: list[SkinSnapshot]
    chroma_count: int


def tarball_url(base: str, game_version: str) -> str:
    """O tarball do patch. 2,39 GB medidos no S1 — uma requisição em vez de ~15 mil."""
    return f"{base.rstrip('/')}/cdn/dragontail-{game_version}.tgz"


async def latest_version(client: SourceClient) -> str:
    """A primeira da lista é a mais recente — KICKOFF §B.1.1."""
    versions = await client.get_json(f"{_base(client)}/api/versions.json")
    if not isinstance(versions, list) or not versions:
        raise ValueError("versions.json não devolveu uma lista de versões")
    return str(versions[0])


def _base(client: SourceClient) -> str:
    return client.settings.ddragon_base_url.rstrip("/")

"""Adaptador do Data Dragon — recorte mínimo (T-05).

Um campeão, dois tipos: `square` e `splash_centered`. O tarball e os demais tipos
chegam no T-09; aqui o que importa é provar o caminho fonte → registro medido.

A tradução de nome vive num mapa só, e é a parte perigosa: ddragon e cdragon usam
`splash` e `centered` com sentidos trocados (ADR 0002). O que o ddragon chama de
`centered` é o corte de 1280x720 — o nosso `splash_centered`.
"""

from __future__ import annotations

from typing import Any

from lol_assets_schema.models import Asset, AssetType, LocalizedName

from lol_assets_indexer.http import SourceClient
from lol_assets_indexer.imaging import measure
from lol_assets_indexer.naming import asset_id, champion_file_name, skin_id, storage_key

#: Pasta do ddragon → nome canônico. **Não inverta.** ADR 0002.
SOURCE_FOLDER_TO_TYPE: dict[str, AssetType] = {
    "centered": "splash_centered",
    "splash": "splash_wide",
}

LANGUAGES = ("pt_BR", "en_US")

#: O recorte do T-05. O T-09 amplia a lista lendo o tarball.
BASE_SKIN_NUM = 0


async def latest_version(client: SourceClient) -> str:
    """A primeira da lista é a mais recente — KICKOFF §B.1.1."""
    versions = await client.get_json(f"{_base(client)}/api/versions.json")
    if not isinstance(versions, list) or not versions:
        raise ValueError("versions.json não devolveu uma lista de versões")
    return str(versions[0])


async def champion_data(
    client: SourceClient, version: str, champion_id: str, language: str
) -> dict[str, Any]:
    """A ficha do campeão num idioma. `id` para URL, `name` para exibição."""
    payload = await client.get_json(
        f"{_base(client)}/cdn/{version}/data/{language}/champion/{champion_id}.json"
    )
    data: dict[str, Any] = payload["data"][champion_id]
    return data


async def build_champion_assets(
    client: SourceClient,
    champion_id: str,
    *,
    version: str | None = None,
) -> list[Asset]:
    """Registros medidos de `square` e `splash_centered` da skin base."""
    game_version = version or await latest_version(client)
    fichas = {
        language: await champion_data(client, game_version, champion_id, language)
        for language in LANGUAGES
    }
    pt = fichas["pt_BR"]
    names = LocalizedName(pt_BR=pt["name"], en_US=fichas["en_US"]["name"])
    # `key` vem como string no ddragon e é a chave de fusão entre fontes (§B.1.5).
    champion_key = int(pt["key"])

    assets = [
        await _build(
            client,
            url=f"{_base(client)}/cdn/{game_version}/img/champion/{champion_id}.png",
            asset_type="square",
            game_version=game_version,
            champion_key=champion_key,
            champion_id=champion_id,
            names=names,
            natural_key=champion_key,
        ),
        await _build(
            client,
            url=(f"{_base(client)}/cdn/img/champion/centered/{champion_id}_{BASE_SKIN_NUM}.jpg"),
            asset_type=SOURCE_FOLDER_TO_TYPE["centered"],
            game_version=game_version,
            champion_key=champion_key,
            champion_id=champion_id,
            names=names,
            natural_key=skin_id(champion_key, BASE_SKIN_NUM),
            skin_num=BASE_SKIN_NUM,
        ),
    ]
    return assets


async def _build(
    client: SourceClient,
    *,
    url: str,
    asset_type: AssetType,
    game_version: str,
    champion_key: int,
    champion_id: str,
    names: LocalizedName,
    natural_key: int,
    skin_num: int | None = None,
) -> Asset:
    """Baixa, mede e monta o registro. Os bytes não são tocados."""
    data = await client.get_bytes(url)
    measured = measure(data)
    file_name = champion_file_name(champion_id, asset_type, measured.format, skin_num=skin_num)

    return Asset(
        id=asset_id(asset_type, natural_key),
        type=asset_type,
        category="champion",
        champion_key=champion_key,
        champion_id=champion_id,
        skin_id=skin_id(champion_key, skin_num) if skin_num is not None else None,
        skin_num=skin_num,
        is_base_skin=(skin_num == BASE_SKIN_NUM) if skin_num is not None else None,
        names=names,
        source="ddragon",
        source_url=url,
        storage_key=storage_key(game_version, "champion", file_name),
        file_name=file_name,
        width=measured.width,
        height=measured.height,
        format=measured.format,
        has_alpha=measured.has_alpha,
        bytes=measured.bytes,
        sha256=measured.sha256,
    )


def _base(client: SourceClient) -> str:
    return client.settings.ddragon_base_url.rstrip("/")

"""Adaptador do Data Dragon — recorte mínimo (T-05).

Um campeão, dois tipos: `square` e `splash_centered`. O tarball e os demais tipos
chegam no T-09; aqui o que importa é provar o caminho fonte → registro medido.

A tradução de nome vive num mapa só, e é a parte perigosa: ddragon e cdragon usam
`splash` e `centered` com sentidos trocados (ADR 0002). O que o ddragon chama de
`centered` é o corte de 1280x720 — o nosso `splash_centered`.
"""

from __future__ import annotations

from dataclasses import dataclass
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

#: Os bytes de origem viajam junto com o registro: quem publica precisa deles, e
#: baixar de novo arriscaria publicar bytes diferentes dos que foram medidos.
FetchedAsset = tuple[Asset, bytes]


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


async def fetch_champion(client: SourceClient, champion_id: str, version: str) -> ChampionSnapshot:
    """Lê a ficha nos dois idiomas e separa skins de chromas."""
    fichas = {
        language: await champion_data(client, version, champion_id, language)
        for language in LANGUAGES
    }
    pt, en = fichas["pt_BR"], fichas["en_US"]
    skins_en = {int(skin["num"]): skin for skin in en.get("skins", [])}

    skins: list[SkinSnapshot] = []
    chromas = 0
    for skin in pt.get("skins", []):
        # `parentSkin` só existe em chroma; skin de verdade não tem o campo.
        if "parentSkin" in skin:
            chromas += 1
            continue
        num = int(skin["num"])
        nome_pt = pt["name"] if num == 0 else skin["name"]
        nome_en = en["name"] if num == 0 else skins_en.get(num, {}).get("name", skin["name"])
        skins.append(
            SkinSnapshot(
                num=num,
                names=LocalizedName(pt_BR=nome_pt, en_US=nome_en),
                chroma_count=sum(
                    1 for outra in pt.get("skins", []) if outra.get("parentSkin") == num
                ),
            )
        )

    return ChampionSnapshot(
        key=int(pt["key"]),
        champion_id=champion_id,
        names=LocalizedName(pt_BR=pt["name"], en_US=en["name"]),
        title=LocalizedName(pt_BR=pt["title"], en_US=en["title"]),
        tags=list(pt.get("tags", [])),
        skins=skins,
        chroma_count=chromas,
    )


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
    return [asset for asset, _ in await fetch_champion_assets(client, champion_id, version=version)]


async def fetch_champion_assets(
    client: SourceClient,
    champion_id: str,
    *,
    version: str | None = None,
) -> list[FetchedAsset]:
    """O mesmo, mas devolvendo os bytes junto — é o que a publicação precisa."""
    game_version = version or await latest_version(client)
    snapshot = await fetch_champion(client, champion_id, game_version)

    return [
        await _build(
            client,
            url=f"{_base(client)}/cdn/{game_version}/img/champion/{champion_id}.png",
            asset_type="square",
            game_version=game_version,
            snapshot=snapshot,
            natural_key=snapshot.key,
        ),
        await _build(
            client,
            url=(f"{_base(client)}/cdn/img/champion/centered/{champion_id}_{BASE_SKIN_NUM}.jpg"),
            asset_type=SOURCE_FOLDER_TO_TYPE["centered"],
            game_version=game_version,
            snapshot=snapshot,
            natural_key=skin_id(snapshot.key, BASE_SKIN_NUM),
            skin_num=BASE_SKIN_NUM,
        ),
    ]


async def _build(
    client: SourceClient,
    *,
    url: str,
    asset_type: AssetType,
    game_version: str,
    snapshot: ChampionSnapshot,
    natural_key: int,
    skin_num: int | None = None,
) -> FetchedAsset:
    """Baixa, mede e monta o registro. Os bytes não são tocados."""
    data = await client.get_bytes(url)
    measured = measure(data)
    champion_id = snapshot.champion_id
    file_name = champion_file_name(champion_id, asset_type, measured.format, skin_num=skin_num)

    asset = Asset(
        id=asset_id(asset_type, natural_key),
        type=asset_type,
        category="champion",
        champion_key=snapshot.key,
        champion_id=champion_id,
        skin_id=skin_id(snapshot.key, skin_num) if skin_num is not None else None,
        skin_num=skin_num,
        is_base_skin=(skin_num == BASE_SKIN_NUM) if skin_num is not None else None,
        names=snapshot.names,
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
    return asset, data


def _base(client: SourceClient) -> str:
    return client.settings.ddragon_base_url.rstrip("/")

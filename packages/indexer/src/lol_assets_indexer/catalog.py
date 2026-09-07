"""Projeção do catálogo — as duas superfícies do ADR 0010.

`champions[]` é a grade padrão (navegação); `skins[]` é o índice de busca. Nenhum
asset entra aqui: o catálogo é o único documento pesado da abertura do site, e é
o que permite desenhar a home antes de qualquer imagem existir.

O T-07 projeta um campeão; o T-10 escala a mesma função para o catálogo inteiro.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from lol_assets_schema.models import Asset, Catalog, CatalogChampion, CatalogSkin

from lol_assets_indexer.adapters.ddragon import ChampionSnapshot
from lol_assets_indexer.naming import skin_id


def project_catalog(
    *,
    game_version: str,
    generated_at: str,
    snapshots: Iterable[ChampionSnapshot],
    assets_by_champion: Mapping[int, list[Asset]] | None = None,
    assets_base_url: str | None = None,
) -> Catalog:
    """Monta o catálogo a partir das fichas dos campeões."""
    assets_by_champion = assets_by_champion or {}
    champions: list[CatalogChampion] = []
    skins: list[CatalogSkin] = []

    for snapshot in snapshots:
        do_campeao = assets_by_champion.get(snapshot.key, [])
        # A miniatura do cartão é o `square`; a do resultado de busca é o `tile`.
        square_key, square_url = _thumbnail(a for a in do_campeao if a.type == "square")
        tiles = {a.skin_num: a for a in do_campeao if a.type == "tile"}

        champions.append(
            CatalogChampion(
                champion_key=snapshot.key,
                champion_id=snapshot.champion_id,
                names=snapshot.names,
                title=snapshot.title,
                tags=snapshot.tags or None,
                skin_count=len(snapshot.skins),
                chroma_count=snapshot.chroma_count,
                base_skin_id=skin_id(snapshot.key, 0),
                thumbnail_key=square_key,
                thumbnail_url=square_url,
            )
        )
        for skin in snapshot.skins:
            tile = tiles.get(skin.num)
            tile_key, tile_url = _thumbnail([tile] if tile is not None else [])
            skins.append(
                CatalogSkin(
                    skin_id=skin_id(snapshot.key, skin.num),
                    skin_num=skin.num,
                    champion_key=snapshot.key,
                    names=skin.names,
                    is_base=skin.num == 0,
                    chroma_count=skin.chroma_count,
                    thumbnail_key=tile_key,
                    thumbnail_url=tile_url,
                )
            )

    return Catalog(
        schema_version=_schema_version(),
        game_version=game_version,
        generated_at=generated_at,
        assets_base_url=assets_base_url or None,
        champions=champions,
        skins=skins,
    )


def _thumbnail(assets: Iterable[Asset]) -> tuple[str | None, str | None]:
    """`(thumbnailKey, thumbnailUrl)` do primeiro asset da sequência.

    Com storage, a miniatura é a chave no bucket. Sem storage (ADR 0012), é a URL
    da fonte. O schema aceita os dois desde o começo e o front lê os dois — é isso
    que faz a volta para a opção A ser barata.
    """
    for asset in assets:
        if asset.storage_key:
            return asset.storage_key, None
        return None, asset.source_url
    return None, None


def _schema_version() -> str:
    from lol_assets_schema import SCHEMA_VERSION

    return SCHEMA_VERSION

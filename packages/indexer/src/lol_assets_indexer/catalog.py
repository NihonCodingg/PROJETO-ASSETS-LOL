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
                thumbnail_key=_square_key(assets_by_champion.get(snapshot.key, [])),
            )
        )
        skins.extend(
            CatalogSkin(
                skin_id=skin_id(snapshot.key, skin.num),
                skin_num=skin.num,
                champion_key=snapshot.key,
                names=skin.names,
                is_base=skin.num == 0,
                chroma_count=skin.chroma_count,
                # A miniatura da skin é o `tile`, que só existe a partir do T-09.
                thumbnail_key=None,
            )
            for skin in snapshot.skins
        )

    return Catalog(
        schema_version=_schema_version(),
        game_version=game_version,
        generated_at=generated_at,
        assets_base_url=assets_base_url or None,
        champions=champions,
        skins=skins,
    )


def _square_key(assets: list[Asset]) -> str | None:
    """A miniatura do cartão é o square, que já é publicado desde o T-05."""
    for asset in assets:
        if asset.type == "square":
            return asset.storage_key
    return None


def _schema_version() -> str:
    from lol_assets_schema import SCHEMA_VERSION

    return SCHEMA_VERSION

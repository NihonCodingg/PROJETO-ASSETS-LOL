"""CLI do indexador — o comando que o GitHub Actions vai chamar (T-13).

O `index` faz o caminho inteiro de uma vez: descobre a versão, lê a fonte, mede,
projeta o catálogo, **valida tudo** e só então publica. A validação vem antes de
qualquer escrita de propósito: um registro inválido precisa abortar sem ter
deixado nada meio publicado no bucket.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import (
    Asset,
    CatalogRef,
    IndexManifest,
    IndexShard,
    ManifestVersion,
    ShardRef,
)
from lol_assets_schema.validators import validate_catalog, validate_shard

from lol_assets_indexer import __version__, logging_setup
from lol_assets_indexer.adapters.ddragon import (
    FetchedAsset,
    fetch_champion,
    fetch_champion_assets,
    latest_version,
)
from lol_assets_indexer.catalog import project_catalog
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_indexer.publish.bucket import build_store
from lol_assets_indexer.publish.storage import LocalObjectStore, ObjectStore, Publisher

logger = logging.getLogger("lol_assets_indexer.cli")

app = typer.Typer(help="Indexador de assets de League of Legends.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Agrupa os subcomandos; sem ele o Typer achata um app de comando único."""


@app.command()
def version() -> None:
    """Imprime a versão do indexador."""
    typer.echo(__version__)


@app.command()
def index(
    champion: Annotated[
        str,
        typer.Option("--champion", help="Id interno do campeão no ddragon, ex.: Jax."),
    ],
    game_version: Annotated[
        str | None,
        typer.Option("--game-version", help="Patch a indexar. Sem isto, usa o mais recente."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Escreve numa pasta local em vez do bucket."),
    ] = False,
    output: Annotated[
        Path,
        typer.Option("--output", help="Pasta de destino do --dry-run."),
    ] = Path("dist/bucket"),
) -> None:
    """Indexa um campeão e publica catálogo, fatia e manifesto."""
    logging_setup.configure()
    settings = IndexerSettings()

    try:
        resumo = asyncio.run(
            _run(
                settings=settings,
                champion_id=champion,
                game_version=game_version,
                dry_run=dry_run,
                output=output,
            )
        )
    except Exception as erro:
        logger.error(
            "indexação falhou",
            extra={"failure": str(erro), "kind": type(erro).__name__},
        )
        raise typer.Exit(code=1) from erro

    typer.echo(
        f"{resumo['assets']} assets · {resumo['champions']} campeão(ões) · "
        f"{resumo['skins']} skins · patch {resumo['gameVersion']} · "
        f"destino {resumo['destination']}"
    )


async def _run(
    *,
    settings: IndexerSettings,
    champion_id: str,
    game_version: str | None,
    dry_run: bool,
    output: Path,
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with SourceClient(settings) as client:
        resolved_version = game_version or await latest_version(client)
        logging_setup.bind(gameVersion=resolved_version, source="ddragon")
        logger.info("indexação iniciada", extra={"champion": champion_id, "dryRun": dry_run})

        snapshot = await fetch_champion(client, champion_id, resolved_version)
        fetched = await fetch_champion_assets(client, champion_id, version=resolved_version)

    assets = [asset for asset, _ in fetched]
    shard = IndexShard(
        schema_version=SCHEMA_VERSION,
        game_version=resolved_version,
        category="champion",
        generated_at=generated_at,
        assets_base_url=settings.assets_public_base_url or None,
        assets=assets,
    )
    catalog = project_catalog(
        game_version=resolved_version,
        generated_at=generated_at,
        snapshots=[snapshot],
        assets_by_champion={snapshot.key: assets},
        assets_base_url=settings.assets_public_base_url or None,
    )

    # Validação ANTES de qualquer escrita: é isso que garante que um registro
    # inválido não deixe o bucket meio publicado.
    validate_shard(shard.model_dump(by_alias=True, exclude_none=True, mode="json"))
    validate_catalog(catalog.model_dump(by_alias=True, exclude_none=True, mode="json"))
    logger.info("documentos validados", extra={"assets": len(assets), "skins": len(catalog.skins)})

    store = _build_store(settings, dry_run=dry_run, output=output)
    publisher = Publisher(store)

    _publish_assets(publisher, fetched)
    catalog_ref = publisher.publish_catalog(catalog)
    shard_ref = publisher.publish_shard(shard)
    publisher.publish_manifest(
        _build_manifest(
            settings=settings,
            game_version=resolved_version,
            generated_at=generated_at,
            catalog_ref=catalog_ref,
            shard_ref=shard_ref,
            assets=assets,
        )
    )

    destination = str(output) if dry_run else settings.s3_bucket
    logger.info("publicação concluída", extra={"destination": destination})
    return {
        "assets": len(assets),
        "champions": len(catalog.champions),
        "skins": len(catalog.skins),
        "gameVersion": resolved_version,
        "destination": destination,
    }


def _build_store(settings: IndexerSettings, *, dry_run: bool, output: Path) -> ObjectStore:
    if dry_run:
        return LocalObjectStore(root=output)
    return build_store(settings)


def _publish_assets(publisher: Publisher, fetched: list[FetchedAsset]) -> None:
    for asset, data in fetched:
        if asset.storage_key is None:
            raise ValueError(f"asset {asset.id} sem storageKey não pode ser publicado")
        publisher.publish_asset(asset.storage_key, data)


def _build_manifest(
    *,
    settings: IndexerSettings,
    game_version: str,
    generated_at: str,
    catalog_ref: CatalogRef,
    shard_ref: ShardRef,
    assets: list[Asset],
) -> IndexManifest:
    return IndexManifest(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        assets_base_url=settings.assets_public_base_url or None,
        current_version=game_version,
        versions=[
            ManifestVersion(
                game_version=game_version,
                indexed_at=generated_at,
                assets_copied=True,
                catalog=catalog_ref,
                total_assets=len(assets),
                total_bytes=sum(asset.bytes for asset in assets),
                shards=[shard_ref],
            )
        ],
    )


if __name__ == "__main__":  # pragma: no cover
    app()

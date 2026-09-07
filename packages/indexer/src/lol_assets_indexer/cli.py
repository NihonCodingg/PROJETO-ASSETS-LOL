"""CLI do indexador — o comando que o GitHub Actions vai chamar (T-13).

O `index` faz o caminho inteiro numa tacada: descobre a versão, baixa o tarball,
mede tudo numa passada, projeta o catálogo, **valida** e só então escreve.

Desde o [ADR 0012] o indexador **não copia asset nenhum**. Ele baixa o tarball
para medir e joga os bytes fora; o que é escrito são três documentos — manifesto,
catálogo e fatias —, servidos como estáticos pelo próprio app. Por isso o
`--dry-run` mudou de sentido: antes era "escreve local em vez do bucket", agora é
"mede e valida sem escrever nada", que é o único ensaio que ainda sobra.

A validação vem antes de qualquer escrita de propósito: um registro inválido
precisa abortar sem ter deixado nada meio escrito.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import Asset, IndexManifest, IndexShard, ManifestVersion
from lol_assets_schema.validators import validate_catalog, validate_shard

from lol_assets_indexer import __version__, logging_setup
from lol_assets_indexer.adapters.ddragon import latest_version, tarball_url
from lol_assets_indexer.adapters.records import build_all, build_champion_snapshots
from lol_assets_indexer.adapters.tarball import TarballScan, scan_tarball
from lol_assets_indexer.catalog import project_catalog
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_indexer.publish.storage import LocalObjectStore, Publisher

logger = logging.getLogger("lol_assets_indexer.cli")

app = typer.Typer(help="Indexador de assets de League of Legends.", no_args_is_help=True)

#: O índice é servido pelo próprio Next como estático — ADR 0012.
DEFAULT_OUTPUT = Path("apps/web/public/indice")


@app.callback()
def main() -> None:
    """Agrupa os subcomandos; sem ele o Typer achata um app de comando único."""


@app.command()
def version() -> None:
    """Imprime a versão do indexador."""
    typer.echo(__version__)


@app.command()
def index(
    game_version: Annotated[
        str | None,
        typer.Option("--game-version", help="Patch a indexar. Sem isto, usa o mais recente."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Mede e valida sem escrever nada."),
    ] = False,
    output: Annotated[
        Path,
        typer.Option("--output", help="Pasta onde o índice é escrito."),
    ] = DEFAULT_OUTPUT,
    tarball: Annotated[
        Path | None,
        typer.Option("--tarball", help="Usa um tarball já baixado em vez de buscar de novo."),
    ] = None,
) -> None:
    """Indexa o patch inteiro: manifesto, catálogo e fatias."""
    logging_setup.configure()
    settings = IndexerSettings()

    try:
        resumo = asyncio.run(
            _run(
                settings=settings,
                game_version=game_version,
                dry_run=dry_run,
                output=output,
                tarball=tarball,
            )
        )
    except Exception as erro:
        logger.error(
            "indexação falhou",
            extra={"failure": str(erro), "kind": type(erro).__name__},
        )
        raise typer.Exit(code=1) from erro

    typer.echo(
        f"{resumo['assets']} assets · {resumo['champions']} campeões · "
        f"{resumo['skins']} skins · {resumo['categories']} categorias · "
        f"patch {resumo['gameVersion']} · destino {resumo['destination']}"
    )


async def _scan_source(
    settings: IndexerSettings, game_version: str | None, tarball: Path | None
) -> TarballScan:
    """Resolve a versão, garante o tarball em disco e faz uma passada nele."""
    if tarball is not None:
        resolved = game_version or _version_from_name(tarball)
        logging_setup.bind(gameVersion=resolved, source="ddragon")
        logger.info("tarball local", extra={"path": str(tarball)})
        with tarball.open("rb") as handle:
            return scan_tarball(handle, resolved)

    async with SourceClient(settings) as client:
        resolved = game_version or await latest_version(client)
        logging_setup.bind(gameVersion=resolved, source="ddragon")
        logger.info("indexação iniciada", extra={"tarball": True})

        # Vai para disco antes de ser lido: um engasgo de rede no meio da
        # varredura custaria a passada inteira, e ela dura minutos.
        with tempfile.TemporaryDirectory(prefix="lol-assets-") as temporario:
            destino = Path(temporario) / f"dragontail-{resolved}.tgz"
            baixados = await client.stream_to(
                tarball_url(settings.ddragon_base_url, resolved), destino
            )
            logger.info("tarball em disco", extra={"bytes": baixados})
            with destino.open("rb") as handle:
                return scan_tarball(handle, resolved)


def _version_from_name(tarball: Path) -> str:
    """`dragontail-16.17.1.tgz` vira `16.17.1`."""
    miolo = tarball.name.removeprefix("dragontail-").removesuffix(".tgz")
    if not miolo or miolo == tarball.name:
        raise ValueError(f"não dá para deduzir a versão de {tarball.name!r}; passe --game-version")
    return miolo


async def _run(
    *,
    settings: IndexerSettings,
    game_version: str | None,
    dry_run: bool,
    output: Path,
    tarball: Path | None,
) -> dict[str, Any]:
    generated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    scan = await _scan_source(settings, game_version, tarball)

    por_categoria = {categoria: assets for categoria, assets in build_all(scan).items() if assets}
    catalog = project_catalog(
        game_version=scan.game_version,
        generated_at=generated_at,
        snapshots=build_champion_snapshots(scan),
        assets_by_champion=_por_campeao(por_categoria.get("champion", [])),
    )
    shards = [
        IndexShard(
            schema_version=SCHEMA_VERSION,
            game_version=scan.game_version,
            category=categoria,
            generated_at=generated_at,
            assets=assets,
        )
        for categoria, assets in por_categoria.items()
    ]

    # Validação ANTES de qualquer escrita.
    validate_catalog(catalog.model_dump(by_alias=True, exclude_none=True, mode="json"))
    for shard in shards:
        validate_shard(shard.model_dump(by_alias=True, exclude_none=True, mode="json"))

    total_assets = sum(len(assets) for assets in por_categoria.values())
    total_bytes = sum(asset.bytes for assets in por_categoria.values() for asset in assets)
    logger.info(
        "documentos validados",
        extra={
            "assets": total_assets,
            "bytes": total_bytes,
            "categorias": len(shards),
            "campeoes": len(catalog.champions),
            "skins": len(catalog.skins),
            "descartadas": scan.skipped,
            "ilegiveis": sum(scan.unreadable.values()),
            "caixaDivergente": len(scan.case_mismatches),
        },
    )

    resumo: dict[str, Any] = {
        "assets": total_assets,
        "champions": len(catalog.champions),
        "skins": len(catalog.skins),
        "categories": len(shards),
        "gameVersion": scan.game_version,
        "destination": "nada escrito (--dry-run)" if dry_run else str(output),
    }
    if dry_run:
        logger.info("dry-run: nada escrito")
        return resumo

    publisher = Publisher(LocalObjectStore(root=output))
    catalog_ref = publisher.publish_catalog(catalog)
    shard_refs = [publisher.publish_shard(shard) for shard in shards]
    publisher.publish_manifest(
        IndexManifest(
            schema_version=SCHEMA_VERSION,
            generated_at=generated_at,
            current_version=scan.game_version,
            versions=[
                ManifestVersion(
                    game_version=scan.game_version,
                    indexed_at=generated_at,
                    # ADR 0012: nada é copiado, então isto nunca é `true`.
                    assets_copied=False,
                    catalog=catalog_ref,
                    total_assets=total_assets,
                    total_bytes=total_bytes,
                    shards=shard_refs,
                )
            ],
        )
    )
    logger.info("índice escrito", extra={"destination": str(output)})
    return resumo


def _por_campeao(assets: list[Asset]) -> dict[int, list[Asset]]:
    """O catálogo só precisa dos assets do campeão para escolher a miniatura."""
    agrupado: dict[int, list[Asset]] = {}
    for asset in assets:
        if asset.champion_key is not None:
            agrupado.setdefault(asset.champion_key, []).append(asset)
    return agrupado


if __name__ == "__main__":  # pragma: no cover
    app()

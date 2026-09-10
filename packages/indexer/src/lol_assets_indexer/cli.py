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
import hashlib
import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer
from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import (
    Asset,
    AssetCategory,
    AssetType,
    IndexManifest,
    IndexShard,
    IndexStatus,
    ManifestVersion,
)
from lol_assets_schema.validators import validate_status

from lol_assets_indexer import __version__, logging_setup
from lol_assets_indexer.adapters.cdragon import fetch_champion_assets, fetch_emotes, fetch_wards
from lol_assets_indexer.adapters.ddragon import latest_version, tarball_url
from lol_assets_indexer.adapters.records import BUILDERS, build_all, build_champion_snapshots
from lol_assets_indexer.adapters.tarball import TarballScan, scan_tarball
from lol_assets_indexer.catalog import project_catalog, verify_catalog
from lol_assets_indexer.github import reporter_from_env
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_indexer.limits import BudgetReport, check_budget, measure
from lol_assets_indexer.merge import MergeReport, merge_assets
from lol_assets_indexer.publish.storage import (
    MANIFEST_KEY,
    LocalObjectStore,
    Publisher,
    prepare_catalog,
    prepare_manifest,
    prepare_shard,
)
from lol_assets_indexer.scheduling import (
    current_generation,
    decide,
    published,
    write_github_output,
)
from lol_assets_indexer.status import build_status, render_summary

logger = logging.getLogger("lol_assets_indexer.cli")

app = typer.Typer(help="Indexador de assets de League of Legends.", no_args_is_help=True)

#: As categorias que só o cdragon tem. Ver `_categorias_so_do_cdragon`.
CATEGORIAS_DO_CDRAGON: tuple[AssetCategory, ...] = ("emote", "ward")

#: Tudo o que uma execução completa emite — a lista que entra na assinatura de
#: geração do T-38. Mora aqui, e não repetida em dois lugares, porque "a lista de
#: categorias" ser duas listas é exatamente como uma delas fica para trás.
CATEGORIAS: tuple[AssetCategory, ...] = tuple(BUILDERS) + CATEGORIAS_DO_CDRAGON

#: O que se busca no cdragon quando o ddragon não traz. Ver `_fundir_com_cdragon`.
TIPOS_DO_CDRAGON: tuple[AssetType, ...] = (
    "chroma",
    "loading_vintage",
    "splash_centered",
    "splash_wide",
    "loading",
    "tile",
    "square",
    "passive_icon",
    "ability_icon",
)

#: O índice é servido pelo próprio Next como estático — ADR 0012.
DEFAULT_OUTPUT = Path("apps/web/public/indice")


#: Nome fixo, ao lado do índice. É o que responde "a indexação de hoje rodou?".
STATUS_KEY = "status.json"


@dataclass
class _Execucao:
    """O que a execução foi descobrindo pelo caminho.

    Existe para o `status.json` poder ser escrito **mesmo quando a indexação
    falha**: o que já se sabia até o ponto da falha vai para o relatório.
    """

    started_at: str
    game_version: str | None = None
    scan: TarballScan | None = None
    por_categoria: dict[str, list[Asset]] = field(default_factory=dict)
    champions: int | None = None
    skins: int | None = None
    budget: BudgetReport | None = None
    fusao: MergeReport | None = None


@app.callback()
def main() -> None:
    """Agrupa os subcomandos; sem ele o Typer achata um app de comando único."""


@app.command()
def version() -> None:
    """Imprime a versão do indexador."""
    typer.echo(__version__)


@app.command()
def check(
    output: Annotated[
        Path,
        typer.Option("--output", help="Pasta do índice publicado."),
    ] = DEFAULT_OUTPUT,
) -> None:
    """Diz se há patch novo, sem baixar nada.

    É o primeiro passo do workflow do T-13: na maioria das execuções não há nada
    a fazer, e "nada a fazer" tem que custar segundos, não os ~15 minutos de
    baixar 2,39 GB.
    """
    logging_setup.configure()
    settings = IndexerSettings()

    try:
        latest = asyncio.run(_latest(settings))
    except Exception as erro:
        logger.error(
            "não consegui consultar a versão mais recente",
            extra={"failure": str(erro), "kind": type(erro).__name__},
        )
        raise typer.Exit(code=1) from erro

    # A assinatura desta execucao usa as categorias que os construtores emitem,
    # sem indexar nada: e so a tabela BUILDERS mais o que so o cdragon traz.
    decisao = decide(latest, published(output), generation=current_generation(CATEGORIAS))
    write_github_output(decisao)
    logger.info(
        "decisão de indexação",
        extra={
            "needsIndex": decisao.needs_index,
            "latest": decisao.latest,
            "indexed": decisao.indexed,
        },
    )
    typer.echo(f"{'indexar' if decisao.needs_index else 'nada a fazer'}: {decisao.reason}")


async def _latest(settings: IndexerSettings) -> str:
    async with SourceClient(settings) as client:
        return await latest_version(client)


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
    summary: Annotated[
        Path | None,
        typer.Option("--summary", help="Onde escrever o resumo em Markdown do job."),
    ] = None,
    cdragon: Annotated[
        bool,
        typer.Option("--cdragon/--sem-cdragon", help="Buscar do cdragon o que o ddragon não tem."),
    ] = True,
) -> None:
    """Indexa o patch inteiro: manifesto, catálogo e fatias."""
    logging_setup.configure()
    settings = IndexerSettings()

    relogio = time.monotonic()
    execucao = _Execucao(started_at=_agora())
    falha: Exception | None = None
    resumo: dict[str, Any] = {}

    try:
        resumo = asyncio.run(
            _run(
                settings=settings,
                game_version=game_version,
                dry_run=dry_run,
                output=output,
                tarball=tarball,
                execucao=execucao,
                cdragon=cdragon,
            )
        )
    except Exception as erro:
        falha = erro
        logger.error(
            "indexação falhou",
            extra={"failure": str(erro), "kind": type(erro).__name__},
        )

    # O relatório vem antes da saída: uma falha aqui não pode esconder o motivo
    # dela mesma. Em `--dry-run` nada é escrito, nem isto — é o combinado.
    status = build_status(
        started_at=execucao.started_at,
        finished_at=_agora(),
        duration_seconds=time.monotonic() - relogio,
        game_version=execucao.game_version,
        run_id=os.environ.get("GITHUB_RUN_ID") or None,
        failure=falha,
        scan=execucao.scan,
        assets_by_category=execucao.por_categoria or None,
        catalog_champions=execucao.champions,
        catalog_skins=execucao.skins,
        budget=execucao.budget,
        merge=execucao.fusao,
    )
    if not dry_run:
        _entregar_status(status, output=output, summary=summary)

    if falha is not None:
        raise typer.Exit(code=1) from falha

    typer.echo(
        f"{resumo['assets']} assets · {resumo['champions']} campeões · "
        f"{resumo['skins']} skins · {resumo['categories']} categorias · "
        f"patch {resumo['gameVersion']} · índice de {_milhar(resumo['indexBytes'])} bytes · "
        f"destino {resumo['destination']}"
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
    execucao: _Execucao,
    cdragon: bool = False,
) -> dict[str, Any]:
    generated_at = _agora()
    scan = await _scan_source(settings, game_version, tarball)
    execucao.scan = scan
    execucao.game_version = scan.game_version

    por_categoria = {categoria: assets for categoria, assets in build_all(scan).items() if assets}
    if cdragon:
        por_categoria["champion"], execucao.fusao = await _fundir_com_cdragon(
            settings, scan, por_categoria.get("champion", [])
        )
        # Emotes e wards não vêm do tarball: só existem no cdragon (T-22).
        for categoria, assets in (await _categorias_so_do_cdragon(settings)).items():
            if assets:
                por_categoria[categoria] = assets
    execucao.por_categoria = {str(c): a for c, a in por_categoria.items()}
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

    execucao.champions = len(catalog.champions)
    execucao.skins = len(catalog.skins)
    total_assets = sum(len(assets) for assets in por_categoria.values())
    total_bytes = sum(asset.bytes for assets in por_categoria.values() for asset in assets)

    # Tudo é serializado, validado e MEDIDO antes de o primeiro arquivo existir.
    # É isso que faz o estouro de orçamento abortar sem deixar índice pela metade.
    verify_catalog(catalog)
    catalog_ref, catalog_payload = prepare_catalog(catalog)
    fatias = [prepare_shard(shard) for shard in shards]
    # Uma versão só, sempre (ADR 0013). A anterior sai do manifesto aqui e some do
    # destino na varredura, depois — nunca antes.
    manifest = IndexManifest(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        current_version=scan.game_version,
        # T-38: o que foi **realmente** emitido, não o que uma execução padrão
        # emitiria. Rodar com `--sem-cdragon` grava uma assinatura menor, e a
        # próxima execução reindexa por causa disso — que é o certo.
        generation=current_generation(por_categoria),
        versions=[
            ManifestVersion(
                game_version=scan.game_version,
                indexed_at=generated_at,
                # ADR 0012: nada é copiado, então isto nunca é `true`.
                assets_copied=False,
                catalog=catalog_ref,
                total_assets=total_assets,
                total_bytes=total_bytes,
                shards=[ref for ref, _ in fatias],
            )
        ],
    )
    manifest_payload = prepare_manifest(manifest)

    report = check_budget(
        BudgetReport(
            catalog=measure("catalog", catalog_payload),
            shards=tuple(
                measure(shard.category, payload)
                for shard, (_, payload) in zip(shards, fatias, strict=True)
            ),
            manifest=measure("manifest", manifest_payload),
        )
    )
    execucao.budget = report

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
            **report.as_log(),
        },
    )

    resumo: dict[str, Any] = {
        "assets": total_assets,
        "champions": len(catalog.champions),
        "skins": len(catalog.skins),
        "categories": len(shards),
        "gameVersion": scan.game_version,
        "indexBytes": report.total_raw,
        "destination": "nada escrito (--dry-run)" if dry_run else str(output),
    }
    if dry_run:
        logger.info("dry-run: nada escrito")
        return resumo

    publisher = Publisher(LocalObjectStore(root=output))
    publisher.publish_catalog(catalog, (catalog_ref, catalog_payload))
    for shard, preparada in zip(shards, fatias, strict=True):
        publisher.publish_shard(shard, preparada)
    publisher.publish_manifest(manifest, manifest_payload)

    # Só depois do manifesto novo estar escrito — a trava que o ADR 0007 pede para
    # passo destrutivo, e o que apaga a versão anterior (ADR 0013).
    removidos = _varrer_orfaos(output, publisher.published_keys)
    logger.info(
        "índice escrito",
        extra={"destination": str(output), "orfaosRemovidos": removidos},
    )
    resumo["sweptDocuments"] = removidos
    return resumo


async def _categorias_so_do_cdragon(
    settings: IndexerSettings,
) -> dict[AssetCategory, list[Asset]]:
    """Emotes e ward skins. Falhar aqui custa a categoria, não a indexação."""
    buscadores: tuple[tuple[AssetCategory, Any], ...] = tuple(
        zip(CATEGORIAS_DO_CDRAGON, (fetch_emotes, fetch_wards), strict=True)
    )
    resultado: dict[AssetCategory, list[Asset]] = {}
    async with SourceClient(settings) as client:
        for categoria, buscar in buscadores:
            try:
                assets, _ = await buscar(client)
            except Exception as erro:
                logger.info(
                    "categoria do cdragon falhou",
                    extra={"categoria": categoria, "kind": type(erro).__name__},
                )
                continue
            resultado[categoria] = assets
    return resultado


async def _fundir_com_cdragon(
    settings: IndexerSettings, scan: TarballScan, do_ddragon: list[Asset]
) -> tuple[list[Asset], MergeReport]:
    """Busca no cdragon **só o que o ddragon não trouxe** e funde.

    Medido: o cdragon responde a 2,8 assets/s com a concorrência de 4 da regra 4
    do CLAUDE.md. Buscar os 173 campeões inteiros custaria ~2 horas por patch, e
    o S2 já mediu que square, splash, loading e tile **empatam** entre as duas
    fontes — pagar duas horas para confirmar empate seria caro e inútil.

    O que se busca é a cobertura que o ddragon não tem: `chroma` e
    `loading_vintage`. A hipótese de empate continua **verificada**, não assumida:
    um punhado de campeões por execução vem completo, e o relatório de fusão
    denuncia se o cdragon vencer alguma disputa por resolução.
    """
    tipos_do_ddragon = {asset.type for asset in do_ddragon}
    faltando = [tipo for tipo in TIPOS_DO_CDRAGON if tipo not in tipos_do_ddragon]
    snapshots = build_champion_snapshots(scan)
    amostra = _amostra_de_verificacao(scan.game_version, [s.key for s in snapshots])

    do_cdragon: list[Asset] = []
    nao_mapeaveis: dict[str, str] = {}
    async with SourceClient(settings) as client:
        for snapshot in snapshots:
            completo = snapshot.key in amostra
            try:
                assets, restos = await fetch_champion_assets(
                    client, snapshot.key, only=None if completo else faltando
                )
            except Exception as erro:
                logger.info(
                    "cdragon falhou para um campeão",
                    extra={"campeao": snapshot.champion_id, "kind": type(erro).__name__},
                )
                continue
            do_cdragon.extend(assets)
            nao_mapeaveis.update(restos)

    fundidos, relatorio = merge_assets(do_ddragon, do_cdragon)
    logger.info(
        "cdragon consultado",
        extra={
            "campeoes": len(snapshots),
            "amostraCompleta": len(amostra),
            "assets": len(do_cdragon),
            "naoMapeaveis": len(nao_mapeaveis),
            **relatorio.as_log(),
        },
    )
    return fundidos, relatorio


def _amostra_de_verificacao(game_version: str, chaves: list[int], quantos: int = 12) -> set[int]:
    """Os campeões que vêm completos do cdragon nesta execução.

    Gira com o patch: em ~15 patches todo campeão terá sido conferido pelo menos
    uma vez. Eram 3 quando o cdragon respondia a 2,8 assets/s; com a busca em
    paralelo são 32/s, e 12 campeões custam ~45 s.
    """
    if not chaves:
        return set()
    ordenadas = sorted(chaves)
    inicio = int(hashlib.sha256(game_version.encode()).hexdigest(), 16) % len(ordenadas)
    return {ordenadas[(inicio + i) % len(ordenadas)] for i in range(min(quantos, len(ordenadas)))}


def _agora() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _entregar_status(status: IndexStatus, *, output: Path, summary: Path | None) -> None:
    """Escreve `status.json`, o resumo do job, e abre a issue se falhou.

    Nesta ordem de propósito: o arquivo é o registro durável, o resumo é
    conveniência, e a issue depende de rede. Se a rede falhar, os dois primeiros
    já aconteceram.
    """
    documento = status.model_dump(by_alias=True, exclude_none=True, mode="json")
    validate_status(documento)
    output.mkdir(parents=True, exist_ok=True)
    (output / STATUS_KEY).write_text(
        json.dumps(documento, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    logger.info("status escrito", extra={"ok": status.ok, "arquivo": STATUS_KEY})

    destino = summary or (
        Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None
    )
    if destino is not None:
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("a", encoding="utf-8") as arquivo:
            arquivo.write(render_summary(status))

    if status.ok:
        return
    reporter = reporter_from_env()
    if reporter is None:
        logger.info("sem GITHUB_TOKEN: nenhuma issue aberta")
        return
    reporter.report(status, run_url=_run_url())


def _run_url() -> str | None:
    servidor = os.environ.get("GITHUB_SERVER_URL")
    repositorio = os.environ.get("GITHUB_REPOSITORY")
    execucao = os.environ.get("GITHUB_RUN_ID")
    if not (servidor and repositorio and execucao):
        return None
    return f"{servidor}/{repositorio}/actions/runs/{execucao}"


def _varrer_orfaos(output: Path, referenciados: frozenset[str]) -> int:
    """Apaga documento de índice que o manifesto novo não aponta mais.

    É por aqui que a versão anterior desaparece (ADR 0013), e é por aqui que os
    documentos de uma reindexação do mesmo patch somem. Num CDN, arquivo com hash
    no nome poderia ficar para sempre — é imutável e ninguém paga por ele. Aqui o
    destino é um repositório Git, e cada patch deixaria um catálogo e seis fatias
    mortos no diretório de trabalho.

    A trava do ADR 0007 para passo destrutivo: isto roda **depois** de o manifesto
    novo estar escrito. Só apaga o que casa com o padrão de nome do índice e o que
    o manifesto atual não referencia — nunca o `manifest.json`, nunca subpasta.
    """
    removidos = 0
    for caminho in output.glob("*.json"):
        nome = caminho.name
        if nome == MANIFEST_KEY or nome in referenciados:
            continue
        if not (nome.startswith("catalog-") or nome.startswith("index-")):
            continue
        caminho.unlink()
        removidos += 1
        logger.info("documento órfão removido", extra={"arquivo": nome})
    return removidos


def _milhar(valor: int) -> str:
    """10583827 vira 10.583.827 — separador daqui, não o do C."""
    return f"{valor:,}".replace(",", ".")


def _por_campeao(assets: list[Asset]) -> dict[int, list[Asset]]:
    """O catálogo só precisa dos assets do campeão para escolher a miniatura."""
    agrupado: dict[int, list[Asset]] = {}
    for asset in assets:
        if asset.champion_key is not None:
            agrupado.setdefault(asset.champion_key, []).append(asset)
    return agrupado


if __name__ == "__main__":  # pragma: no cover
    app()

"""Relatório da execução — `status.json` e o resumo do job (T-12).

Não há processo monitorando nada e nem vai haver: o projeto é de uma pessoa e
alguns amigos (§11 da Spec). O que substitui monitoramento é **falhar alto**, e
falhar alto aqui significa três coisas:

1. `status.json` escrito **toda** execução, com sucesso ou com falha, ao lado do
   índice. Quem quiser saber se a indexação de hoje rodou abre uma URL, não o log
   do Actions.
2. O mesmo conteúdo como tabela no resumo do job, para não precisar nem da URL.
3. Issue automática quando falha ([`github.py`](github.py)).

O detector de dimensão inesperada mora aqui porque é o mesmo tipo de coisa: não é
erro, é a fonte mudando debaixo do projeto sem avisar. Os números vieram do S1.
"""

from __future__ import annotations

from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import (
    Asset,
    AssetType,
    DimensionDeviation,
    IndexStatus,
    StatusBytes,
    StatusCounts,
    StatusFailure,
    StatusSource,
)

from lol_assets_indexer.adapters.tarball import TarballScan
from lol_assets_indexer.limits import BudgetReport

#: Dimensões medidas no S1 para 100 % das imagens do patch 16.17.1. O que fugir
#: daqui não é rejeitado — é relatado. Um corte que muda de tamanho é notícia.
EXPECTED_DIMENSIONS: dict[AssetType, tuple[int, int]] = {
    "splash_centered": (1280, 720),
    "splash_wide": (1215, 717),
    "loading": (308, 560),
    "tile": (380, 380),
    "square": (128, 128),
}


def dimension_deviations(assets: list[Asset]) -> list[DimensionDeviation]:
    """Agrupa por (tipo, tamanho encontrado). Uma linha por desvio, não por asset."""
    contagem: dict[tuple[AssetType, int, int], tuple[int, str]] = {}
    for asset in assets:
        esperado = EXPECTED_DIMENSIONS.get(asset.type)
        if esperado is None or (asset.width, asset.height) == esperado:
            continue
        chave = (asset.type, asset.width, asset.height)
        quantos, exemplo = contagem.get(chave, (0, asset.id))
        contagem[chave] = (quantos + 1, exemplo)

    return [
        DimensionDeviation(
            type=tipo,
            expected=EXPECTED_DIMENSIONS[tipo],
            found=(largura, altura),
            assets=quantos,
            example=exemplo,
        )
        for (tipo, largura, altura), (quantos, exemplo) in sorted(
            contagem.items(), key=lambda item: -item[1][0]
        )
    ]


def build_status(
    *,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    game_version: str | None,
    run_id: str | None = None,
    failure: BaseException | None = None,
    scan: TarballScan | None = None,
    assets_by_category: dict[str, list[Asset]] | None = None,
    catalog_champions: int | None = None,
    catalog_skins: int | None = None,
    budget: BudgetReport | None = None,
) -> IndexStatus:
    """Monta o relatório com o que existir.

    Tudo é opcional de propósito: uma falha no primeiro segundo ainda precisa
    produzir um `status.json` válido, dizendo que falhou e por quê.
    """
    por_categoria = assets_by_category or {}
    todos = [asset for assets in por_categoria.values() for asset in assets]

    counts = None
    if por_categoria or catalog_champions is not None:
        por_fonte: dict[str, int] = {}
        for asset in todos:
            por_fonte[asset.source] = por_fonte.get(asset.source, 0) + 1
        counts = StatusCounts(
            assets=len(todos) or None,
            champions=catalog_champions,
            skins=catalog_skins,
            categories=len(por_categoria) or None,
            assets_by_category={c: len(a) for c, a in sorted(por_categoria.items())} or None,
            assets_by_source=dict(sorted(por_fonte.items())) or None,
        )

    return IndexStatus(
        schema_version=SCHEMA_VERSION,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=round(duration_seconds, 3),
        ok=failure is None,
        game_version=game_version,
        run_id=run_id,
        failure=(
            None
            if failure is None
            else StatusFailure(kind=type(failure).__name__, message=str(failure))
        ),
        counts=counts,
        bytes=(
            None
            if budget is None
            else StatusBytes(
                index=budget.total_raw,
                catalog_gzip=budget.catalog.compressed,
                largest_shard_gzip=max((s.compressed for s in budget.shards), default=0),
                described_assets=sum(asset.bytes for asset in todos),
            )
        ),
        source=(
            None
            if scan is None
            else StatusSource(
                files=scan.files,
                images_measured=len(scan.images),
                images_skipped=scan.skipped,
                unreadable=dict(scan.unreadable) or None,
                case_mismatches=len(scan.case_mismatches),
            )
        ),
        unexpected_dimensions=dimension_deviations(todos) or None,
    )


def _milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def render_summary(status: IndexStatus) -> str:
    """Markdown para o `$GITHUB_STEP_SUMMARY`.

    O critério do T-12 é "aparece na aba do Actions sem precisar abrir o log", e
    é por isso que a falha vem **primeiro**: quem abre a aba depois de um e-mail
    de falha quer o motivo, não a contagem de assets.
    """
    linhas: list[str] = []
    marca = "✅" if status.ok else "❌"
    versao = status.game_version or "versão não resolvida"
    linhas.append(f"## {marca} Indexação — {versao}")
    linhas.append("")

    if status.failure is not None:
        linhas.append(f"**{status.failure.kind}**")
        linhas.append("")
        linhas.append("```")
        linhas.append(status.failure.message)
        linhas.append("```")
        linhas.append("")

    linhas.append("| | |")
    linhas.append("|---|---:|")
    linhas.append(f"| Duração | {status.duration_seconds:.1f} s |")
    if status.counts is not None:
        for rotulo, valor in (
            ("Assets", status.counts.assets),
            ("Campeões", status.counts.champions),
            ("Skins", status.counts.skins),
        ):
            if valor is not None:
                linhas.append(f"| {rotulo} | {_milhar(valor)} |")
    if status.bytes is not None and status.bytes.index is not None:
        linhas.append(f"| Índice escrito | {_milhar(status.bytes.index)} B |")
        if status.bytes.catalog_gzip is not None:
            linhas.append(f"| Catálogo (gzip) | {_milhar(status.bytes.catalog_gzip)} B |")
        if status.bytes.largest_shard_gzip is not None:
            linhas.append(f"| Maior fatia (gzip) | {_milhar(status.bytes.largest_shard_gzip)} B |")
    if status.source is not None:
        if status.source.images_measured is not None:
            linhas.append(f"| Imagens medidas | {_milhar(status.source.images_measured)} |")
        if status.source.images_skipped is not None:
            linhas.append(f"| Descartadas pelo escopo | {_milhar(status.source.images_skipped)} |")
    linhas.append("")

    if status.counts is not None and status.counts.assets_by_category:
        linhas.append("| Categoria | Assets |")
        linhas.append("|---|---:|")
        for categoria, quantos in status.counts.assets_by_category.items():
            linhas.append(f"| `{categoria}` | {_milhar(quantos)} |")
        linhas.append("")

    if status.source is not None and status.source.unreadable:
        linhas.append("### Imagens ilegíveis")
        linhas.append("")
        for onde, quantos in status.source.unreadable.items():
            linhas.append(f"- `{onde}`: {quantos}")
        linhas.append("")

    if status.unexpected_dimensions:
        linhas.append("### ⚠️ Dimensões fora do esperado")
        linhas.append("")
        linhas.append("Medidas do S1 mudaram na fonte. Não é erro; é notícia.")
        linhas.append("")
        linhas.append("| Tipo | Esperado | Encontrado | Assets | Exemplo |")
        linhas.append("|---|---|---|---:|---|")
        for desvio in status.unexpected_dimensions:
            esperado = f"{desvio.expected[0]}x{desvio.expected[1]}"
            achado = f"{desvio.found[0]}x{desvio.found[1]}"
            linhas.append(
                f"| `{desvio.type}` | {esperado} | **{achado}** | {desvio.assets} "
                f"| `{desvio.example or ''}` |"
            )
        linhas.append("")

    return "\n".join(linhas).rstrip() + "\n"

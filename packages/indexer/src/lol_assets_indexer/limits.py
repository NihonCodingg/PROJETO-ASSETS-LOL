"""Guardas de tamanho do índice — RNF-03 e RNF-05.

Três limites, três motivos diferentes:

- **Catálogo ≤ 150 KiB comprimido.** É o único documento pesado da abertura do
  site. Se ele engordar, engorda para todo mundo, em toda visita.
- **Fatia `champion` ≤ 1,5 MiB comprimida.** É a maior, e é carregada no primeiro
  clique. As outras vêm depois, ao entrar na categoria.
- **Índice de uma versão ≤ 15 MiB escritos.** Desde o [ADR 0012] o índice é
  versionado no repositório: o limite aqui é do Git, não do navegador. Medido no
  patch 16.17.1: 10.583.827 bytes, com o [T-11] ainda por empilhar ~3 MB por
  versão antiga.

Os dois primeiros medem **gzip**, porque é assim que a Vercel serve. O terceiro
mede os bytes **escritos**, porque é assim que o Git guarda.

Este módulo só mede e reclama. Quem decide o que cortar quando estourar é gente,
não código — o indexador para e diz o número.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass

#: RNF-03. O documento da abertura.
CATALOG_GZIP_LIMIT = 150 * 1024
#: RNF-03. A maior fatia, carregada sob demanda.
SHARD_GZIP_LIMIT = 3 * 1024 * 1024 // 2
#: RNF-05. O que o repositório carrega por versão.
INDEX_RAW_LIMIT = 15 * 1024 * 1024


class BudgetExceededError(RuntimeError):
    """Um limite do RNF-03 ou do RNF-05 estourou. Nada foi escrito."""


@dataclass(frozen=True, slots=True)
class Measurement:
    """O tamanho de um documento nas duas formas que importam."""

    name: str
    raw: int
    compressed: int

    @property
    def ratio(self) -> float:
        return self.raw / self.compressed if self.compressed else 0.0


def measure(name: str, payload: bytes) -> Measurement:
    # mtime=0 para a medição não depender do relógio.
    return Measurement(name=name, raw=len(payload), compressed=len(gzip.compress(payload, mtime=0)))


@dataclass(frozen=True, slots=True)
class BudgetReport:
    """O que a guarda mediu. Vai para o log mesmo quando passa."""

    catalog: Measurement
    shards: tuple[Measurement, ...]
    manifest: Measurement

    @property
    def total_raw(self) -> int:
        return self.catalog.raw + self.manifest.raw + sum(s.raw for s in self.shards)

    @property
    def total_compressed(self) -> int:
        return (
            self.catalog.compressed
            + self.manifest.compressed
            + sum(s.compressed for s in self.shards)
        )

    def as_log(self) -> dict[str, int]:
        return {
            "catalogoBytes": self.catalog.raw,
            "catalogoGzip": self.catalog.compressed,
            "maiorFatiaGzip": max((s.compressed for s in self.shards), default=0),
            "indiceBytes": self.total_raw,
        }


def _kib(value: int) -> str:
    return f"{value / 1024:,.1f} KiB".replace(",", ".")


def check_budget(report: BudgetReport) -> BudgetReport:
    """Levanta `BudgetExceededError` se algum limite estourou.

    A mensagem traz o número medido, o limite e o quanto passou — sem isso quem
    lê o log do Actions não sabe se cortou de mais ou de menos.
    """
    estouros: list[str] = []

    if report.catalog.compressed > CATALOG_GZIP_LIMIT:
        estouros.append(
            f"o catálogo tem {_kib(report.catalog.compressed)} comprimidos, "
            f"{_kib(report.catalog.compressed - CATALOG_GZIP_LIMIT)} acima do limite de "
            f"{_kib(CATALOG_GZIP_LIMIT)} (RNF-03)"
        )

    for shard in report.shards:
        if shard.compressed > SHARD_GZIP_LIMIT:
            estouros.append(
                f"a fatia {shard.name!r} tem {_kib(shard.compressed)} comprimidos, "
                f"{_kib(shard.compressed - SHARD_GZIP_LIMIT)} acima do limite de "
                f"{_kib(SHARD_GZIP_LIMIT)} (RNF-03)"
            )

    if report.total_raw > INDEX_RAW_LIMIT:
        estouros.append(
            f"o índice desta versão tem {_kib(report.total_raw)} escritos, "
            f"{_kib(report.total_raw - INDEX_RAW_LIMIT)} acima do limite de "
            f"{_kib(INDEX_RAW_LIMIT)} (RNF-05)"
        )

    if estouros:
        raise BudgetExceededError(
            "orçamento do índice estourado; nada foi escrito:\n  - " + "\n  - ".join(estouros)
        )
    return report

"""T-10 — as guardas de tamanho do índice, dos dois lados de cada limite.

O que estas guardas protegem não é o disco: é a abertura do site (RNF-03) e o
repositório (RNF-05). Um índice que passa do limite não quebra nada
imediatamente — fica só um pouco pior a cada patch, até ninguém saber quando
começou. Por isso o build para.

Os payloads aqui são aleatórios de propósito: JSON de verdade comprime 8 vezes, e um
teste feito com bytes repetidos mediria o gzip, não o limite.
"""

from __future__ import annotations

import os

import pytest
from lol_assets_indexer.limits import (
    CATALOG_GZIP_LIMIT,
    INDEX_RAW_LIMIT,
    SHARD_GZIP_LIMIT,
    BudgetExceededError,
    BudgetReport,
    check_budget,
    measure,
)


def incompressivel(tamanho: int) -> bytes:
    return os.urandom(tamanho)


def relatorio(
    *,
    catalogo: int = 1024,
    fatias: dict[str, int] | None = None,
    manifesto: int = 512,
) -> BudgetReport:
    return BudgetReport(
        catalog=measure("catalog", incompressivel(catalogo)),
        shards=tuple(
            measure(nome, incompressivel(tamanho))
            for nome, tamanho in (fatias or {"champion": 4096}).items()
        ),
        manifest=measure("manifest", incompressivel(manifesto)),
    )


# --- medição ---------------------------------------------------------------------


def test_a_medicao_nao_depende_do_relogio() -> None:
    """Sem `mtime=0` o gzip carimba a hora e a medida muda entre execuções."""
    payload = b"a" * 10_000
    assert measure("x", payload).compressed == measure("x", payload).compressed


def test_mede_bruto_e_comprimido() -> None:
    medida = measure("catalog", b"{}" * 5_000)
    assert medida.raw == 10_000
    assert medida.compressed < medida.raw
    assert medida.ratio > 1


# --- catálogo: RNF-03 -------------------------------------------------------------


def test_catalogo_no_limite_passa() -> None:
    # `check_budget` devolve o relatório quando passa, para ir ao log.
    relat = relatorio(catalogo=CATALOG_GZIP_LIMIT - 4096)
    assert check_budget(relat) is relat


def test_catalogo_acima_do_limite_falha_dizendo_quanto() -> None:
    with pytest.raises(BudgetExceededError) as erro:
        check_budget(relatorio(catalogo=CATALOG_GZIP_LIMIT + 200_000))

    mensagem = str(erro.value)
    assert "catálogo" in mensagem
    assert "RNF-03" in mensagem
    assert "acima do limite" in mensagem
    assert "nada foi escrito" in mensagem


# --- fatia: RNF-03 -----------------------------------------------------------------


def test_fatia_no_limite_passa() -> None:
    check_budget(relatorio(fatias={"champion": SHARD_GZIP_LIMIT - 4096}))


def test_fatia_acima_do_limite_falha_nomeando_a_categoria() -> None:
    with pytest.raises(BudgetExceededError) as erro:
        check_budget(relatorio(fatias={"item": 4096, "champion": SHARD_GZIP_LIMIT + 500_000}))

    mensagem = str(erro.value)
    assert "'champion'" in mensagem
    assert "'item'" not in mensagem, "só a fatia que estourou devia aparecer"


# --- índice inteiro: RNF-05 ---------------------------------------------------------


def test_indice_acima_do_teto_falha() -> None:
    """O limite do RNF-05 é sobre os bytes **escritos** — é o Git que paga."""
    with pytest.raises(BudgetExceededError, match="RNF-05"):
        check_budget(
            relatorio(
                fatias={"champion": 13 * 1024 * 1024, "profile_icon": 12 * 1024 * 1024},
                catalogo=1024,
            )
        )


def test_o_teto_cobre_o_indice_completo_medido() -> None:
    """19.013.632 bytes, medidos no 16.17.1 com as duas fontes ([ADR 0015]).

    O teto de 15 MiB reprovava essa execução, e reprovar significava perder
    chroma, emote e ward. Este é o número que derrubou o teto antigo: baixar
    `INDEX_RAW_LIMIT` sem refazer a conta volta a quebrar o produto em silêncio,
    e aqui isso vira teste vermelho.
    """
    assert INDEX_RAW_LIMIT >= 19_013_632


def test_o_total_soma_catalogo_fatias_e_manifesto() -> None:
    relat = relatorio(catalogo=1000, fatias={"a": 2000, "b": 3000}, manifesto=500)
    assert relat.total_raw == 1000 + 2000 + 3000 + 500
    assert relat.total_raw < INDEX_RAW_LIMIT


def test_varios_estouros_aparecem_todos_de_uma_vez() -> None:
    """Consertar um limite e descobrir o próximo no build seguinte é caro."""
    with pytest.raises(BudgetExceededError) as erro:
        check_budget(
            relatorio(
                catalogo=CATALOG_GZIP_LIMIT + 200_000,
                fatias={"champion": SHARD_GZIP_LIMIT + 500_000},
            )
        )

    assert str(erro.value).count("acima do limite") == 2


def test_o_relatorio_vai_para_o_log_com_os_numeros_que_importam() -> None:
    linha = relatorio(fatias={"champion": 4096, "item": 2048}).as_log()
    assert set(linha) == {"catalogoBytes", "catalogoGzip", "maiorFatiaGzip", "indiceBytes"}
    assert linha["maiorFatiaGzip"] > 0

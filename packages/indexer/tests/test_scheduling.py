"""T-13 — a decisão de indexar, que é o que faz o workflow custar segundos.

O agendamento roda a cada 6 h e a Riot publica a cada duas semanas: em ~27 de
cada 28 execuções não há nada a fazer. Se essa decisão errar para o lado de
"indexar", o custo é 2,39 GB de download por engano; se errar para o lado de
"nada a fazer", o site fica velho sem ninguém perceber.
"""

from __future__ import annotations

import json
from pathlib import Path

from lol_assets_indexer.scheduling import decide, indexed_version, write_github_output

VERSAO = "16.17.1"
ANTIGA = "16.16.1"


def manifesto(destino: Path, versao: str) -> Path:
    documento = {
        "schemaVersion": "1.1.0",
        "generatedAt": "2026-09-08T00:00:00Z",
        "currentVersion": versao,
        "versions": [
            {
                "gameVersion": versao,
                "indexedAt": "2026-09-08T00:00:00Z",
                "assetsCopied": False,
                "catalog": {"url": "catalog-a.json", "champions": 173, "skins": 2118, "bytes": 10},
                "shards": [
                    {
                        "category": "champion",
                        "url": "index-champion-b.json",
                        "assets": 1,
                        "bytes": 1,
                    }
                ],
            }
        ],
    }
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "manifest.json").write_text(json.dumps(documento), encoding="utf-8")
    return destino


# --- a decisão -------------------------------------------------------------------


def test_sem_indice_publicado_indexa() -> None:
    decisao = decide(VERSAO, None)
    assert decisao.needs_index is True
    assert "não há índice" in decisao.reason


def test_versao_diferente_indexa() -> None:
    decisao = decide(VERSAO, ANTIGA)
    assert decisao.needs_index is True
    assert ANTIGA in decisao.reason and VERSAO in decisao.reason


def test_mesma_versao_nao_indexa() -> None:
    """É o caso de ~27 em 28 execuções. Custar segundos aqui é o ponto do ticket."""
    decisao = decide(VERSAO, VERSAO)
    assert decisao.needs_index is False
    assert decisao.reason == f"já indexado em {VERSAO}"


def test_fonte_mais_antiga_que_o_indice_tambem_indexa() -> None:
    """Se o ddragon voltar atrás num patch, o índice volta junto.

    A regra é "diferente", não "maior": o índice descreve o que a fonte serve
    hoje. Comparar por ordem deixaria o site apontando para arquivos que a fonte
    não tem mais.
    """
    assert decide(ANTIGA, VERSAO).needs_index is True


# --- ler o que está publicado -------------------------------------------------------


def test_le_a_versao_do_manifesto_publicado(tmp_path: Path) -> None:
    assert indexed_version(manifesto(tmp_path / "indice", VERSAO)) == VERSAO


def test_destino_inexistente_nao_tem_versao(tmp_path: Path) -> None:
    assert indexed_version(tmp_path / "nao-existe") is None


def test_manifesto_corrompido_conta_como_ausente(tmp_path: Path) -> None:
    """Melhor reindexar por causa de arquivo corrompido do que ficar parado."""
    destino = tmp_path / "indice"
    destino.mkdir()
    (destino / "manifest.json").write_text("{isto não é json", encoding="utf-8")

    assert indexed_version(destino) is None


def test_manifesto_fora_do_contrato_conta_como_ausente(tmp_path: Path) -> None:
    destino = tmp_path / "indice"
    destino.mkdir()
    (destino / "manifest.json").write_text('{"schemaVersion": "1.1.0"}', encoding="utf-8")

    assert indexed_version(destino) is None


# --- a ponte com o Actions -----------------------------------------------------------


def test_escreve_as_saidas_que_o_workflow_le(tmp_path: Path) -> None:
    saida = tmp_path / "github_output"
    write_github_output(decide(VERSAO, ANTIGA), str(saida))

    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert "needs_index=true" in linhas
    assert f"game_version={VERSAO}" in linhas
    assert f"indexed_version={ANTIGA}" in linhas


def test_a_saida_e_acrescentada_nao_sobrescrita(tmp_path: Path) -> None:
    """O `$GITHUB_OUTPUT` é compartilhado pelo step inteiro."""
    saida = tmp_path / "github_output"
    saida.write_text("outra_coisa=1\n", encoding="utf-8")
    write_github_output(decide(VERSAO, VERSAO), str(saida))

    texto = saida.read_text(encoding="utf-8")
    assert texto.startswith("outra_coisa=1")
    assert "needs_index=false" in texto


def test_sem_indice_publicado_a_saida_traz_versao_vazia(tmp_path: Path) -> None:
    saida = tmp_path / "github_output"
    write_github_output(decide(VERSAO, None), str(saida))

    assert "indexed_version=" in saida.read_text(encoding="utf-8")


def test_fora_do_actions_nao_escreve_nada(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    write_github_output(decide(VERSAO, VERSAO))
    assert not list(tmp_path.iterdir())

"""T-13 e T-38 — a decisão de indexar, que é o que faz o workflow custar segundos.

O agendamento roda a cada 6 h e a Riot publica a cada duas semanas: em ~27 de
cada 28 execuções não há nada a fazer. Se essa decisão errar para o lado de
"indexar", o custo é 2,39 GB de download por engano; se errar para o lado de
"nada a fazer", o site fica velho sem ninguém perceber.

O T-38 acrescentou o segundo jeito de ficar velho, que é o silencioso: o
indexador muda e o patch não. Foi o que aconteceu com o T-21 e o T-22, e é o
caso que estes testes existem para não deixar voltar.
"""

from __future__ import annotations

import json
from pathlib import Path

from lol_assets_indexer.scheduling import (
    GERACAO_DO_INDEXADOR,
    Publicado,
    current_generation,
    decide,
    indexed_version,
    published,
    write_github_output,
)
from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import Generation

VERSAO = "16.17.1"
ANTIGA = "16.16.1"

#: O que uma execução completa emite hoje.
CATEGORIAS = ("champion", "emote", "item", "map", "profile_icon", "rune", "summoner_spell", "ward")
ATUAL = current_generation(CATEGORIAS)


def publicado(
    versao: str = VERSAO,
    *,
    schema: str = SCHEMA_VERSION,
    geracao: Generation | None = ATUAL,
) -> Publicado:
    return Publicado(game_version=versao, schema_version=schema, generation=geracao)


def manifesto(destino: Path, versao: str, *, com_assinatura: bool = True) -> Path:
    documento: dict[str, object] = {
        "schemaVersion": SCHEMA_VERSION,
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
    if com_assinatura:
        documento["generation"] = {
            "indexer": GERACAO_DO_INDEXADOR,
            "categories": list(CATEGORIAS),
        }
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "manifest.json").write_text(json.dumps(documento), encoding="utf-8")
    return destino


# --- a versão do jogo (T-13) -------------------------------------------------------


def test_sem_indice_publicado_indexa() -> None:
    decisao = decide(VERSAO, None, generation=ATUAL)
    assert decisao.needs_index is True
    assert "não há índice" in decisao.reason


def test_versao_diferente_indexa() -> None:
    decisao = decide(VERSAO, publicado(ANTIGA), generation=ATUAL)
    assert decisao.needs_index is True
    assert ANTIGA in decisao.reason and VERSAO in decisao.reason


def test_mesma_versao_e_mesma_assinatura_nao_indexa() -> None:
    """É o caso de ~27 em 28 execuções. Custar segundos aqui é o ponto do ticket."""
    decisao = decide(VERSAO, publicado(), generation=ATUAL)
    assert decisao.needs_index is False
    assert decisao.reason == f"já indexado em {VERSAO}"


def test_fonte_mais_antiga_que_o_indice_tambem_indexa() -> None:
    """Se o ddragon voltar atrás num patch, o índice volta junto.

    A regra é "diferente", não "maior": o índice descreve o que a fonte serve
    hoje. Comparar por ordem deixaria o site apontando para arquivos que a fonte
    não tem mais.
    """
    assert decide(ANTIGA, publicado(VERSAO), generation=ATUAL).needs_index is True


# --- a assinatura de geração (T-38) ---------------------------------------------------


def test_indexador_novo_reindexa_no_mesmo_patch() -> None:
    """O caso do T-21: etiquetas novas, patch igual, índice publicado sem elas."""
    antigo = Generation(indexer=GERACAO_DO_INDEXADOR - 1, categories=list(CATEGORIAS))
    decisao = decide(VERSAO, publicado(geracao=antigo), generation=ATUAL)

    assert decisao.needs_index is True
    assert "assinatura" in decisao.reason
    assert str(GERACAO_DO_INDEXADOR) in decisao.reason


def test_categoria_nova_reindexa_no_mesmo_patch() -> None:
    """O caso do T-22: emote e ward passaram a existir, e o patch não mudou."""
    sem_emote = Generation(
        indexer=GERACAO_DO_INDEXADOR,
        categories=[c for c in CATEGORIAS if c not in {"emote", "ward"}],
    )
    decisao = decide(VERSAO, publicado(geracao=sem_emote), generation=ATUAL)

    assert decisao.needs_index is True
    assert "entraram emote, ward" in decisao.reason


def test_categoria_que_sumiu_tambem_reindexa() -> None:
    """Fatia órfã no destino é pior que fatia faltando: ela ainda é servida."""
    com_extra = Generation(indexer=GERACAO_DO_INDEXADOR, categories=[*CATEGORIAS, "rank"])
    decisao = decide(VERSAO, publicado(geracao=com_extra), generation=ATUAL)

    assert decisao.needs_index is True
    assert "saíram rank" in decisao.reason


def test_ordem_das_categorias_nao_conta() -> None:
    embaralhada = Generation(indexer=GERACAO_DO_INDEXADOR, categories=list(reversed(CATEGORIAS)))
    assert decide(VERSAO, publicado(geracao=embaralhada), generation=ATUAL).needs_index is False


def test_indice_sem_assinatura_reindexa_sem_quebrar() -> None:
    """O índice publicado hoje foi gerado antes do T-38 e não tem o campo."""
    decisao = decide(VERSAO, publicado(geracao=None), generation=ATUAL)

    assert decisao.needs_index is True
    assert "sem assinatura" in decisao.reason


def test_contrato_diferente_reindexa() -> None:
    decisao = decide(VERSAO, publicado(schema="1.1.0"), generation=ATUAL)

    assert decisao.needs_index is True
    assert "contrato" in decisao.reason and "1.1.0" in decisao.reason


def test_a_versao_do_jogo_vence_a_assinatura_no_motivo() -> None:
    """Patch novo **e** indexador novo: o motivo fala do patch, que é o que manda."""
    antigo = Generation(indexer=1, categories=["champion"])
    decisao = decide(VERSAO, publicado(ANTIGA, geracao=antigo), generation=ATUAL)

    assert "assinatura" not in decisao.reason
    assert ANTIGA in decisao.reason


def test_a_assinatura_atual_e_ordenada_e_sem_repetido() -> None:
    assinatura = current_generation(["ward", "champion", "ward"])
    assert assinatura.categories == ["champion", "ward"]
    assert assinatura.indexer == GERACAO_DO_INDEXADOR


# --- ler o que está publicado -------------------------------------------------------


def test_le_a_versao_do_manifesto_publicado(tmp_path: Path) -> None:
    assert indexed_version(manifesto(tmp_path / "indice", VERSAO)) == VERSAO


def test_le_a_assinatura_do_manifesto_publicado(tmp_path: Path) -> None:
    atual = published(manifesto(tmp_path / "indice", VERSAO))
    assert atual is not None
    assert atual.schema_version == SCHEMA_VERSION
    assert atual.generation is not None
    assert atual.generation.indexer == GERACAO_DO_INDEXADOR


def test_manifesto_antigo_sem_assinatura_continua_legivel(tmp_path: Path) -> None:
    atual = published(manifesto(tmp_path / "indice", VERSAO, com_assinatura=False))
    assert atual is not None
    assert atual.generation is None


def test_destino_inexistente_nao_tem_versao(tmp_path: Path) -> None:
    assert indexed_version(tmp_path / "nao-existe") is None
    assert published(tmp_path / "nao-existe") is None


def test_manifesto_corrompido_conta_como_ausente(tmp_path: Path) -> None:
    """Melhor reindexar por causa de arquivo corrompido do que ficar parado."""
    destino = tmp_path / "indice"
    destino.mkdir()
    (destino / "manifest.json").write_text("{isto não é json", encoding="utf-8")

    assert indexed_version(destino) is None


def test_manifesto_fora_do_contrato_conta_como_ausente(tmp_path: Path) -> None:
    destino = tmp_path / "indice"
    destino.mkdir()
    (destino / "manifest.json").write_text('{"schemaVersion": "1.2.0"}', encoding="utf-8")

    assert indexed_version(destino) is None


# --- a ponte com o Actions -----------------------------------------------------------


def test_escreve_as_saidas_que_o_workflow_le(tmp_path: Path) -> None:
    saida = tmp_path / "github_output"
    write_github_output(decide(VERSAO, publicado(ANTIGA), generation=ATUAL), str(saida))

    linhas = saida.read_text(encoding="utf-8").splitlines()
    assert "needs_index=true" in linhas
    assert f"game_version={VERSAO}" in linhas
    assert f"indexed_version={ANTIGA}" in linhas


def test_a_saida_e_acrescentada_nao_sobrescrita(tmp_path: Path) -> None:
    """O `$GITHUB_OUTPUT` é compartilhado pelo step inteiro."""
    saida = tmp_path / "github_output"
    saida.write_text("outra_coisa=1\n", encoding="utf-8")
    write_github_output(decide(VERSAO, publicado(), generation=ATUAL), str(saida))

    texto = saida.read_text(encoding="utf-8")
    assert texto.startswith("outra_coisa=1")
    assert "needs_index=false" in texto


def test_sem_indice_publicado_a_saida_traz_versao_vazia(tmp_path: Path) -> None:
    saida = tmp_path / "github_output"
    write_github_output(decide(VERSAO, None, generation=ATUAL), str(saida))

    assert "indexed_version=" in saida.read_text(encoding="utf-8")


def test_fora_do_actions_nao_escreve_nada(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    write_github_output(decide(VERSAO, publicado(), generation=ATUAL))
    assert not list(tmp_path.iterdir())

"""A decisão de indexar ou não, e como ela chega ao Actions (T-13, T-38).

O workflow roda a cada 6 horas; a Riot publica um patch a cada duas semanas. Na
esmagadora maioria das execuções não há nada a fazer, e "nada a fazer" precisa
custar segundos, não os ~40 minutos de baixar 2,39 GB.

**Duas coisas fazem reindexar, não uma** (T-38). A versão do jogo é a óbvia. A
outra é o indexador mudar: o T-21 acrescentou etiquetas de filtro e o T-22
acrescentou emotes e wards, e nenhum dos dois teria chegado ao índice publicado
até a Riot lançar patch. O índice ficaria velho **de código** parecendo novo de
versão, e o único jeito de descobrir seria alguém reparar que o filtro não
filtra.

Este módulo é a parte testável dessa decisão. O YAML só pergunta e obedece.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from lol_assets_schema import SCHEMA_VERSION
from lol_assets_schema.models import Generation, IndexManifest

logger = logging.getLogger(__name__)

#: Sobe **à mão** quando um construtor passa a produzir registro diferente.
#:
#: Não é hash do código-fonte de propósito: hash reindexaria 2,39 GB a cada
#: refatoração e a cada bump de dependência. O preço de ser manual é lembrar — e
#: o histórico abaixo existe para que "por que este número é 3?" tenha resposta
#: sem `git log`.
#:
#: 1. T-09 — a primeira indexação do patch inteiro.
#: 2. T-21 — etiquetas de filtro nas categorias não-campeão.
#: 3. T-22 — emotes e ward skins pelo cdragon, e a fusão das duas fontes.
GERACAO_DO_INDEXADOR = 3


@dataclass(frozen=True, slots=True)
class Decision:
    """O que o workflow precisa saber para decidir se continua."""

    needs_index: bool
    latest: str
    indexed: str | None
    reason: str

    def as_github_output(self) -> str:
        return (
            f"needs_index={'true' if self.needs_index else 'false'}\n"
            f"game_version={self.latest}\n"
            f"indexed_version={self.indexed or ''}\n"
        )


@dataclass(frozen=True, slots=True)
class Publicado:
    """O que o índice publicado diz sobre si mesmo."""

    game_version: str
    schema_version: str
    #: `None` nos índices gerados antes do T-38.
    generation: Generation | None


def current_generation(categories: Iterable[str]) -> Generation:
    """A assinatura desta execução. `categories` é o que foi realmente emitido."""
    return Generation(indexer=GERACAO_DO_INDEXADOR, categories=sorted(set(categories)))


def published(output: Path) -> Publicado | None:
    """O que já está publicado no destino, ou `None`.

    Manifesto ilegível conta como ausente: melhor reindexar por causa de um
    arquivo corrompido do que ficar parado achando que está tudo certo.
    """
    manifesto = output / "manifest.json"
    if not manifesto.is_file():
        return None
    try:
        documento = IndexManifest.model_validate(json.loads(manifesto.read_text(encoding="utf-8")))
    except (ValueError, OSError) as erro:
        logger.info(
            "manifesto ilegível no destino; tratando como ausente",
            extra={"kind": type(erro).__name__},
        )
        return None
    return Publicado(
        game_version=documento.current_version,
        schema_version=documento.schema_version,
        generation=documento.generation,
    )


def indexed_version(output: Path) -> str | None:
    """Só a versão publicada, para quem só quer o número."""
    atual = published(output)
    return atual.game_version if atual else None


def _mudanca_de_categorias(atual: Generation, publicada: Generation) -> str | None:
    """O que entrou e o que saiu, ou `None` se o conjunto é o mesmo."""
    novas = sorted(set(atual.categories) - set(publicada.categories))
    sumidas = sorted(set(publicada.categories) - set(atual.categories))
    partes = []
    if novas:
        partes.append("entraram " + ", ".join(novas))
    if sumidas:
        partes.append("saíram " + ", ".join(sumidas))
    return "; ".join(partes) if partes else None


def decide(
    latest: str,
    indexed: Publicado | None,
    *,
    generation: Generation,
    schema_version: str = SCHEMA_VERSION,
) -> Decision:
    """Indexa quando a versão do jogo, o contrato **ou** a assinatura diferem.

    A versão do jogo é comparada por **diferença**, não por ordem: se o ddragon
    voltar atrás num patch, o índice tem que voltar junto — ele descreve o que a
    fonte serve hoje, não o que ela já serviu. Comparar por ordem faria o site
    continuar apontando para arquivos que a fonte não tem mais.

    O motivo diz **qual** dos três mudou. É o que alguém quer saber ao abrir o
    log de uma execução que baixou 2,39 GB às três da manhã.
    """
    atual = generation
    if indexed is None:
        return Decision(True, latest, None, "não há índice publicado")

    versao = indexed.game_version
    if versao != latest:
        return Decision(True, latest, versao, f"índice em {versao}, fonte em {latest}")

    if indexed.schema_version != schema_version:
        return Decision(
            True,
            latest,
            versao,
            f"contrato do índice mudou de {indexed.schema_version} para {schema_version}",
        )

    publicada = indexed.generation
    if publicada is None:
        return Decision(True, latest, versao, "índice publicado sem assinatura de geração")

    if publicada.indexer != atual.indexer:
        return Decision(
            True,
            latest,
            versao,
            f"assinatura: o indexador foi de {publicada.indexer} para {atual.indexer}",
        )

    mudanca = _mudanca_de_categorias(atual, publicada)
    if mudanca is not None:
        return Decision(True, latest, versao, f"assinatura: categorias mudaram — {mudanca}")

    return Decision(False, latest, versao, f"já indexado em {latest}")


def write_github_output(decision: Decision, path: str | None = None) -> None:
    """Escreve no `$GITHUB_OUTPUT`. Fora do Actions, não faz nada."""
    destino = path or os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    with Path(destino).open("a", encoding="utf-8") as arquivo:
        arquivo.write(decision.as_github_output())

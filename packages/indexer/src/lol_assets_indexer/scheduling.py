"""A decisão de indexar ou não, e como ela chega ao Actions (T-13).

O workflow roda a cada 6 horas; a Riot publica um patch a cada duas semanas. Na
esmagadora maioria das execuções não há nada a fazer, e "nada a fazer" precisa
custar segundos, não os ~15 minutos de baixar 2,39 GB.

Este módulo é a parte testável dessa decisão. O YAML só pergunta e obedece.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from lol_assets_schema.models import IndexManifest

logger = logging.getLogger(__name__)


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


def indexed_version(output: Path) -> str | None:
    """A versão que já está publicada no destino, ou `None`.

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
    return documento.current_version


def decide(latest: str, indexed: str | None) -> Decision:
    """Indexa quando a versão publicada é **diferente** da mais recente.

    Diferente, não "menor": se o ddragon voltar atrás num patch, o índice tem que
    voltar junto — ele descreve o que a fonte serve hoje, não o que ela já serviu.
    Comparar por ordem faria o site continuar apontando para arquivos que a fonte
    não tem mais.
    """
    if indexed is None:
        return Decision(True, latest, None, "não há índice publicado")
    if indexed != latest:
        return Decision(True, latest, indexed, f"índice em {indexed}, fonte em {latest}")
    return Decision(False, latest, indexed, f"já indexado em {latest}")


def write_github_output(decision: Decision, path: str | None = None) -> None:
    """Escreve no `$GITHUB_OUTPUT`. Fora do Actions, não faz nada."""
    destino = path or os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    with Path(destino).open("a", encoding="utf-8") as arquivo:
        arquivo.write(decision.as_github_output())

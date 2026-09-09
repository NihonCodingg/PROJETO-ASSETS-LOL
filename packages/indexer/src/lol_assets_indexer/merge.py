"""Fusão de fontes — juntar ddragon e cdragon sem trocar corte nem duplicar.

A regra do §8 da Spec: para cada `(identidade, tipo canônico)`, vence a **maior
resolução**; empate favorece o **ddragon**, que é a fonte oficial.

Duas coisas que parecem detalhe e não são:

**Tipos diferentes nunca competem.** `splash_centered` e `splash_wide` são cortes
distintos da mesma skin, com dimensões diferentes — se entrassem na mesma disputa,
o de 1280x720 "venceria" o de 1215x717 e o corte aberto sumiria do catálogo. A
chave da fusão inclui o tipo justamente por isso — [ADR 0002].

**Empate é a regra, não a exceção.** O S2 mediu: square, splash, loading e tile
empatam entre as duas fontes. O cdragon entra por **cobertura** — chroma e
`loading_vintage` —, não por resolução. Um desempate que não favorecesse o
ddragon trocaria 100 % dos assets de campeão de fonte sem ganhar um pixel.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field

from lol_assets_schema.models import Asset, AssetSource

logger = logging.getLogger(__name__)

#: Quem ganha o empate. Ordem de preferência, da melhor para a pior.
SOURCE_PRIORITY: tuple[AssetSource, ...] = ("ddragon", "cdragon", "riot_static", "wiki")

_PRIORIDADE = {fonte: posicao for posicao, fonte in enumerate(SOURCE_PRIORITY)}


def merge_key(asset: Asset) -> tuple[str, str]:
    """`(identidade, tipo)` — a chave do §8 da Spec.

    A identidade é o `id`, que já embute o tipo e a chave natural
    (`splash_centered:24004`). Manter o tipo explícito na chave é redundante de
    propósito: é ele que impede os dois cortes de splash de competirem, e essa
    garantia não pode depender do formato de outro campo.
    """
    return (asset.id, asset.type)


def _pixels(asset: Asset) -> int:
    return asset.width * asset.height


def _prioridade(asset: Asset) -> int:
    return _PRIORIDADE.get(asset.source, len(SOURCE_PRIORITY))


def wins(candidato: Asset, atual: Asset) -> bool:
    """`True` se o candidato deve substituir o que já está lá.

    Maior resolução ganha. Empate de resolução vai para a fonte de maior
    prioridade. Empate dos dois mantém quem chegou primeiro — o resultado não
    pode depender da ordem em que as fontes foram lidas.
    """
    if _pixels(candidato) != _pixels(atual):
        return _pixels(candidato) > _pixels(atual)
    return _prioridade(candidato) < _prioridade(atual)


@dataclass
class MergeReport:
    """O que a fusão fez. Vai para o `status.json` (T-12)."""

    #: Quantos registros venceram, por fonte.
    winners_by_source: dict[str, int] = field(default_factory=dict)
    #: Quantos foram descartados por perder a disputa, por fonte.
    losers_by_source: dict[str, int] = field(default_factory=dict)
    #: Disputas em que as duas fontes tinham a mesma resolução.
    ties: int = 0
    #: Disputas decididas por resolução.
    resolution_wins: int = 0
    #: Registros que só existem numa fonte — o valor real do cdragon.
    exclusive_by_source: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.winners_by_source.values())

    @property
    def contested(self) -> int:
        return sum(self.losers_by_source.values())

    def as_log(self) -> dict[str, int]:
        return {
            "fusaoTotal": self.total,
            "fusaoDisputados": self.contested,
            "fusaoEmpates": self.ties,
            "fusaoPorResolucao": self.resolution_wins,
        }


def merge_assets(*sources: Iterable[Asset]) -> tuple[list[Asset], MergeReport]:
    """Funde as fontes na ordem em que vierem e devolve o relatório.

    A ordem dos argumentos **não** decide nada: quem decide é `wins`. Ela existe
    só para o relatório saber quantos vieram de onde.
    """
    vencedores: dict[tuple[str, str], Asset] = {}
    disputas: dict[tuple[str, str], int] = {}
    relatorio = MergeReport()

    for fonte in sources:
        for asset in fonte:
            chave = merge_key(asset)
            atual = vencedores.get(chave)
            if atual is None:
                vencedores[chave] = asset
                disputas[chave] = 1
                continue

            disputas[chave] += 1
            if _pixels(asset) == _pixels(atual):
                relatorio.ties += 1
            else:
                relatorio.resolution_wins += 1

            perdedor = atual if wins(asset, atual) else asset
            if perdedor is atual:
                vencedores[chave] = asset
            relatorio.losers_by_source[perdedor.source] = (
                relatorio.losers_by_source.get(perdedor.source, 0) + 1
            )

    for chave, vencedor in vencedores.items():
        relatorio.winners_by_source[vencedor.source] = (
            relatorio.winners_by_source.get(vencedor.source, 0) + 1
        )
        if disputas[chave] == 1:
            relatorio.exclusive_by_source[vencedor.source] = (
                relatorio.exclusive_by_source.get(vencedor.source, 0) + 1
            )

    logger.info("fontes fundidas", extra=relatorio.as_log())
    # Ordem estável: sem isto, o hash do documento mudaria entre execuções
    # idênticas e o índice pareceria novo a cada patch.
    return sorted(vencedores.values(), key=lambda a: (a.type, a.id)), relatorio

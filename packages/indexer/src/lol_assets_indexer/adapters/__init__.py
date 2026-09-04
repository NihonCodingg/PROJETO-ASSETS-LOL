"""Adaptadores de fonte.

Cada adaptador produz registros no mesmo contrato (`lol_assets_schema.models`).
Nenhum re-encoda imagem — o ADR 0001 é garantido por teste de varredura sobre os
arquivos deste pacote.
"""

__all__ = ["ddragon"]

from lol_assets_indexer.adapters import ddragon

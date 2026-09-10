"""Leitura do índice do disco, com cache que sabe quando expirou.

O índice muda quando o workflow do T-13 commita um patch novo — no máximo a cada
seis horas, e na prática a cada duas semanas. Reler 19 MB de JSON a cada
requisição seria absurdo; nunca reler seria pior, porque a API serviria o patch
de ontem sem sintoma nenhum.

O meio-termo é o `mtime`: barato de checar, e muda exatamente quando o arquivo
muda. Um `TTL` teria a janela de erro embutida no número.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from lol_assets_schema.models import Asset, IndexManifest, IndexShard


class IndiceIndisponivelError(RuntimeError):
    """Não há índice legível no diretório configurado."""


@dataclass
class Indice:
    """O índice publicado, lido do disco sob demanda."""

    diretorio: Path
    _manifesto: IndexManifest | None = field(default=None, init=False, repr=False)
    _mtime: float | None = field(default=None, init=False, repr=False)
    _fatias: dict[str, IndexShard] = field(default_factory=dict, init=False, repr=False)

    @property
    def _arquivo(self) -> Path:
        return self.diretorio / "manifest.json"

    def manifesto(self) -> IndexManifest:
        try:
            mtime = self._arquivo.stat().st_mtime
        except OSError as erro:
            raise IndiceIndisponivelError(
                f"não há manifest.json em {self.diretorio}; rode `lol-assets-indexer index`"
            ) from erro

        if self._manifesto is None or mtime != self._mtime:
            try:
                documento = json.loads(self._arquivo.read_text(encoding="utf-8"))
                self._manifesto = IndexManifest.model_validate(documento)
            except (ValueError, OSError) as erro:
                raise IndiceIndisponivelError(f"manifest.json ilegível: {erro}") from erro
            # O manifesto mudou: as fatias em memória descrevem o patch anterior.
            self._fatias.clear()
            self._mtime = mtime
        return self._manifesto

    def versao_atual(self) -> str:
        return self.manifesto().current_version

    def fatia(self, game_version: str, category: str) -> IndexShard:
        manifesto = self.manifesto()
        versao = next(
            (v for v in manifesto.versions if v.game_version == game_version),
            None,
        )
        if versao is None:
            raise KeyError(f"a versão {game_version} não está no manifesto")

        referencia = next((s for s in versao.shards if s.category == category), None)
        if referencia is None:
            raise KeyError(f"a versão {game_version} não tem a fatia {category}")

        chave = f"{game_version}/{category}"
        em_memoria = self._fatias.get(chave)
        if em_memoria is not None:
            return em_memoria

        caminho = self.diretorio / referencia.url
        try:
            documento = json.loads(caminho.read_text(encoding="utf-8"))
        except (ValueError, OSError) as erro:
            raise IndiceIndisponivelError(f"fatia ilegível em {caminho}: {erro}") from erro

        fatia = IndexShard.model_validate(documento)
        self._fatias[chave] = fatia
        return fatia

    def assets_por_id(self, game_version: str, ids: list[str]) -> list[Asset]:
        """Acha assets por id, varrendo só as fatias que o manifesto declara.

        A ordem de saída é a dos `ids` pedidos, não a do índice: quem pediu
        escolheu a ordem, e um zip que reordena confunde na hora de conferir.
        """
        manifesto = self.manifesto()
        versao = next((v for v in manifesto.versions if v.game_version == game_version), None)
        if versao is None:
            raise KeyError(f"a versão {game_version} não está no manifesto")

        procurados = set(ids)
        achados: dict[str, Asset] = {}
        for referencia in versao.shards:
            if len(achados) == len(procurados):
                break
            for asset in self.fatia(game_version, referencia.category).assets:
                if asset.id in procurados:
                    achados[asset.id] = asset
        return [achados[asset_id] for asset_id in ids if asset_id in achados]

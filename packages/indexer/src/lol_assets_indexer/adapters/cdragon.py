"""Adaptador do Community Dragon — o que o ddragon não tem.

O cdragon **não** acrescenta resolução: o S2 mediu empate em square, splash,
loading e tile. Ele acrescenta **cobertura** — chromas e `loading_vintage`, que
não existem no tarball do ddragon.

**Todo caminho vem do JSON. Nenhum é montado.** O S2 testou os três caminhos que
a §B.2.3 do KICKOFF sugeria montar à mão: **404 em 162 de 162 tentativas**. Os
declarados em `v1/champions/{key}.json`: **397 de 397 responderam 200**. É por
isso que este módulo lê caminho e nunca escreve caminho, e é por isso que existe
um teste varrendo o fonte atrás de f-string com extensão de imagem.

Caminho declarado que não começa com `/lol-game-data/assets/` é **registrado como
não mapeável**, não descartado em silêncio: é assim que a próxima mudança de
formato do cliente aparece no `status.json` em vez de virar asset faltando.
"""

from __future__ import annotations

import logging
from collections.abc import Collection
from dataclasses import dataclass, field
from typing import Any

from lol_assets_schema.models import Asset, AssetType, LocalizedName

from lol_assets_indexer.http import SourceClient
from lol_assets_indexer.imaging import UnsupportedImageFormatError, measure
from lol_assets_indexer.naming import asset_id, champion_file_name

logger = logging.getLogger(__name__)

#: Prefixo dos caminhos de asset nos JSONs do cliente. §B.2.1 do KICKOFF.
ASSET_PREFIX = "/lol-game-data/assets/"
#: Onde o cdragon serve o que está sob aquele prefixo.
GAME_DATA_ROOT = "plugins/rcp-be-lol-game-data/global/default"


def champion_json_url(base: str, champion_key: int) -> str:
    """A ficha do campeão. É daqui que sai todo o resto."""
    return f"{base.rstrip('/')}/latest/{GAME_DATA_ROOT}/v1/champions/{champion_key}.json"


def asset_url(base: str, declared: str) -> str | None:
    """`/lol-game-data/assets/<Path>` vira URL. `None` se o prefixo não casar.

    A regra é do KICKOFF §B.2.1, e o minúsculo importa: o cliente declara
    `ASSETS/Characters/Jax/...` e o cdragon serve `assets/characters/jax/...`.
    """
    if not declared.startswith(ASSET_PREFIX):
        return None
    relativo = declared[len(ASSET_PREFIX) :].lower()
    return f"{base.rstrip('/')}/latest/{GAME_DATA_ROOT}/{relativo}"


@dataclass(frozen=True, slots=True)
class DeclaredAsset:
    """Um caminho que o JSON declarou, já classificado."""

    json_path: str
    declared: str
    type: AssetType
    #: `skinId` a que o asset pertence. Ausente nos que são do campeão.
    skin: int | None = None
    parent_skin_num: int | None = None
    label: str | None = None


@dataclass
class ChampionPaths:
    """O que a ficha de um campeão declara, e o que ela declarou e não dá para mapear."""

    champion_key: int
    champion_id: str
    names: LocalizedName
    assets: list[DeclaredAsset] = field(default_factory=list)
    #: `caminho no JSON -> valor declarado`, para os que não casam o prefixo.
    unmappable: dict[str, str] = field(default_factory=dict)


def _skin_num(skin_identifier: int, champion_key: int) -> int:
    return skin_identifier - champion_key * 1000


def _varrer_nao_mapeaveis(no: Any, achados: dict[str, str], caminho: str = "") -> None:
    """Percorre a ficha inteira atrás de campo `*Path` que não dá para mapear.

    Não basta olhar os campos que este adaptador usa: o objetivo é que **uma
    mudança de formato do cliente apareça**, e ela apareceria justamente num
    campo que ninguém está lendo ainda. `abilityVideoImagePath` é o exemplo vivo
    — o S2 testou os caminhos dele e levou 404.

    URL absoluta não conta: ela não precisa de mapeamento nenhum.
    """
    if isinstance(no, dict):
        for chave, valor in no.items():
            adiante = f"{caminho}.{chave}" if caminho else str(chave)
            if (
                isinstance(valor, str)
                and str(chave).endswith("Path")
                and valor
                and not valor.startswith(ASSET_PREFIX)
                and not valor.startswith("http")
            ):
                achados[adiante] = valor
            else:
                _varrer_nao_mapeaveis(valor, achados, adiante)
    elif isinstance(no, list):
        for i, item in enumerate(no):
            _varrer_nao_mapeaveis(item, achados, f"{caminho}[{i}]")


def declared_assets(document: dict[str, Any]) -> ChampionPaths:
    """Percorre a ficha e classifica cada caminho declarado.

    Só os campos que a v1 usa. Voz, vídeo e áudio (`stingerSfxPath`,
    `chooseVoPath`, `banVoPath`, `splashVideoPath`) são declarados e ignorados de
    propósito — não são asset visual, e o §1.2 da Spec os deixa fora.
    """
    champion_key = int(document["id"])
    alias = str(document.get("alias") or document.get("name") or champion_key)
    nome = LocalizedName(pt_BR=str(document.get("name") or alias))
    paths = ChampionPaths(champion_key=champion_key, champion_id=alias, names=nome)

    _varrer_nao_mapeaveis(document, paths.unmappable)

    def registrar(
        json_path: str,
        declarado: Any,
        tipo: AssetType,
        *,
        skin: int | None = None,
        parent: int | None = None,
        label: str | None = None,
    ) -> None:
        if not isinstance(declarado, str) or not declarado:
            return
        if not declarado.startswith(ASSET_PREFIX):
            paths.unmappable[json_path] = declarado
            return
        paths.assets.append(
            DeclaredAsset(
                json_path=json_path,
                declared=declarado,
                type=tipo,
                skin=skin,
                parent_skin_num=parent,
                label=label,
            )
        )

    registrar("squarePortraitPath", document.get("squarePortraitPath"), "square")

    passiva = document.get("passive") or {}
    registrar("passive.abilityIconPath", passiva.get("abilityIconPath"), "passive_icon")
    for i, feitico in enumerate(document.get("spells") or []):
        registrar(f"spells[{i}].abilityIconPath", feitico.get("abilityIconPath"), "ability_icon")

    for i, skin in enumerate(document.get("skins") or []):
        identificador = int(skin["id"])
        num = _skin_num(identificador, champion_key)
        rotulo = str(skin.get("name") or "")
        base = f"skins[{i}]"
        # ADR 0002: no cdragon, `splashPath` é o corte CENTRADO (1280x720) e
        # `uncenteredSplashPath` é o aberto (1215x717). Não inverta.
        registrar(
            f"{base}.splashPath",
            skin.get("splashPath"),
            "splash_centered",
            skin=identificador,
            label=rotulo,
        )
        registrar(
            f"{base}.uncenteredSplashPath",
            skin.get("uncenteredSplashPath"),
            "splash_wide",
            skin=identificador,
            label=rotulo,
        )
        registrar(
            f"{base}.tilePath", skin.get("tilePath"), "tile", skin=identificador, label=rotulo
        )
        registrar(
            f"{base}.loadScreenPath",
            skin.get("loadScreenPath"),
            "loading",
            skin=identificador,
            label=rotulo,
        )
        registrar(
            f"{base}.loadScreenVintagePath",
            skin.get("loadScreenVintagePath"),
            "loading_vintage",
            skin=identificador,
            label=rotulo,
        )
        # O `chromaPath` da própria skin é a amostra "cor original", que o

        registrar(
            f"{base}.chromaPath",
            skin.get("chromaPath"),
            "chroma",
            skin=identificador,
            parent=num,
            label=rotulo,
        )

        for j, chroma in enumerate(skin.get("chromas") or []):
            chroma_id = int(chroma["id"])
            # Medido em 26 de 26 chromas do Jax: `tilePath` e `chromaPath` são o
            # MESMO arquivo. Registrar os dois duplicaria o índice.
            registrar(
                f"{base}.chromas[{j}].chromaPath",
                chroma.get("chromaPath"),
                "chroma",
                skin=chroma_id,
                parent=num,
                label=str(chroma.get("name") or ""),
            )

    return paths


async def fetch_champion_paths(client: SourceClient, champion_key: int) -> ChampionPaths:
    documento = await client.get_json(
        champion_json_url(client.settings.cdragon_base_url, champion_key)
    )
    return declared_assets(documento)


async def fetch_champion_assets(
    client: SourceClient,
    champion_key: int,
    *,
    only: Collection[AssetType] | None = None,
) -> tuple[list[Asset], dict[str, str]]:
    """Baixa, mede e monta os registros. Devolve também o que não deu para mapear.

    `only` limita os tipos buscados. Existe por medição, não por gosto: o cdragon
    responde a **2,8 assets/s** com a concorrência de 4 da regra 4 do CLAUDE.md,
    e os 173 campeões inteiros custariam ~2 horas por patch. Buscar só o que
    falta é o que cabe na janela do workflow.
    """
    paths = await fetch_champion_paths(client, champion_key)
    base = client.settings.cdragon_base_url
    assets: list[Asset] = []

    for declarado in paths.assets:
        if only is not None and declarado.type not in only:
            continue
        url = asset_url(base, declarado.declared)
        if url is None:  # pragma: no cover - `declared_assets` já filtrou
            paths.unmappable[declarado.json_path] = declarado.declared
            continue
        try:
            medida = measure(await client.get_bytes(url))
        except (UnsupportedImageFormatError, OSError, ValueError) as erro:
            logger.info(
                "asset do cdragon ilegível",
                extra={"url": url, "kind": type(erro).__name__},
            )
            continue

        num = None if declarado.skin is None else _skin_num(declarado.skin, paths.champion_key)
        natural = declarado.skin if declarado.skin is not None else paths.champion_key
        assets.append(
            Asset(
                id=asset_id(declarado.type, natural),
                type=declarado.type,
                category="champion",
                champion_key=paths.champion_key,
                champion_id=paths.champion_id,
                skin_id=declarado.skin,
                skin_num=num,
                parent_skin_num=declarado.parent_skin_num,
                is_base_skin=(num == 0) if num is not None else None,
                names=LocalizedName(pt_BR=declarado.label or paths.names.pt_BR),
                source="cdragon",
                source_url=url,
                file_name=champion_file_name(
                    paths.champion_id, declarado.type, medida.format, skin_num=num
                ),
                width=medida.width,
                height=medida.height,
                format=medida.format,
                has_alpha=medida.has_alpha,
                bytes=medida.bytes,
                sha256=medida.sha256,
            )
        )

    if paths.unmappable:
        logger.info(
            "caminhos declarados que não dá para mapear",
            extra={"quantos": len(paths.unmappable), "campeao": paths.champion_id},
        )
    return assets, paths.unmappable


__all__ = [
    "ASSET_PREFIX",
    "GAME_DATA_ROOT",
    "ChampionPaths",
    "DeclaredAsset",
    "asset_url",
    "champion_json_url",
    "declared_assets",
    "fetch_champion_assets",
    "fetch_champion_paths",
]

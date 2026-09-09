"""Montagem dos registros do índice a partir da varredura do tarball.

Cada categoria tem um construtor pequeno que junta a medição (do `tarball.py`)
com o metadado (dos JSONs de `data/`). Nenhum deles copia bytes — desde o
[ADR 0012] o `storageKey` fica **sempre ausente** e o front usa a `sourceUrl`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from lol_assets_schema.models import Asset, AssetCategory, AssetType, LocalizedName

from lol_assets_indexer.adapters.ddragon import (
    SOURCE_FOLDER_TO_TYPE,
    ChampionSnapshot,
    SkinSnapshot,
)
from lol_assets_indexer.adapters.tarball import TarballScan
from lol_assets_indexer.imaging import MeasuredImage
from lol_assets_indexer.naming import asset_id, champion_file_name, file_extension, skin_id

DDRAGON = "https://ddragon.leagueoflegends.com"

#: Os ícones de stat mod, que nenhum JSON do ddragon lista.
STAT_MODS_DIR = "img/perk-images/StatMods/"


def _texto(valor: Any) -> str | None:
    """Nome em branco no ddragon é ausência, não nome."""
    if not isinstance(valor, str):
        return None
    return valor.strip() or None


def _names(pt: Any, en: Any, *, fallback: str) -> LocalizedName:
    """Rótulo nos dois idiomas, com `""` tratado como ausência.

    O patch real traz item e feitiço com `"name": ""` — placeholder que o
    ddragon nunca removeu. O schema exige pelo menos um caractere, então o
    registro cai para o `fallback`, que é sempre um id.
    """
    return LocalizedName(pt_BR=_texto(pt) or fallback, en_US=_texto(en))


def _versioned_url(game_version: str, relative: str) -> str:
    return f"{DDRAGON}/cdn/{game_version}/{relative}"


def _unversioned_url(relative: str) -> str:
    return f"{DDRAGON}/cdn/{relative}"


def _asset(
    *,
    asset_type: AssetType,
    category: AssetCategory,
    natural_key: int | str,
    names: LocalizedName,
    source_url: str,
    file_name: str,
    measured: MeasuredImage,
    **extra: Any,
) -> Asset:
    """O registro. `storage_key` fica ausente: nada é copiado (ADR 0012)."""
    return Asset(
        id=asset_id(asset_type, natural_key),
        type=asset_type,
        category=category,
        names=names,
        source="ddragon",
        source_url=source_url,
        storage_key=None,
        file_name=file_name,
        width=measured.width,
        height=measured.height,
        format=measured.format,
        has_alpha=measured.has_alpha,
        bytes=measured.bytes,
        sha256=measured.sha256,
        **extra,
    )


def real_skins(ficha: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Skins de verdade. Chroma tem `parentSkin` e não entra — KICKOFF §B.1.4."""
    for skin in ficha.get("skins", []):
        if "parentSkin" not in skin:
            yield skin


def build_champion_assets(scan: TarballScan) -> list[Asset]:
    """Square por campeão; splash, loading e tile por skin; habilidades e passiva."""
    assets: list[Asset] = []
    pt_fichas = scan.champions.get("pt_BR", {})
    en_fichas = scan.champions.get("en_US", {})

    for champion_id, pt in pt_fichas.items():
        en = en_fichas.get(champion_id, pt)
        champion_key = int(pt["key"])
        nome = _names(pt.get("name"), en.get("name"), fallback=champion_id)
        comum = {"champion_key": champion_key, "champion_id": champion_id}

        achado = scan.resolve(f"img/champion/{champion_id}.png")
        if achado is not None:
            relativo, square = achado
            assets.append(
                _asset(
                    asset_type="square",
                    category="champion",
                    natural_key=champion_key,
                    names=nome,
                    source_url=_versioned_url(scan.game_version, relativo),
                    file_name=champion_file_name(champion_id, "square", square.format),
                    measured=square,
                    **comum,
                )
            )

        assets.extend(_champion_ability_assets(scan, champion_id, pt, en, nome, comum))
        assets.extend(_skin_assets(scan, champion_id, pt, en, champion_key, comum))

    return assets


def _champion_ability_assets(
    scan: TarballScan,
    champion_id: str,
    pt: dict[str, Any],
    en: dict[str, Any],
    fallback: LocalizedName,
    comum: dict[str, Any],
) -> Iterator[Asset]:
    passiva = pt.get("passive", {})
    arquivo = (passiva.get("image") or {}).get("full")
    if arquivo:
        medida = scan.image(f"img/passive/{arquivo}")
        if medida is not None:
            yield _asset(
                asset_type="passive_icon",
                category="champion",
                natural_key=f"{comum['champion_key']}.P",
                names=_names(
                    passiva.get("name"),
                    (en.get("passive") or {}).get("name"),
                    fallback=fallback.pt_BR,
                ),
                source_url=_versioned_url(scan.game_version, f"img/passive/{arquivo}"),
                file_name=f"{champion_id}_passive.{file_extension(medida.format)}",
                measured=medida,
                **comum,
            )

    spells_en = en.get("spells", [])
    for indice, spell in enumerate(pt.get("spells", [])):
        arquivo = (spell.get("image") or {}).get("full")
        if not arquivo:
            continue
        medida = scan.image(f"img/spell/{arquivo}")
        if medida is None:
            continue
        letra = "QWER"[indice] if indice < 4 else str(indice)
        yield _asset(
            asset_type="ability_icon",
            category="champion",
            natural_key=f"{comum['champion_key']}.{letra}",
            names=_names(
                spell.get("name"),
                (spells_en[indice].get("name") if indice < len(spells_en) else None),
                fallback=fallback.pt_BR,
            ),
            source_url=_versioned_url(scan.game_version, f"img/spell/{arquivo}"),
            file_name=f"{champion_id}_{letra}.{file_extension(medida.format)}",
            measured=medida,
            **comum,
        )


def _skin_assets(
    scan: TarballScan,
    champion_id: str,
    pt: dict[str, Any],
    en: dict[str, Any],
    champion_key: int,
    comum: dict[str, Any],
) -> Iterator[Asset]:
    skins_en = {int(s["num"]): s for s in en.get("skins", [])}
    for skin in real_skins(pt):
        num = int(skin["num"])
        nome = _names(
            pt.get("name") if num == 0 else skin.get("name"),
            en.get("name") if num == 0 else skins_en.get(num, {}).get("name"),
            fallback=champion_id,
        )
        for pasta, tipo in SOURCE_FOLDER_TO_TYPE.items():
            achado = scan.resolve(f"img/champion/{pasta}/{champion_id}_{num}.jpg")
            if achado is None:
                continue
            relativo, medida = achado
            yield _asset(
                asset_type=tipo,
                category="champion",
                natural_key=skin_id(champion_key, num),
                names=nome,
                # splash, centered, loading e tiles NÃO são versionados (ADR 0007).
                source_url=_unversioned_url(relativo),
                file_name=champion_file_name(champion_id, tipo, medida.format, skin_num=num),
                measured=medida,
                skin_id=skin_id(champion_key, num),
                skin_num=num,
                is_base_skin=num == 0,
                **comum,
            )


def _simple_category(
    scan: TarballScan,
    *,
    prefixo: str,
    tipo: AssetType,
    categoria: AssetCategory,
    prefixo_do_nome: str,
    versionado: bool,
    rotulos: dict[str, LocalizedName],
    etiquetas: dict[str, list[str]] | None = None,
) -> list[Asset]:
    """Categorias cujo registro é `um arquivo → um asset`, sem skin nem campeão."""
    assets: list[Asset] = []
    por_chave = etiquetas or {}
    for relativo, medida in scan.images_under(prefixo):
        arquivo = relativo.rsplit("/", 1)[-1]
        chave = arquivo.rsplit(".", 1)[0]
        nome = rotulos.get(chave) or _names(chave, None, fallback=chave)
        assets.append(
            _asset(
                asset_type=tipo,
                category=categoria,
                natural_key=chave,
                names=nome,
                source_url=(
                    _versioned_url(scan.game_version, relativo)
                    if versionado
                    else _unversioned_url(relativo)
                ),
                file_name=f"{prefixo_do_nome}_{chave}.{file_extension(medida.format)}",
                measured=medida,
                ref_id=chave,
                tags=por_chave.get(chave) or None,
            )
        )
    return assets


def _rotulos_de(scan: TarballScan, arquivo: str) -> dict[str, LocalizedName]:
    """Nomes por id, dos JSONs de `data/` que têm a forma `{data: {id: {name}}}`."""
    pt = (scan.data.get("pt_BR", {}).get(arquivo) or {}).get("data", {})
    en = (scan.data.get("en_US", {}).get(arquivo) or {}).get("data", {})
    return {
        str(chave): _names(
            valor.get("name"), (en.get(chave) or {}).get("name"), fallback=str(chave)
        )
        for chave, valor in pt.items()
        if isinstance(valor, dict)
    }


#: Mapas cujos itens a v1 filtra. §B.1.6 do KICKOFF.
MAPAS = {"11": "mapa:sr", "12": "mapa:aram", "30": "mapa:arena"}


def item_tags(scan: TarballScan) -> dict[str, list[str]]:
    """Etiquetas de filtro de item, do que o próprio `item.json` declara.

    Três coisas, e nada inventado: se é comprável (`gold.purchasable`), em que
    mapas aparece (`maps`), e a classificação que a Riot já dá (`tags`).

    O `purchasable: false` é o que separa item de verdade de item de missão, de
    modo antigo ou de upgrade do Ornn — todos continuam no JSON e todos poluiriam
    a listagem padrão (§B.1.6).
    """
    dados = (scan.data.get("pt_BR", {}).get("item.json") or {}).get("data", {})
    etiquetas: dict[str, list[str]] = {}
    for chave, item in dados.items():
        if not isinstance(item, dict):
            continue
        marcas: list[str] = []
        if (item.get("gold") or {}).get("purchasable"):
            marcas.append("compravel")
        for mapa, etiqueta in MAPAS.items():
            if (item.get("maps") or {}).get(mapa):
                marcas.append(etiqueta)
        marcas.extend(f"classe:{t.lower()}" for t in item.get("tags") or [] if isinstance(t, str))
        if marcas:
            etiquetas[str(chave)] = marcas
    return etiquetas


def build_item_assets(scan: TarballScan) -> list[Asset]:
    return _simple_category(
        scan,
        prefixo="img/item/",
        tipo="item_icon",
        categoria="item",
        prefixo_do_nome="Item",
        versionado=True,
        etiquetas=item_tags(scan),
        rotulos=_rotulos_de(scan, "item.json"),
    )


def build_profile_icon_assets(scan: TarballScan) -> list[Asset]:
    return _simple_category(
        scan,
        prefixo="img/profileicon/",
        tipo="profile_icon",
        categoria="profile_icon",
        prefixo_do_nome="ProfileIcon",
        versionado=True,
        rotulos={},
    )


def map_tags(scan: TarballScan) -> dict[str, list[str]]:
    """`map11` vira `mapa:11`, e o nome do mapa vira etiqueta legível."""
    dados = (scan.data.get("pt_BR", {}).get("map.json") or {}).get("data", {})
    etiquetas: dict[str, list[str]] = {}
    for chave, mapa in dados.items():
        if not isinstance(mapa, dict):
            continue
        arquivo = ((mapa.get("image") or {}).get("full") or "").rsplit(".", 1)[0]
        if arquivo:
            etiquetas[arquivo] = [f"mapa:{chave}"]
    return etiquetas


def build_map_assets(scan: TarballScan) -> list[Asset]:
    return _simple_category(
        scan,
        prefixo="img/map/",
        tipo="map_image",
        categoria="map",
        prefixo_do_nome="Map",
        versionado=True,
        etiquetas=map_tags(scan),
        rotulos={},
    )


def build_summoner_spell_assets(scan: TarballScan) -> list[Asset]:
    """Feitiços de invocador. `img/spell/` mistura eles com as habilidades."""
    rotulos = _rotulos_de(scan, "summoner.json")
    arquivos = {
        (valor.get("image") or {}).get("full"): chave
        for chave, valor in (scan.data.get("pt_BR", {}).get("summoner.json") or {})
        .get("data", {})
        .items()
    }
    assets: list[Asset] = []
    for arquivo, chave in arquivos.items():
        if not arquivo:
            continue
        medida = scan.image(f"img/spell/{arquivo}")
        if medida is None:
            continue
        assets.append(
            _asset(
                asset_type="summoner_spell_icon",
                category="summoner_spell",
                natural_key=chave,
                names=rotulos.get(chave) or _names(chave, None, fallback=chave),
                source_url=_versioned_url(scan.game_version, f"img/spell/{arquivo}"),
                file_name=f"Summoner_{chave}.{file_extension(medida.format)}",
                measured=medida,
                ref_id=chave,
            )
        )
    return assets


def build_rune_assets(scan: TarballScan) -> list[Asset]:
    """Runas e árvores. As URLs de `perk-images` não são versionadas."""
    rotulos: dict[str, LocalizedName] = {}
    arvores_pt = scan.data.get("pt_BR", {}).get("runesReforged.json") or []
    arvores_en = {
        a.get("id"): a for a in (scan.data.get("en_US", {}).get("runesReforged.json") or [])
    }
    caminhos: dict[str, tuple[str, AssetType, str]] = {}

    arvores: dict[str, list[str]] = {}
    for arvore in arvores_pt:
        arvore_en = arvores_en.get(arvore.get("id"), {})
        icone = arvore.get("icon")
        if icone:
            chave = str(arvore["id"])
            caminhos[f"img/{icone}"] = (chave, "rune_tree_icon", "RuneTree")
            # A própria árvore leva a etiqueta dela: é o que faz "Precisão"
            # filtrar a árvore e as runas dela de uma vez (RF-08).
            arvores[chave] = [f"arvore:{chave}"]
            rotulos[chave] = _names(arvore.get("name"), arvore_en.get("name"), fallback=chave)
        slots_en = arvore_en.get("slots", [])
        for i, slot in enumerate(arvore.get("slots", [])):
            runas_en = {
                r.get("id"): r for r in (slots_en[i].get("runes", []) if i < len(slots_en) else [])
            }
            for runa in slot.get("runes", []):
                icone = runa.get("icon")
                if not icone:
                    continue
                chave = str(runa["id"])
                caminhos[f"img/{icone}"] = (chave, "rune_icon", "Rune")
                arvores[chave] = [f"arvore:{arvore['id']}", f"slot:{i}"]
                rotulos[chave] = _names(
                    runa.get("name"),
                    (runas_en.get(runa.get("id")) or {}).get("name"),
                    fallback=chave,
                )

    # Os stat mods não aparecem em runesReforged.json — nenhum JSON do ddragon os
    # lista. São arquivos soltos, e a §A.4 do KICKOFF os cita junto com as runas
    # justamente porque também têm alfa e nunca podem virar JPEG (ADR 0001).
    for relativo, _ in scan.images_under(STAT_MODS_DIR):
        chave = relativo.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        caminhos[relativo] = (chave, "stat_mod_icon", "StatMod")
        # Stat mod não pertence a árvore nenhuma, e isso é informação: o filtro
        # por árvore precisa poder deixá-los de fora sem fingir que são runas.
        arvores[chave] = ["arvore:nenhuma"]

    assets: list[Asset] = []
    for relativo, (chave, tipo, prefixo) in caminhos.items():
        medida = scan.image(relativo)
        if medida is None:
            continue
        assets.append(
            _asset(
                asset_type=tipo,
                category="rune",
                natural_key=chave,
                names=rotulos.get(chave) or _names(chave, None, fallback=chave),
                source_url=_unversioned_url(relativo),
                file_name=f"{prefixo}_{chave}.{file_extension(medida.format)}",
                measured=medida,
                ref_id=chave,
                tags=arvores.get(chave) or None,
            )
        )
    return assets


def build_champion_snapshots(scan: TarballScan) -> list[ChampionSnapshot]:
    """As fichas normalizadas que alimentam o catálogo (ADR 0010)."""
    snapshots: list[ChampionSnapshot] = []
    en_fichas = scan.champions.get("en_US", {})

    for champion_id, pt in scan.champions.get("pt_BR", {}).items():
        en = en_fichas.get(champion_id, pt)
        skins_en = {int(s["num"]): s for s in en.get("skins", [])}
        skins = [
            SkinSnapshot(
                num=int(skin["num"]),
                names=_names(
                    pt.get("name") if int(skin["num"]) == 0 else skin.get("name"),
                    en.get("name")
                    if int(skin["num"]) == 0
                    else skins_en.get(int(skin["num"]), {}).get("name"),
                    fallback=champion_id,
                ),
                chroma_count=sum(
                    1
                    for outra in pt.get("skins", [])
                    if outra.get("parentSkin") == int(skin["num"])
                ),
            )
            for skin in real_skins(pt)
        ]
        snapshots.append(
            ChampionSnapshot(
                key=int(pt["key"]),
                champion_id=champion_id,
                names=_names(pt.get("name"), en.get("name"), fallback=champion_id),
                title=_names(
                    pt.get("title"), en.get("title"), fallback=_texto(pt.get("name")) or champion_id
                ),
                tags=list(pt.get("tags", [])),
                skins=skins,
                chroma_count=sum(1 for s in pt.get("skins", []) if "parentSkin" in s),
            )
        )
    return sorted(snapshots, key=lambda s: s.names.pt_BR)


#: Categoria → construtor. É esta tabela que o T-10 percorre para fatiar.
BUILDERS: dict[AssetCategory, Callable[[TarballScan], list[Asset]]] = {
    "champion": build_champion_assets,
    "item": build_item_assets,
    "summoner_spell": build_summoner_spell_assets,
    "profile_icon": build_profile_icon_assets,
    "rune": build_rune_assets,
    "map": build_map_assets,
}


def build_all(scan: TarballScan) -> dict[AssetCategory, list[Asset]]:
    """Todos os registros que o tarball do ddragon produz, por categoria."""
    return {categoria: construtor(scan) for categoria, construtor in BUILDERS.items()}

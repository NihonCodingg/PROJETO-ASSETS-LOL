"""T-09 — o tarball inteiro, numa passada, medindo tudo e copiando nada.

O que estes testes protegem: o filtro de escopo (44 % do peso do tarball é
descartado), o filtro de chroma, e a promessa do ADR 0012 de que nenhum registro
sai com `storageKey`.
"""

from __future__ import annotations

import collections
import copy
import hashlib

import pytest
from lol_assets_indexer.adapters.records import build_all, build_champion_assets, real_skins
from lol_assets_indexer.adapters.tarball import (
    TarballScan,
    data_target,
    is_in_scope_image,
    strip_version,
)
from lol_assets_schema.validators import validate_shard

VERSAO = "16.17.1"


# --- classificação de caminho -------------------------------------------------


@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("16.17.1/img/champion/Jax.png", "img/champion/Jax.png"),
        ("img/champion/splash/Jax_0.jpg", "img/champion/splash/Jax_0.jpg"),
        ("16.17.1/data/pt_BR/item.json", "data/pt_BR/item.json"),
    ],
)
def test_strip_version(entrada: str, esperado: str) -> None:
    assert strip_version(entrada) == esperado


@pytest.mark.parametrize(
    "caminho,dentro",
    [
        ("img/champion/Jax.png", True),
        ("img/champion/centered/Jax_0.jpg", True),
        ("img/item/3031.png", True),
        ("img/perk-images/Styles/x.png", True),
        ("img/tft-champion/x.png", False),
        ("img/challenges-images/z.png", False),
        ("img/mission/w.png", False),
        ("img/sprite/champion0.png", False),
        ("img/mode/classic/champion/x.png", False),
        ("data/pt_BR/item.json", False),
    ],
)
def test_filtro_de_escopo(caminho: str, dentro: bool) -> None:
    assert is_in_scope_image(caminho) is dentro


def test_data_target_so_aceita_os_idiomas_da_v1() -> None:
    assert data_target("data/pt_BR/item.json") == ("pt_BR", "item.json")
    assert data_target("data/en_US/champion/Jax.json") == ("en_US", "champion/Jax.json")
    assert data_target("data/th_TH/champion.json") is None
    assert data_target("data/pt_BR/challenges.json") is None


# --- a varredura ---------------------------------------------------------------


def test_uma_passada_mede_so_o_que_esta_no_escopo(scan: TarballScan) -> None:
    assert scan.images, "nada foi medido"
    assert scan.files > len(scan.images) + scan.skipped, "os JSONs de data/ também contam"
    for caminho in scan.images:
        assert is_in_scope_image(caminho), f"{caminho} não deveria ter sido aberto"
    assert scan.skipped > 0, "o filtro de escopo não descartou nada"
    assert not scan.unreadable, scan.unreadable


def test_nao_mede_nada_de_fora_do_escopo(scan: TarballScan) -> None:
    for proibido in ("tft", "challenges", "mission", "sprite", "mode/classic"):
        assert not any(proibido in caminho for caminho in scan.images)


def test_le_os_dois_idiomas_e_ignora_os_outros(scan: TarballScan) -> None:
    assert set(scan.champions) == {"pt_BR", "en_US"}
    assert scan.champions["pt_BR"]["Jax"]["key"] == "24", "a ficha vem desembrulhada"
    assert "item.json" in scan.data["pt_BR"]
    assert "th_TH" not in scan.data


# --- os registros ---------------------------------------------------------------


def test_chroma_nao_vira_skin(scan: TarballScan) -> None:
    """`parentSkin` é o que separa chroma de skin — KICKOFF §B.1.4."""
    ficha = scan.champions["pt_BR"]["Jax"]
    nums = [int(s["num"]) for s in real_skins(ficha)]
    assert nums == [0, 4], "o chroma 18 entrou como skin"

    assets = build_champion_assets(scan)
    splashes = [a for a in assets if a.type == "splash_centered" and a.champion_key == 24]
    assert {a.skin_num for a in splashes} == {0, 4}
    assert not any(a.skin_num == 18 for a in assets), "o chroma virou registro"


def test_os_quatro_cortes_saem_com_os_nomes_canonicos(scan: TarballScan) -> None:
    """ADR 0002: `centered` é splash_centered; `splash` é splash_wide."""
    jax = [a for a in build_champion_assets(scan) if a.champion_id == "Jax"]
    por_tipo = {a.type: a for a in jax if a.skin_num == 0}
    assert (por_tipo["splash_centered"].width, por_tipo["splash_centered"].height) == (1280, 720)
    assert (por_tipo["splash_wide"].width, por_tipo["splash_wide"].height) == (1215, 717)
    assert (por_tipo["loading"].width, por_tipo["loading"].height) == (308, 560)
    assert (por_tipo["tile"].width, por_tipo["tile"].height) == (380, 380)
    assert "/centered/" in por_tipo["splash_centered"].source_url
    assert "/splash/" in por_tipo["splash_wide"].source_url


def test_todas_as_categorias_produzem_registros_validos(scan: TarballScan) -> None:
    tudo = build_all(scan)
    assert set(tudo) == {"champion", "item", "summoner_spell", "profile_icon", "rune", "map"}
    for categoria, assets in tudo.items():
        assert assets, f"categoria {categoria} vazia"
        validate_shard(
            {
                "schemaVersion": "1.1.0",
                "gameVersion": VERSAO,
                "category": categoria,
                "generatedAt": "2026-09-07T00:00:00Z",
                "assets": [
                    a.model_dump(by_alias=True, exclude_none=True, mode="json") for a in assets
                ],
            }
        )


def test_nenhum_registro_tem_storage_key(scan: TarballScan) -> None:
    """ADR 0012: nada é copiado, então `storageKey` fica sempre ausente."""
    for assets in build_all(scan).values():
        for asset in assets:
            assert asset.storage_key is None, f"{asset.id} saiu com storageKey"


def test_urls_versionadas_e_nao_versionadas_nos_lugares_certos(scan: TarballScan) -> None:
    """ADR 0007: só alguns tipos são versionados. É isso que limita o histórico."""
    tudo = build_all(scan)
    versionados = {
        "square",
        "passive_icon",
        "ability_icon",
        "item_icon",
        "profile_icon",
        "map_image",
        "summoner_spell_icon",
    }
    for assets in tudo.values():
        for asset in assets:
            tem_versao = f"/cdn/{VERSAO}/" in asset.source_url
            if asset.type in versionados:
                assert tem_versao, f"{asset.id} devia ser versionado"
            else:
                assert not tem_versao, f"{asset.id} não devia ser versionado"


def test_runas_saem_com_alfa_e_como_png(scan: TarballScan) -> None:
    """S1 mediu: perk-images são RGBA. ADR 0001 regra 4 depende disso."""
    runas = build_all(scan)["rune"]
    assert runas
    for runa in runas:
        assert runa.has_alpha is True
        assert runa.format == "png"


def test_feitico_de_invocador_nao_vira_habilidade(scan: TarballScan) -> None:
    """`img/spell/` mistura habilidade de campeão com feitiço de invocador."""
    tudo = build_all(scan)
    habilidades = {a.id for a in tudo["champion"] if a.type == "ability_icon"}
    feiticos = {a.id for a in tudo["summoner_spell"]}
    assert habilidades and feiticos
    assert not (habilidades & feiticos)
    assert {a.champion_key for a in tudo["champion"] if a.type == "ability_icon"} == {9, 24}


def test_nomes_saem_dos_dois_idiomas(scan: TarballScan) -> None:
    item = build_all(scan)["item"][0]
    assert item.names.pt_BR == "Gume do Infinito"
    assert item.names.en_US == "Gume do Infinito"


def test_identidade_e_nome_de_arquivo(scan: TarballScan) -> None:
    jax = [a for a in build_champion_assets(scan) if a.champion_id == "Jax"]
    por_tipo = {a.type: a for a in jax if a.skin_num in (None, 0)}
    assert por_tipo["square"].id == "square:24"
    assert por_tipo["square"].file_name == "Jax_square.png"
    assert por_tipo["splash_centered"].id == "splash_centered:24000"
    assert por_tipo["splash_centered"].file_name == "Jax_000_splash_centered.jpg"


def test_a_medicao_bate_byte_a_byte_com_o_arquivo(
    scan: TarballScan, membros: dict[str, bytes]
) -> None:
    """RNF-13: o `sha256` do índice tem que valer para o arquivo servido pela fonte.

    Sem storage (ADR 0012) é o único jeito de o front conferir o que baixou.
    """
    conferidos = 0
    for caminho, dados in membros.items():
        medido = scan.image(strip_version(caminho))
        if medido is None:
            continue
        assert medido.bytes == len(dados), caminho
        assert medido.sha256 == hashlib.sha256(dados).hexdigest(), caminho
        conferidos += 1
    assert conferidos > 10, conferidos


#: Manifesto de contagens do tarball de fixture, por categoria e tipo.
#:
#: A fixture tem um caso de cada coisa: um campeão, duas skins de verdade, um
#: chroma, dois idiomas e um arquivo de cada categoria. Se um construtor parar de
#: produzir um tipo — ou passar a produzir a mais —, é aqui que aparece.
CONTAGENS_ESPERADAS: dict[str, dict[str, int]] = {
    "champion": {
        "square": 2,
        "passive_icon": 2,
        "ability_icon": 4,
        "splash_centered": 4,
        "splash_wide": 4,
        "loading": 4,
        "tile": 4,
    },
    "item": {"item_icon": 2},
    "summoner_spell": {"summoner_spell_icon": 1},
    "profile_icon": {"profile_icon": 1},
    "rune": {"rune_tree_icon": 1, "rune_icon": 1, "stat_mod_icon": 1},
    "map": {"map_image": 1},
}


def test_as_contagens_batem_com_o_manifesto_esperado(scan: TarballScan) -> None:
    """Critério 4 do T-09, na escala da fixture.

    Os números do patch real (173 squares, 2.118 splashes por tipo, 868 itens,
    726 feitiços) estão em `docs/evidencias/`; aqui o que se protege é que cada
    construtor continue produzindo exatamente os tipos que promete.
    """
    obtidas = {
        str(categoria): dict(collections.Counter(a.type for a in assets))
        for categoria, assets in build_all(scan).items()
    }
    for categoria, esperado in CONTAGENS_ESPERADAS.items():
        assert obtidas[categoria] == esperado, categoria
    assert set(obtidas) == set(CONTAGENS_ESPERADAS)


def test_nome_em_branco_no_ddragon_cai_para_o_id(scan: TarballScan) -> None:
    """O patch real tem item com `"name": ""`, e o schema exige um caractere.

    Encontrado rodando contra o tarball de verdade: a indexação inteira abortava
    num placeholder que o ddragon nunca removeu.
    """
    vazio = copy.deepcopy(scan)
    vazio.data["pt_BR"]["item.json"]["data"]["3031"]["name"] = "  "
    vazio.data["en_US"]["item.json"]["data"]["3031"]["name"] = ""

    item = build_all(vazio)["item"][0]
    assert item.names.pt_BR == "3031"
    assert item.names.en_US is None


def test_stat_mod_entra_mesmo_sem_json_que_o_liste(scan: TarballScan) -> None:
    """Nenhum JSON do ddragon lista stat mod; eles vêm da varredura da pasta.

    A §A.4 do KICKOFF os cita junto com as runas porque têm alfa e nunca podem
    virar JPEG — mas quem constrói pelo `runesReforged.json` simplesmente não os vê.
    """
    stat_mods = [a for a in build_all(scan)["rune"] if a.type == "stat_mod_icon"]
    assert stat_mods, "os stat mods sumiram do índice"
    for asset in stat_mods:
        assert asset.has_alpha is True
        assert asset.format == "png"
        assert "/perk-images/StatMods/" in asset.source_url
        assert asset.names.pt_BR == "StatModsHealthScalingIcon"


def test_caixa_divergente_no_nome_do_arquivo_nao_perde_a_skin(scan: TarballScan) -> None:
    """O ddragon escreve `Fiddlesticks` em `data/` e `FiddleSticks` em `img/`.

    São 13 skins reais no patch 16.17.1. Buscar só pelo caminho exato as apagaria
    do índice sem erro nenhum — some silenciosamente, que é o pior jeito.
    """
    fiddle = [a for a in build_champion_assets(scan) if a.champion_id == "Fiddlesticks"]
    splashes = [a for a in fiddle if a.type == "splash_centered"]
    assert {a.skin_num for a in splashes} == {0, 4}

    # A URL tem que ser a do arquivo que existe, não a deduzida do championId.
    for asset in splashes:
        assert "/FiddleSticks_" in asset.source_url, asset.source_url
    # E o nome do arquivo que oferecemos segue a nossa convenção, com o id do dado.
    assert splashes[0].file_name.startswith("Fiddlesticks_")
    assert scan.case_mismatches, "a divergência precisa ficar registrada"


# --- etiquetas de filtro (T-21) ------------------------------------------------------


def test_item_compravel_leva_a_etiqueta(scan: TarballScan) -> None:
    """§B.1.6: `purchasable: false` é o que separa item de verdade de item de missão."""
    itens = {a.ref_id: a for a in build_all(scan)["item"]}
    assert "compravel" in (itens["3031"].tags or [])
    assert "compravel" not in (itens["3901"].tags or []), "item de missão não é comprável"


def test_item_leva_os_mapas_em_que_aparece(scan: TarballScan) -> None:
    etiquetas = {a.ref_id: set(a.tags or []) for a in build_all(scan)["item"]}
    assert {"mapa:sr", "mapa:aram"} <= etiquetas["3031"]
    assert "mapa:arena" not in etiquetas["3031"], "o JSON diz false para a Arena"


def test_item_leva_a_classificacao_que_a_riot_ja_da(scan: TarballScan) -> None:
    itens = {a.ref_id: a for a in build_all(scan)["item"]}
    assert "classe:criticalstrike" in (itens["3031"].tags or [])


def test_runa_leva_a_arvore_a_que_pertence(scan: TarballScan) -> None:
    """É o que faz filtrar "Precisão" trazer a árvore e as runas dela de uma vez."""
    por_tipo = {a.type: a for a in build_all(scan)["rune"]}
    assert "arvore:8000" in (por_tipo["rune_tree_icon"].tags or [])
    assert "arvore:8000" in (por_tipo["rune_icon"].tags or [])


def test_stat_mod_nao_finge_pertencer_a_uma_arvore(scan: TarballScan) -> None:
    """Filtro por árvore precisa poder deixá-los de fora sem mentir."""
    stat_mods = [a for a in build_all(scan)["rune"] if a.type == "stat_mod_icon"]
    assert stat_mods
    assert all("arvore:nenhuma" in (a.tags or []) for a in stat_mods)


def test_mapa_leva_o_numero_dele(scan: TarballScan) -> None:
    mapas = build_all(scan)["map"]
    assert mapas
    assert "mapa:11" in (mapas[0].tags or [])


def test_categoria_sem_etiqueta_nao_ganha_lista_vazia(scan: TarballScan) -> None:
    """`tags: []` no índice seria ruído: ausência é ausência."""
    icones = build_all(scan)["profile_icon"]
    assert icones
    assert all(a.tags is None for a in icones)

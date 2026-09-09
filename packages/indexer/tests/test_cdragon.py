"""T-16 — o cdragon, e a regra que o S2 comprou com 162 requisições.

O spike testou os três caminhos que a §B.2.3 do KICKOFF sugeria **montar**:
404 em 162 de 162. Os caminhos **declarados** no JSON: 397 de 397 responderam
200. Por isso a regra deste adaptador é uma só — ler caminho, nunca escrever — e
por isso metade destes testes vigia justamente isso.

A fixture é a ficha real do Jax, enxugada: a skin base, uma com
`loadScreenVintagePath` e uma com chromas. Nenhum teste toca a rede.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import httpx
import pytest
import respx
from lol_assets_indexer.adapters import cdragon
from lol_assets_indexer.adapters.cdragon import (
    ASSET_PREFIX,
    GAME_DATA_ROOT,
    asset_url,
    champion_json_url,
    declared_assets,
    fetch_champion_assets,
)
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_schema.validators import validate_shard
from PIL import Image

CDRAGON = "https://raw.communitydragon.org"
FIXTURE = Path(__file__).parent / "fixtures" / "cdragon-jax-24.json"
FICHA = json.loads(FIXTURE.read_text(encoding="utf-8"))


def imagem(largura: int, altura: int, formato: str, *, alfa: bool = False) -> bytes:
    modo = "RGBA" if alfa else "RGB"
    cor = (9, 9, 9, 0) if alfa else (9, 9, 9)
    buffer = io.BytesIO()
    Image.new(modo, (largura, altura), cor).save(buffer, format=formato)
    return buffer.getvalue()


#: Dimensões medidas no S2, por tipo.
MEDIDAS = {
    "square": (128, 128, "PNG"),
    "splash_centered": (1280, 720, "JPEG"),
    "splash_wide": (1215, 717, "JPEG"),
    "tile": (380, 380, "JPEG"),
    "loading": (308, 560, "JPEG"),
    "loading_vintage": (308, 560, "JPEG"),
    "chroma": (270, 303, "PNG"),
    "passive_icon": (64, 64, "PNG"),
    "ability_icon": (64, 64, "PNG"),
}


def cliente() -> SourceClient:
    return SourceClient(IndexerSettings(indexer_max_retries=1))


def montar_rotas() -> None:
    respx.get(champion_json_url(CDRAGON, 24)).mock(return_value=httpx.Response(200, json=FICHA))
    for declarado in declared_assets(FICHA).assets:
        largura, altura, formato = MEDIDAS[declarado.type]
        respx.get(asset_url(CDRAGON, declarado.declared) or "").mock(
            return_value=httpx.Response(
                200, content=imagem(largura, altura, formato, alfa=formato == "PNG")
            )
        )


# --- a regra de mapeamento -------------------------------------------------------------


def test_o_caminho_declarado_vira_url_em_minusculas() -> None:
    """O cliente declara `ASSETS/Characters/Jax`; o cdragon serve `assets/characters/jax`."""
    url = asset_url(CDRAGON, "/lol-game-data/assets/ASSETS/Characters/Jax/Skins/Base/x.jpg")
    assert url == f"{CDRAGON}/latest/{GAME_DATA_ROOT}/assets/characters/jax/skins/base/x.jpg"


def test_caminho_ja_minusculo_passa_igual() -> None:
    url = asset_url(CDRAGON, f"{ASSET_PREFIX}v1/champion-icons/24.png")
    assert url == f"{CDRAGON}/latest/{GAME_DATA_ROOT}/v1/champion-icons/24.png"


def test_barra_no_fim_da_base_nao_duplica() -> None:
    assert asset_url(f"{CDRAGON}/", f"{ASSET_PREFIX}v1/x.png") == asset_url(
        CDRAGON, f"{ASSET_PREFIX}v1/x.png"
    )


def test_prefixo_inesperado_nao_vira_url() -> None:
    assert asset_url(CDRAGON, "champion-abilities/0024/ability_0024_P1.jpg") is None
    assert asset_url(CDRAGON, "/outra-coisa/assets/x.png") is None


# --- nenhum caminho é montado (a regra que o S2 comprou) ----------------------------------


def test_o_modulo_nao_monta_caminho_de_asset() -> None:
    """Varredura de fonte: f-string com extensão de imagem é caminho montado.

    A §B.2.3 do KICKOFF sugeria montar três caminhos. O S2 mediu **404 em 162 de
    162**. Esta é exatamente a regra que se perde num refactor bem-intencionado.
    """
    codigo = Path(cdragon.__file__).read_text(encoding="utf-8")
    suspeitos = re.findall(r'f"[^"]*\{[^"]*\}[^"]*\.(?:png|jpg|jpeg)"', codigo)
    assert not suspeitos, suspeitos


def test_todo_caminho_de_asset_sai_do_json():  # type: ignore[no-untyped-def]
    """Nenhum `DeclaredAsset` tem caminho que não esteja no documento."""
    bruto = json.dumps(FICHA)
    for declarado in declared_assets(FICHA).assets:
        assert declarado.declared in bruto


# --- o que a ficha declara --------------------------------------------------------------


def test_classifica_os_tipos_que_a_v1_usa() -> None:
    paths = declared_assets(FICHA)
    por_tipo: dict[str, int] = {}
    for declarado in paths.assets:
        por_tipo[declarado.type] = por_tipo.get(declarado.type, 0) + 1

    assert por_tipo == {
        "square": 1,
        "passive_icon": 1,
        "ability_icon": 4,
        "splash_centered": 3,
        "splash_wide": 3,
        "tile": 3,
        "loading": 3,
        "loading_vintage": 1,
        # a amostra "cor original" da skin com chromas, mais as três chromas
        "chroma": 4,
    }


def test_splash_centered_vem_de_splashPath_e_nao_do_uncentered() -> None:
    """ADR 0002: no cdragon, `splashPath` é o corte de 1280x720."""
    paths = declared_assets(FICHA)
    centered = next(d for d in paths.assets if d.type == "splash_centered")
    wide = next(d for d in paths.assets if d.type == "splash_wide")

    assert centered.json_path.endswith(".splashPath")
    assert wide.json_path.endswith(".uncenteredSplashPath")
    assert "uncentered" in wide.declared.lower()
    assert "uncentered" not in centered.declared.lower()


def test_vintage_so_aparece_na_skin_que_tem_o_campo() -> None:
    paths = declared_assets(FICHA)
    vintages = [d for d in paths.assets if d.type == "loading_vintage"]

    assert len(vintages) == 1
    assert vintages[0].skin == 24001
    com_o_campo = [s["id"] for s in FICHA["skins"] if s.get("loadScreenVintagePath")]
    assert [v.skin for v in vintages] == com_o_campo


def test_chroma_leva_o_parent_skin_num() -> None:
    """Critério 2 do T-16, e o que separa chroma de skin no índice."""
    paths = declared_assets(FICHA)
    chromas = [d for d in paths.assets if d.type == "chroma"]

    assert chromas, "a fixture tem uma skin com chromas"
    for chroma in chromas:
        assert chroma.parent_skin_num == 7, "todas pertencem à skin 24007"
    assert {c.skin for c in chromas} == {24007, 24009, 24010, 24011}


def test_a_amostra_da_propria_skin_tem_parent_igual_ao_proprio_num() -> None:
    """`skins[].chromaPath` é a "cor original", que o cliente mostra junto das chromas."""
    paths = declared_assets(FICHA)
    amostra = next(d for d in paths.assets if d.type == "chroma" and d.skin == 24007)
    assert amostra.parent_skin_num == 7


def test_caminho_relativo_e_registrado_como_nao_mapeavel() -> None:
    """Critério 4: não some em silêncio.

    `abilityVideoImagePath` traz `champion-abilities/...`, sem o prefixo. O S2
    testou: 404. Ele fica registrado para a próxima mudança de formato aparecer.
    """
    paths = declared_assets(FICHA)

    assert paths.unmappable, "a fixture tem caminho relativo de propósito"
    assert all("abilityVideoImagePath" in chave for chave in paths.unmappable)
    assert all(not valor.startswith(ASSET_PREFIX) for valor in paths.unmappable.values())


def test_voz_e_som_sao_ignorados_sem_virar_nao_mapeavel() -> None:
    """Eles casam o prefixo, mas não são asset visual — §1.2 da Spec."""
    paths = declared_assets(FICHA)
    declarados = {d.json_path for d in paths.assets} | set(paths.unmappable)

    assert "stingerSfxPath" not in declarados
    assert "chooseVoPath" not in declarados


def test_ficha_sem_skins_nao_quebra() -> None:
    assert declared_assets({"id": 24, "alias": "Jax", "name": "Jax"}).assets == []


# --- os registros -------------------------------------------------------------------------


@respx.mock
async def test_produz_registros_validos_contra_o_schema() -> None:
    montar_rotas()
    async with cliente() as http:
        assets, nao_mapeaveis = await fetch_champion_assets(http, 24)

    assert assets
    validate_shard(
        {
            "schemaVersion": "1.1.0",
            "gameVersion": "16.18.1",
            "category": "champion",
            "generatedAt": "2026-09-09T00:00:00Z",
            "assets": [a.model_dump(by_alias=True, exclude_none=True, mode="json") for a in assets],
        }
    )
    assert nao_mapeaveis


@respx.mock
async def test_a_fonte_registrada_e_cdragon() -> None:
    montar_rotas()
    async with cliente() as http:
        assets, _ = await fetch_champion_assets(http, 24)

    assert {a.source for a in assets} == {"cdragon"}
    assert all(a.source_url.startswith(f"{CDRAGON}/latest/") for a in assets)


@respx.mock
async def test_nenhum_registro_tem_storage_key() -> None:
    """ADR 0012 vale para toda fonte, não só para o ddragon."""
    montar_rotas()
    async with cliente() as http:
        assets, _ = await fetch_champion_assets(http, 24)

    assert all(a.storage_key is None for a in assets)


@respx.mock
async def test_as_dimensoes_medidas_batem_com_o_s2() -> None:
    montar_rotas()
    async with cliente() as http:
        assets, _ = await fetch_champion_assets(http, 24)

    por_tipo = {a.type: (a.width, a.height) for a in assets}
    assert por_tipo["splash_centered"] == (1280, 720)
    assert por_tipo["splash_wide"] == (1215, 717)
    assert por_tipo["chroma"] == (270, 303)
    assert por_tipo["loading_vintage"] == (308, 560)


@respx.mock
async def test_chroma_chega_ao_registro_com_parent_skin_num() -> None:
    montar_rotas()
    async with cliente() as http:
        assets, _ = await fetch_champion_assets(http, 24)

    chromas = [a for a in assets if a.type == "chroma"]
    assert len(chromas) == 4
    assert all(a.parent_skin_num == 7 for a in chromas)
    assert all(a.skin_id is not None and a.skin_num is not None for a in chromas)


@respx.mock
async def test_asset_ilegivel_nao_derruba_o_campeao() -> None:
    """Uma imagem quebrada custa um registro, não o campeão inteiro."""
    montar_rotas()
    quebrada = next(d for d in declared_assets(FICHA).assets if d.type == "tile")
    respx.get(asset_url(CDRAGON, quebrada.declared) or "").mock(
        return_value=httpx.Response(200, content=b"isto nao e imagem")
    )

    async with cliente() as http:
        assets, _ = await fetch_champion_assets(http, 24)

    assert assets
    assert not any(a.type == "tile" and a.skin_id == quebrada.skin for a in assets)


@respx.mock
async def test_ficha_inexistente_falha_alto() -> None:
    respx.get(champion_json_url(CDRAGON, 9999)).mock(return_value=httpx.Response(404))
    async with cliente() as http:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_champion_assets(http, 9999)


# --- emotes e ward skins (T-22) ------------------------------------------------------


EMOTES = [
    {"id": 1, "name": "", "inventoryIcon": "/lol-game-data/assets/"},
    {
        "id": 2,
        "name": "Mestre das Armas",
        "inventoryIcon": "/lol-game-data/assets/ASSETS/Loadouts/SummonerEmotes/Emote2.png",
    },
    {"id": 3, "name": "Sem ícone"},
    {"id": 4, "name": "Relativo", "inventoryIcon": "loadouts/emote4.png"},
]

WARDS = [
    {
        "id": 0,
        "name": "Sentinela Padrão",
        "wardImagePath": f"{ASSET_PREFIX}content/src/LeagueClient/WardSkinImages/wardHero_0.png",
        "wardShadowImagePath": (
            f"{ASSET_PREFIX}content/src/LeagueClient/WardSkinImages/wardHeroShadow_0.png"
        ),
    },
    {"id": 7, "name": "Só a sentinela", "wardImagePath": "/lol-game-data/assets/x/ward_7.png"},
]


def test_o_prefixo_sozinho_nao_e_caminho_de_arquivo() -> None:
    """9 das 2.347 entradas de emote trazem `/lol-game-data/assets/` e nada depois.

    É o que separa as 2.347 declaradas dos **2.338** que o S4 mediu.
    """
    from lol_assets_indexer.adapters.cdragon import declared_emotes

    catalogo = declared_emotes(EMOTES)
    assert [d.ref for d in catalogo.assets] == ["2"]
    assert "[0].inventoryIcon" in catalogo.unmappable


def test_emote_sem_icone_nao_vira_nao_mapeavel() -> None:
    """Campo ausente é ausência, não erro de mapeamento."""
    from lol_assets_indexer.adapters.cdragon import declared_emotes

    catalogo = declared_emotes(EMOTES)
    assert not any("[2]" in chave for chave in catalogo.unmappable)


def test_emote_com_caminho_relativo_e_registrado() -> None:
    from lol_assets_indexer.adapters.cdragon import declared_emotes

    catalogo = declared_emotes(EMOTES)
    assert catalogo.unmappable["[3].inventoryIcon"] == "loadouts/emote4.png"


def test_cada_ward_tem_duas_imagens() -> None:
    """265 wards, 530 arquivos — a sombra é outra arte, não duplicata."""
    from lol_assets_indexer.adapters.cdragon import declared_wards

    catalogo = declared_wards(WARDS)
    assert [d.ref for d in catalogo.assets] == ["0", "0-shadow", "7"]


def test_a_categoria_dos_dois_catalogos_e_a_certa() -> None:
    from lol_assets_indexer.adapters.cdragon import declared_emotes, declared_wards

    assert declared_emotes(EMOTES).category == "emote"
    assert declared_wards(WARDS).category == "ward"


@respx.mock
async def test_emotes_viram_registros_validos() -> None:
    from lol_assets_indexer.adapters.cdragon import EMOTES_JSON, catalog_url, fetch_emotes

    respx.get(catalog_url(CDRAGON, EMOTES_JSON)).mock(
        return_value=httpx.Response(200, json=EMOTES)
    )
    respx.get(re.compile(rf"{re.escape(CDRAGON)}/latest/.*emote2\.png")).mock(
        return_value=httpx.Response(200, content=imagem(256, 256, "PNG", alfa=True))
    )

    async with cliente() as http:
        assets, nao_mapeaveis = await fetch_emotes(http)

    assert len(assets) == 1
    emote = assets[0]
    assert emote.category == "emote"
    assert emote.type == "emote_icon"
    assert emote.file_name == "Emote_2.png"
    assert emote.names.pt_BR == "Mestre das Armas"
    assert (emote.width, emote.height) == (256, 256), "o S4 mediu 256x256"
    assert len(nao_mapeaveis) == 2


@respx.mock
async def test_wards_viram_registros_validos() -> None:
    from lol_assets_indexer.adapters.cdragon import WARDS_JSON, catalog_url, fetch_wards

    respx.get(catalog_url(CDRAGON, WARDS_JSON)).mock(return_value=httpx.Response(200, json=WARDS))
    respx.get(re.compile(rf"{re.escape(CDRAGON)}/latest/.*ward.*\.png")).mock(
        return_value=httpx.Response(200, content=imagem(460, 550, "PNG", alfa=True))
    )

    async with cliente() as http:
        assets, _ = await fetch_wards(http)

    assert {a.file_name for a in assets} == {"Ward_0.png", "Ward_0-shadow.png", "Ward_7.png"}
    assert all(a.category == "ward" for a in assets)
    assert all((a.width, a.height) == (460, 550) for a in assets), "o S4 mediu 460x550"

    validate_shard(
        {
            "schemaVersion": "1.1.0",
            "gameVersion": "16.18.1",
            "category": "ward",
            "generatedAt": "2026-09-09T00:00:00Z",
            "assets": [a.model_dump(by_alias=True, exclude_none=True, mode="json") for a in assets],
        }
    )


@respx.mock
async def test_nenhuma_das_duas_categorias_produz_rank() -> None:
    """Critério 4 do T-22: emblema de elo saiu da v1 pelo ADR 0012."""
    from lol_assets_indexer.adapters.cdragon import EMOTES_JSON, catalog_url, fetch_emotes

    respx.get(catalog_url(CDRAGON, EMOTES_JSON)).mock(
        return_value=httpx.Response(200, json=EMOTES)
    )
    respx.get(re.compile(rf"{re.escape(CDRAGON)}/latest/.*\.png")).mock(
        return_value=httpx.Response(200, content=imagem(256, 256, "PNG", alfa=True))
    )

    async with cliente() as http:
        assets, _ = await fetch_emotes(http)

    assert all(a.category != "rank" for a in assets)

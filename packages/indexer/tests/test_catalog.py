"""T-10 — as invariantes do ADR 0010, que nenhum JSON Schema pega.

O schema garante o formato de cada entrada. O que ele não vê é a relação entre
os dois níveis: `skinCount` contra o número de skins daquele campeão, `skinId`
contra `championKey * 1000 + skinNum`, uma base por campeão. É essa aritmética
que faz o seletor de skin encontrar o que procura, e ela quebra em silêncio.
"""

from __future__ import annotations

import pytest
from lol_assets_indexer.adapters.ddragon import ChampionSnapshot, SkinSnapshot
from lol_assets_indexer.catalog import CatalogShapeError, project_catalog, verify_catalog
from lol_assets_schema.models import Catalog, CatalogChampion, CatalogSkin, LocalizedName

VERSAO = "16.17.1"


def nome(texto: str) -> LocalizedName:
    return LocalizedName(pt_BR=texto, en_US=texto)


def campeao(chave: int, champion_id: str, skin_count: int = 2) -> CatalogChampion:
    return CatalogChampion(
        champion_key=chave,
        champion_id=champion_id,
        names=nome(champion_id),
        skin_count=skin_count,
        base_skin_id=chave * 1000,
    )


def skin(
    chave: int, num: int, *, base: bool | None = None, skin_id: int | None = None
) -> CatalogSkin:
    return CatalogSkin(
        skin_id=chave * 1000 + num if skin_id is None else skin_id,
        skin_num=num,
        champion_key=chave,
        names=nome(f"skin {num}"),
        is_base=num == 0 if base is None else base,
    )


def catalogo(campeoes: list[CatalogChampion], skins: list[CatalogSkin]) -> Catalog:
    return Catalog(
        schema_version="1.1.0",
        game_version=VERSAO,
        generated_at="2026-09-07T00:00:00Z",
        champions=campeoes,
        skins=skins,
    )


# --- o caminho certo ---------------------------------------------------------------


def test_catalogo_consistente_passa() -> None:
    verify_catalog(
        catalogo(
            [campeao(24, "Jax"), campeao(9, "Fiddlesticks", skin_count=1)],
            [skin(24, 0), skin(24, 4), skin(9, 0)],
        )
    )


def test_o_catalogo_projetado_do_tarball_e_consistente(scan) -> None:  # type: ignore[no-untyped-def]
    """A projeção real tem que passar na própria guarda."""
    from lol_assets_indexer.adapters.records import build_champion_snapshots

    verify_catalog(
        project_catalog(
            game_version=VERSAO,
            generated_at="2026-09-07T00:00:00Z",
            snapshots=build_champion_snapshots(scan),
        )
    )


# --- o que quebra em silêncio --------------------------------------------------------


def test_skin_count_que_nao_bate_e_recusado() -> None:
    with pytest.raises(CatalogShapeError, match="diz 3 skins"):
        verify_catalog(catalogo([campeao(24, "Jax", skin_count=3)], [skin(24, 0), skin(24, 4)]))


def test_campeao_repetido_e_recusado() -> None:
    with pytest.raises(CatalogShapeError, match="campeão repetido"):
        verify_catalog(catalogo([campeao(24, "Jax", 1), campeao(24, "Jax", 1)], [skin(24, 0)]))


def test_skin_repetida_e_recusada() -> None:
    with pytest.raises(CatalogShapeError, match="skin repetida"):
        verify_catalog(catalogo([campeao(24, "Jax", 2)], [skin(24, 0), skin(24, 0)]))


def test_skin_de_campeao_que_nao_existe_e_recusada() -> None:
    with pytest.raises(CatalogShapeError, match="não está no catálogo"):
        verify_catalog(catalogo([campeao(24, "Jax", 1)], [skin(24, 0), skin(99, 0)]))


def test_skin_id_que_nao_deriva_da_chave_e_recusado() -> None:
    """`skinId = championKey * 1000 + skinNum` é a junção entre os dois níveis."""
    with pytest.raises(CatalogShapeError, match="não bate com championKey"):
        verify_catalog(catalogo([campeao(24, "Jax", 1)], [skin(24, 0, skin_id=24999)]))


def test_campeao_sem_base_e_recusado() -> None:
    with pytest.raises(CatalogShapeError, match="0 skins marcadas como base"):
        verify_catalog(catalogo([campeao(24, "Jax", 1)], [skin(24, 4)]))


def test_campeao_com_duas_bases_e_recusado() -> None:
    with pytest.raises(CatalogShapeError, match="2 skins marcadas como base"):
        verify_catalog(catalogo([campeao(24, "Jax", 2)], [skin(24, 0), skin(24, 4, base=True)]))


def test_todos_os_problemas_saem_de_uma_vez() -> None:
    with pytest.raises(CatalogShapeError) as erro:
        verify_catalog(catalogo([campeao(24, "Jax", 5)], [skin(24, 0), skin(99, 0)]))

    mensagem = str(erro.value)
    assert "diz 5 skins" in mensagem
    assert "não está no catálogo" in mensagem


# --- chroma não é skin ----------------------------------------------------------------


def test_chroma_nao_entra_em_nenhum_dos_dois_niveis(scan) -> None:  # type: ignore[no-untyped-def]
    """KICKOFF §B.1.4, verificado na projeção e não só no construtor de assets."""
    from lol_assets_indexer.adapters.records import build_champion_snapshots

    projetado = project_catalog(
        game_version=VERSAO,
        generated_at="2026-09-07T00:00:00Z",
        snapshots=build_champion_snapshots(scan),
    )
    jax = next(c for c in projetado.champions if c.champion_key == 24)
    assert jax.skin_count == 2
    assert jax.chroma_count == 1, "o chroma conta, mas como chroma"
    assert 24018 not in {s.skin_id for s in projetado.skins}


def test_o_contador_de_skins_e_o_de_chromas_sao_independentes() -> None:
    projetado = project_catalog(
        game_version=VERSAO,
        generated_at="2026-09-07T00:00:00Z",
        snapshots=[
            ChampionSnapshot(
                key=24,
                champion_id="Jax",
                names=nome("Jax"),
                title=nome("o Grão-Mestre das Armas"),
                tags=["Fighter"],
                skins=[
                    SkinSnapshot(num=0, names=nome("Jax"), chroma_count=0),
                    SkinSnapshot(num=4, names=nome("Deus da Guerra"), chroma_count=7),
                ],
                chroma_count=7,
            )
        ],
    )
    verify_catalog(projetado)
    assert projetado.champions[0].skin_count == 2
    assert projetado.champions[0].chroma_count == 7
    assert len(projetado.skins) == 2

"""T-17 — a fusão, e as duas maneiras de ela estragar tudo em silêncio.

A primeira: deixar `splash_centered` e `splash_wide` competirem. O centrado tem
1280x720 e o aberto 1215x717, então o centrado "venceria" — e o corte aberto
sumiria do catálogo inteiro sem erro nenhum.

A segunda: desempatar para o lado errado. O S2 mediu empate em square, splash,
loading e tile; um desempate que não favorecesse o ddragon trocaria a fonte de
100 % dos assets de campeão sem ganhar um pixel.
"""

from __future__ import annotations

from lol_assets_indexer.merge import SOURCE_PRIORITY, merge_assets, merge_key, wins
from lol_assets_schema.models import Asset, AssetSource, AssetType, LocalizedName


def asset(
    tipo: AssetType,
    natural: int,
    *,
    source: AssetSource = "ddragon",
    largura: int = 1280,
    altura: int = 720,
    **extra: object,
) -> Asset:
    base: dict[str, object] = {
        "id": f"{tipo}:{natural}",
        "type": tipo,
        "category": "champion",
        "champion_key": 24,
        "champion_id": "Jax",
        "names": LocalizedName(pt_BR="Jax"),
        "source": source,
        "source_url": f"https://{source}.invalido/{tipo}/{natural}.jpg",
        "file_name": f"Jax_{tipo}.jpg",
        "width": largura,
        "height": altura,
        "format": "jpeg",
        "has_alpha": False,
        "bytes": largura * altura // 10,
        "sha256": "0" * 64,
    }
    por_skin = {"splash_centered", "splash_wide", "loading", "loading_vintage", "tile", "chroma"}
    if tipo in por_skin:
        base |= {"skin_id": natural, "skin_num": natural - 24000, "is_base_skin": natural == 24000}
    base.update(extra)
    return Asset.model_validate(base)


# --- a chave --------------------------------------------------------------------------


def test_a_chave_inclui_o_tipo() -> None:
    chave = merge_key(asset("splash_centered", 24000))
    assert chave == ("splash_centered:24000", "splash_centered")


def test_os_dois_cortes_de_splash_tem_chaves_diferentes() -> None:
    """Se um dia isto empatar, o corte aberto some do catálogo."""
    assert merge_key(asset("splash_centered", 24000)) != merge_key(asset("splash_wide", 24000))


# --- quem ganha -------------------------------------------------------------------------


def test_maior_resolucao_ganha() -> None:
    maior = asset("splash_centered", 24000, source="cdragon", largura=1920, altura=1080)
    menor = asset("splash_centered", 24000, source="ddragon")
    assert wins(maior, menor) is True
    assert wins(menor, maior) is False


def test_empate_de_resolucao_favorece_o_ddragon() -> None:
    """O caso de 100 % dos assets de campeão, segundo o S2."""
    do_cdragon = asset("splash_centered", 24000, source="cdragon")
    do_ddragon = asset("splash_centered", 24000, source="ddragon")

    assert wins(do_cdragon, do_ddragon) is False
    assert wins(do_ddragon, do_cdragon) is True


def test_a_ordem_de_prioridade_das_fontes_e_a_do_projeto() -> None:
    assert SOURCE_PRIORITY[0] == "ddragon"
    assert SOURCE_PRIORITY.index("cdragon") < SOURCE_PRIORITY.index("wiki")


def test_empate_total_mantem_quem_chegou_primeiro() -> None:
    """O resultado não pode depender da ordem em que as fontes foram lidas."""
    a = asset("splash_centered", 24000, source="ddragon")
    b = asset("splash_centered", 24000, source="ddragon")
    assert wins(b, a) is False


# --- a fusão -----------------------------------------------------------------------------


def test_mesma_identidade_e_tipo_vira_um_registro_so() -> None:
    fundidos, relatorio = merge_assets(
        [asset("splash_centered", 24000, source="ddragon")],
        [asset("splash_centered", 24000, source="cdragon")],
    )

    assert len(fundidos) == 1
    assert fundidos[0].source == "ddragon"
    assert relatorio.ties == 1
    assert relatorio.losers_by_source == {"cdragon": 1}


def test_o_source_do_vencedor_e_o_que_fica_no_indice() -> None:
    fundidos, _ = merge_assets(
        [asset("splash_centered", 24000, source="ddragon")],
        [asset("splash_centered", 24000, source="cdragon", largura=1920, altura=1080)],
    )
    assert fundidos[0].source == "cdragon"
    assert "cdragon" in fundidos[0].source_url
    assert (fundidos[0].width, fundidos[0].height) == (1920, 1080)


def test_os_dois_cortes_sobrevivem_a_fusao() -> None:
    """Critério 3: o centrado nunca substitui o aberto."""
    fundidos, _ = merge_assets(
        [
            asset("splash_centered", 24000, largura=1280, altura=720),
            asset("splash_wide", 24000, largura=1215, altura=717),
        ],
        [
            asset("splash_centered", 24000, source="cdragon", largura=1280, altura=720),
            asset("splash_wide", 24000, source="cdragon", largura=1215, altura=717),
        ],
    )

    tipos = {a.type for a in fundidos}
    assert tipos == {"splash_centered", "splash_wide"}
    assert len(fundidos) == 2


def test_chroma_que_so_existe_no_cdragon_sobrevive() -> None:
    """Critério 4, e o motivo de o cdragon existir no projeto."""
    fundidos, relatorio = merge_assets(
        [asset("splash_centered", 24000)],
        [
            asset("chroma", 24009, source="cdragon", largura=270, altura=303, parent_skin_num=7),
            asset("loading_vintage", 24001, source="cdragon", largura=308, altura=560),
        ],
    )

    por_tipo = {a.type: a for a in fundidos}
    assert set(por_tipo) == {"splash_centered", "chroma", "loading_vintage"}
    assert por_tipo["chroma"].parent_skin_num == 7
    assert relatorio.exclusive_by_source == {"ddragon": 1, "cdragon": 2}


def test_o_total_bate_com_a_soma_menos_as_duplicatas() -> None:
    """Critério 5."""
    do_ddragon = [asset("splash_centered", 24000), asset("square", 24)]
    do_cdragon = [
        asset("splash_centered", 24000, source="cdragon"),  # duplicata
        asset("chroma", 24009, source="cdragon", largura=270, altura=303, parent_skin_num=7),
    ]

    fundidos, relatorio = merge_assets(do_ddragon, do_cdragon)

    assert len(fundidos) == len(do_ddragon) + len(do_cdragon) - 1
    assert relatorio.total == len(fundidos)
    assert relatorio.contested == 1


def test_a_ordem_dos_argumentos_nao_muda_o_resultado() -> None:
    """Quem decide é a regra, não quem foi lido primeiro."""
    do_ddragon = [asset("splash_centered", 24000), asset("square", 24)]
    do_cdragon = [
        asset("splash_centered", 24000, source="cdragon"),
        asset("chroma", 24009, source="cdragon", largura=270, altura=303, parent_skin_num=7),
    ]

    numa_ordem, _ = merge_assets(do_ddragon, do_cdragon)
    na_outra, _ = merge_assets(do_cdragon, do_ddragon)

    assert [(a.id, a.source) for a in numa_ordem] == [(a.id, a.source) for a in na_outra]


def test_a_saida_e_estavel_entre_execucoes() -> None:
    """Ordem instável faria o hash do documento mudar sem o conteúdo mudar."""
    entrada = [asset("tile", 24004, largura=380, altura=380), asset("square", 24)]
    primeira, _ = merge_assets(entrada)
    segunda, _ = merge_assets(list(reversed(entrada)))

    assert [a.id for a in primeira] == [a.id for a in segunda]


def test_fonte_vazia_nao_quebra() -> None:
    fundidos, relatorio = merge_assets([], [asset("square", 24)])
    assert len(fundidos) == 1
    assert relatorio.total == 1


def test_sem_fonte_nenhuma_o_resultado_e_vazio() -> None:
    fundidos, relatorio = merge_assets()
    assert fundidos == []
    assert relatorio.total == 0


# --- o relatório -------------------------------------------------------------------------


def test_o_relatorio_separa_empate_de_disputa_por_resolucao() -> None:
    _, relatorio = merge_assets(
        [asset("splash_centered", 24000), asset("tile", 24000, largura=380, altura=380)],
        [
            asset("splash_centered", 24000, source="cdragon"),  # empate
            asset("tile", 24000, source="cdragon", largura=512, altura=512),  # resolução
        ],
    )

    assert relatorio.ties == 1
    assert relatorio.resolution_wins == 1


def test_o_relatorio_conta_vencedores_por_fonte() -> None:
    _, relatorio = merge_assets(
        [asset("splash_centered", 24000)],
        [asset("tile", 24000, source="cdragon", largura=512, altura=512)],
    )
    assert relatorio.winners_by_source == {"ddragon": 1, "cdragon": 1}


def test_o_relatorio_vai_para_o_log_com_o_que_importa() -> None:
    _, relatorio = merge_assets([asset("square", 24)])
    linha = relatorio.as_log()
    assert set(linha) == {"fusaoTotal", "fusaoDisputados", "fusaoEmpates", "fusaoPorResolucao"}

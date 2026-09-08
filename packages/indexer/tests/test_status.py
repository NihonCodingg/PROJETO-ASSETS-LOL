"""T-12 — o relatório da execução, que substitui monitoramento.

Não há processo vigiando nada (§11 da Spec). O que existe é `status.json`, o
resumo do job e a issue automática — e os três só valem se funcionarem **quando
a indexação falha**, que é justamente quando o código que os produz tem menos
informação para trabalhar.
"""

from __future__ import annotations

import pytest
from lol_assets_indexer.limits import BudgetReport, measure
from lol_assets_indexer.status import (
    EXPECTED_DIMENSIONS,
    build_status,
    dimension_deviations,
    render_summary,
)
from lol_assets_schema.models import Asset, LocalizedName
from lol_assets_schema.validators import validate_status

INICIO = "2026-09-08T00:00:00Z"
FIM = "2026-09-08T00:07:31Z"


def asset(tipo: str = "square", largura: int = 128, altura: int = 128, **extra: object) -> Asset:
    base: dict[str, object] = {
        "id": f"{tipo}:24",
        "type": tipo,
        "category": "champion",
        "champion_key": 24,
        "champion_id": "Jax",
        "names": LocalizedName(pt_BR="Jax"),
        "source": "ddragon",
        "source_url": "https://ddragon.leagueoflegends.com/cdn/16.17.1/img/champion/Jax.png",
        "file_name": "Jax_square.png",
        "width": largura,
        "height": altura,
        "format": "png",
        "has_alpha": False,
        "bytes": 27107,
        "sha256": "0" * 64,
    }
    # ADR 0002: corte por skin exige a identidade da skin.
    if tipo in {"splash_centered", "splash_wide", "loading", "tile", "chroma"}:
        base |= {"skin_id": 24000, "skin_num": 0, "is_base_skin": True}
    base.update(extra)
    return Asset.model_validate(base)


def orcamento() -> BudgetReport:
    return BudgetReport(
        catalog=measure("catalog", b"{}" * 500),
        shards=(measure("champion", b"[]" * 4000), measure("item", b"[]" * 100)),
        manifest=measure("manifest", b"{}" * 10),
    )


# --- o relatório existe mesmo quando quase nada aconteceu ---------------------------


def test_falha_antes_de_resolver_a_versao_ainda_produz_status_valido() -> None:
    """O pior caso: caiu no primeiro segundo e não se sabe nem o patch."""
    status = build_status(
        started_at=INICIO,
        finished_at=FIM,
        duration_seconds=0.4,
        game_version=None,
        failure=RuntimeError("ddragon fora do ar"),
    )

    documento = status.model_dump(by_alias=True, exclude_none=True, mode="json")
    validate_status(documento)
    assert documento["ok"] is False
    assert documento["failure"]["kind"] == "RuntimeError"
    assert "gameVersion" not in documento


def test_sucesso_produz_status_valido_e_completo() -> None:
    status = build_status(
        started_at=INICIO,
        finished_at=FIM,
        duration_seconds=451.2,
        game_version="16.17.1",
        run_id="123",
        assets_by_category={"champion": [asset()], "item": [asset("item_icon", 64, 64)]},
        catalog_champions=173,
        catalog_skins=2118,
        budget=orcamento(),
    )

    documento = status.model_dump(by_alias=True, exclude_none=True, mode="json")
    validate_status(documento)
    assert documento["ok"] is True
    assert documento["counts"]["assets"] == 2
    assert documento["counts"]["champions"] == 173
    assert documento["counts"]["assetsByCategory"] == {"champion": 1, "item": 1}
    assert documento["counts"]["assetsBySource"] == {"ddragon": 2}
    assert documento["bytes"]["index"] > 0
    assert documento["bytes"]["describedAssets"] == 27107 * 2


def test_a_duracao_e_arredondada_mas_nao_perdida() -> None:
    status = build_status(
        started_at=INICIO,
        finished_at=FIM,
        duration_seconds=451.23456,
        game_version="16.17.1",
    )
    assert status.duration_seconds == 451.235


# --- dimensões inesperadas: o detector de fonte mudando --------------------------------


def test_dimensao_dentro_do_esperado_nao_vira_desvio() -> None:
    esperado = EXPECTED_DIMENSIONS["splash_centered"]
    assert dimension_deviations([asset("splash_centered", *esperado)]) == []


def test_dimensao_fora_do_esperado_e_agrupada_por_tamanho() -> None:
    """Uma linha por (tipo, tamanho), não uma por asset: são 2.118 splashes."""
    desvios = dimension_deviations(
        [
            asset("splash_centered", 1280, 720),
            asset("splash_centered", 1920, 1080),
            asset("splash_centered", 1920, 1080),
            asset("tile", 512, 512),
        ]
    )

    assert [(d.type, d.found, d.assets) for d in desvios] == [
        ("splash_centered", (1920, 1080), 2),
        ("tile", (512, 512), 1),
    ]
    assert desvios[0].expected == (1280, 720)
    assert desvios[0].example == "splash_centered:24"


def test_tipo_sem_dimensao_canonica_nunca_vira_desvio() -> None:
    """Ícone de item não tem tamanho fixo medido; não dá para chamar de desvio."""
    assert dimension_deviations([asset("item_icon", 999, 999)]) == []


def test_o_desvio_entra_no_status_e_valida() -> None:
    status = build_status(
        started_at=INICIO,
        finished_at=FIM,
        duration_seconds=1.0,
        game_version="16.17.1",
        assets_by_category={"champion": [asset("tile", 512, 512)]},
    )
    documento = status.model_dump(by_alias=True, exclude_none=True, mode="json")
    validate_status(documento)
    assert documento["unexpectedDimensions"][0]["found"] == [512, 512]


# --- o resumo do job -------------------------------------------------------------------


def test_o_resumo_de_falha_comeca_pelo_motivo() -> None:
    """Quem abre a aba do Actions depois de uma falha quer o motivo, não a contagem."""
    texto = render_summary(
        build_status(
            started_at=INICIO,
            finished_at=FIM,
            duration_seconds=2.0,
            game_version="16.17.1",
            failure=ValueError("versions.json não devolveu uma lista de versões"),
        )
    )

    assert texto.startswith("## ❌ Indexação — 16.17.1")
    assert "**ValueError**" in texto
    assert "versions.json" in texto
    assert texto.index("ValueError") < texto.index("Duração")


def test_o_resumo_de_sucesso_traz_a_tabela_por_categoria() -> None:
    texto = render_summary(
        build_status(
            started_at=INICIO,
            finished_at=FIM,
            duration_seconds=451.2,
            game_version="16.17.1",
            assets_by_category={"champion": [asset()], "item": [asset("item_icon", 64, 64)]},
            catalog_champions=173,
            catalog_skins=2118,
            budget=orcamento(),
        )
    )

    assert texto.startswith("## ✅ Indexação — 16.17.1")
    assert "| `champion` | 1 |" in texto
    assert "| Skins | 2.118 |" in texto
    assert "451.2 s" in texto


def test_o_resumo_avisa_de_dimensao_inesperada() -> None:
    texto = render_summary(
        build_status(
            started_at=INICIO,
            finished_at=FIM,
            duration_seconds=1.0,
            game_version="16.17.1",
            assets_by_category={"champion": [asset("tile", 512, 512)]},
        )
    )
    assert "Dimensões fora do esperado" in texto
    assert "380x380" in texto
    assert "**512x512**" in texto


def test_o_resumo_e_markdown_bem_formado_mesmo_sem_nada() -> None:
    texto = render_summary(
        build_status(started_at=INICIO, finished_at=FIM, duration_seconds=0.1, game_version=None)
    )
    assert texto.startswith("## ✅ Indexação — versão não resolvida")
    assert texto.endswith("\n")


@pytest.mark.parametrize("tipo", sorted(EXPECTED_DIMENSIONS))
def test_toda_dimensao_canonica_veio_do_s1(tipo: str) -> None:
    """Se alguém inventar um tamanho aqui, o detector passa a mentir."""
    medidas = {
        "splash_centered": (1280, 720),
        "splash_wide": (1215, 717),
        "loading": (308, 560),
        "tile": (380, 380),
        "square": (128, 128),
    }
    assert EXPECTED_DIMENSIONS[tipo] == medidas[tipo]  # type: ignore[index]

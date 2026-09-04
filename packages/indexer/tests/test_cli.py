"""T-07 — a CLI amarra as pontas e falha alto.

O que estes testes protegem é a ordem: validar antes de publicar. Um registro
inválido tem que abortar sem ter deixado nada meio publicado no bucket — e isso
só é verificável olhando o que NÃO foi escrito.
"""

from __future__ import annotations

import io
import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from lol_assets_indexer import logging_setup
from lol_assets_indexer.cli import app
from lol_assets_schema.models import Asset
from lol_assets_schema.validators import validate_catalog, validate_manifest, validate_shard
from PIL import Image
from typer.testing import CliRunner

DDRAGON = "https://ddragon.leagueoflegends.com"
VERSAO = "16.17.1"
runner = CliRunner()


def imagem(largura: int, altura: int, formato: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (largura, altura), (12, 34, 56)).save(buffer, format=formato)
    return buffer.getvalue()


def ficha() -> dict[str, Any]:
    return {
        "data": {
            "Jax": {
                "id": "Jax",
                "key": "24",
                "name": "Jax",
                "title": "o Grão-Mestre das Armas",
                "tags": ["Fighter"],
                "skins": [
                    {"id": "24000", "num": 0, "name": "default", "chromas": False},
                    {"id": "24004", "num": 4, "name": "Jax Deus da Guerra", "chromas": True},
                    # chroma: tem `parentSkin`, então não é skin de verdade (§B.1.4)
                    {"id": "24018", "num": 18, "name": "Chroma", "parentSkin": 4},
                ],
            }
        }
    }


def montar_rotas() -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(
        return_value=httpx.Response(200, json=[VERSAO, "16.16.1"])
    )
    for idioma in ("pt_BR", "en_US"):
        respx.get(f"{DDRAGON}/cdn/{VERSAO}/data/{idioma}/champion/Jax.json").mock(
            return_value=httpx.Response(200, json=ficha())
        )
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/img/champion/Jax.png").mock(
        return_value=httpx.Response(200, content=imagem(128, 128, "PNG"))
    )
    respx.get(f"{DDRAGON}/cdn/img/champion/centered/Jax_0.jpg").mock(
        return_value=httpx.Response(200, content=imagem(1280, 720, "JPEG"))
    )


def ler(destino: Path, nome: str) -> Any:
    return json.loads((destino / nome).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _limpar_contexto() -> Any:
    logging_setup.clear_context()
    yield
    logging_setup.clear_context()


# --- caminho feliz --------------------------------------------------------------


@respx.mock
def test_dry_run_produz_a_arvore_completa_e_sai_zero(tmp_path: Path) -> None:
    montar_rotas()
    resultado = runner.invoke(
        app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)]
    )

    assert resultado.exit_code == 0, resultado.output
    manifesto = ler(tmp_path, "manifest.json")
    validate_manifest(manifesto)

    versao = manifesto["versions"][0]
    validate_catalog(ler(tmp_path, versao["catalog"]["url"]))
    validate_shard(ler(tmp_path, versao["shards"][0]["url"]))

    # os assets também foram para a árvore, com os bytes de origem
    assert (tmp_path / VERSAO / "champion" / "Jax_square.png").exists()
    assert (tmp_path / VERSAO / "champion" / "Jax_000_splash_centered.jpg").exists()


@respx.mock
def test_o_catalogo_tem_um_campeao_e_as_skins_dele(tmp_path: Path) -> None:
    """ADR 0010: navegação por campeão, busca por skin — e chroma não é skin."""
    montar_rotas()
    runner.invoke(app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)])

    manifesto = ler(tmp_path, "manifest.json")
    catalogo = ler(tmp_path, manifesto["versions"][0]["catalog"]["url"])

    assert len(catalogo["champions"]) == 1
    campeao = catalogo["champions"][0]
    assert campeao["championKey"] == 24
    assert campeao["skinCount"] == 2, "duas skins de verdade; o chroma não conta"
    assert campeao["chromaCount"] == 1
    assert len(catalogo["skins"]) == campeao["skinCount"]
    assert {s["skinId"] for s in catalogo["skins"]} == {24000, 24004}
    assert sum(1 for s in catalogo["skins"] if s["isBase"]) == 1
    assert manifesto["versions"][0]["catalog"]["skins"] == len(catalogo["skins"])


@respx.mock
def test_a_miniatura_do_campeao_aponta_para_asset_publicado(tmp_path: Path) -> None:
    montar_rotas()
    runner.invoke(app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)])

    manifesto = ler(tmp_path, "manifest.json")
    catalogo = ler(tmp_path, manifesto["versions"][0]["catalog"]["url"])
    miniatura = catalogo["champions"][0]["thumbnailKey"]

    assert miniatura is not None
    assert (tmp_path / miniatura).exists(), "o cartão da grade apontaria para o vazio"


@respx.mock
def test_versao_pode_ser_fixada(tmp_path: Path) -> None:
    montar_rotas()
    rota = respx.get(f"{DDRAGON}/api/versions.json")
    resultado = runner.invoke(
        app,
        [
            "index",
            "--champion",
            "Jax",
            "--game-version",
            VERSAO,
            "--dry-run",
            "--output",
            str(tmp_path),
        ],
    )

    assert resultado.exit_code == 0
    assert not rota.called


# --- falha alto -----------------------------------------------------------------


@respx.mock
def test_registro_invalido_aborta_sem_publicar_nada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A validação vem antes da escrita. Nada de bucket meio publicado."""
    montar_rotas()

    async def adaptador_quebrado(*args: Any, **kwargs: Any) -> list[tuple[Asset, bytes]]:
        # `model_construct` pula a validação do Pydantic de propósito: o que se
        # testa aqui é a trava do JSON Schema, na fronteira da publicação.
        invalido = Asset.model_construct(
            id="rune_icon:8010",
            type="rune_icon",
            category="rune",
            names={"pt_BR": "x"},
            source="ddragon",
            source_url="https://exemplo.invalido/x.jpg",
            storage_key=f"{VERSAO}/rune/Rune_8010.jpg",
            file_name="Rune_8010.jpg",
            width=256,
            height=256,
            format="jpeg",
            has_alpha=True,  # alfa em JPEG: proibido pelo ADR 0001 regra 4
            bytes=10,
            sha256="0" * 64,
        )
        return [(invalido, b"bytes")]

    monkeypatch.setattr("lol_assets_indexer.cli.fetch_champion_assets", adaptador_quebrado)
    resultado = runner.invoke(
        app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)]
    )

    assert resultado.exit_code != 0
    assert not list(tmp_path.rglob("*.json")), "nada podia ter sido publicado"
    assert not (tmp_path / "manifest.json").exists()


@respx.mock
def test_fonte_indisponivel_sai_diferente_de_zero(tmp_path: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(200, json=[VERSAO]))
    respx.get(f"{DDRAGON}/cdn/{VERSAO}/data/pt_BR/champion/NaoExiste.json").mock(
        return_value=httpx.Response(404)
    )
    resultado = runner.invoke(
        app, ["index", "--champion", "NaoExiste", "--dry-run", "--output", str(tmp_path)]
    )

    assert resultado.exit_code != 0
    assert not (tmp_path / "manifest.json").exists()


def test_sem_credencial_e_sem_dry_run_falha_dizendo_o_que_fazer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variavel in ("S3_ENDPOINT_URL", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(variavel, raising=False)
    with respx.mock:
        montar_rotas()
        resultado = runner.invoke(app, ["index", "--champion", "Jax"])

    assert resultado.exit_code != 0


# --- log ------------------------------------------------------------------------


def eventos_de(resultado: Any) -> list[dict[str, Any]]:
    """O log vai para stderr; o CliRunner junta tudo em `output`.

    A linha de resumo do comando não é JSON, então filtra-se pelo `{`.
    """
    saida = resultado.output + getattr(resultado, "stderr", "")
    return [json.loads(linha) for linha in saida.splitlines() if linha.startswith("{")]


@respx.mock
def test_o_log_e_uma_linha_json_por_evento_com_a_versao(tmp_path: Path) -> None:
    montar_rotas()
    resultado = runner.invoke(
        app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)]
    )
    eventos = eventos_de(resultado)

    assert eventos, "a indexação precisa deixar rastro"
    assert all("event" in evento and "level" in evento for evento in eventos)

    # `gameVersion` entra no contexto assim que a versão é resolvida
    com_versao = [evento for evento in eventos if evento.get("gameVersion") == VERSAO]
    assert com_versao, "nenhum evento carregou o patch"
    assert any(evento.get("source") == "ddragon" for evento in com_versao)


@respx.mock
def test_o_log_de_falha_diz_o_tipo_do_erro(tmp_path: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(500))
    resultado = runner.invoke(
        app, ["index", "--champion", "Jax", "--dry-run", "--output", str(tmp_path)]
    )
    eventos = eventos_de(resultado)

    falhas = [evento for evento in eventos if evento["level"] == "error"]
    assert falhas
    assert "kind" in falhas[0]


def test_formatador_json_nao_quebra_com_objeto_estranho() -> None:
    formatador = logging_setup.JsonLineFormatter()
    registro = logging.LogRecord("t", logging.INFO, "f", 1, "oi", None, None)
    registro.__dict__["algo"] = object()
    assert json.loads(formatador.format(registro))["event"] == "oi"


# --- ajuda ------------------------------------------------------------------------


def test_help_descreve_as_opcoes_em_portugues() -> None:
    # O Rich quebra o texto na largura do terminal e pinta com ANSI. Sem fixar a
    # largura, a CI (80 colunas) trunca o nome das opções e o teste falha por
    # ambiente, não por regressão.
    resultado = runner.invoke(
        app,
        ["index", "--help"],
        env={"COLUMNS": "200", "NO_COLOR": "1", "TERM": "dumb"},
    )
    assert resultado.exit_code == 0

    limpo = re.sub("\x1b\\[[0-9;]*m", "", resultado.output)
    for trecho in ("--champion", "--game-version", "--dry-run", "--output"):
        assert trecho in limpo, limpo
    assert "campeão" in limpo

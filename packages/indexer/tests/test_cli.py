"""A CLI amarra as pontas e falha alto.

Duas coisas são verificadas aqui olhando o que **não** foi escrito: a ordem
(validar antes de escrever — um registro inválido aborta sem deixar índice pela
metade) e o ADR 0012 (nenhuma imagem sai para o disco, nunca).
"""

from __future__ import annotations

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
from typer.testing import CliRunner

DDRAGON = "https://ddragon.leagueoflegends.com"
VERSAO = "16.17.1"
CATEGORIAS = {"champion", "item", "summoner_spell", "profile_icon", "rune", "map"}
runner = CliRunner()


@pytest.fixture
def tarball_local(tmp_path: Path, tarball_bytes: bytes) -> Path:
    """O tarball de mentira em disco — é assim que a CLI o recebe."""
    caminho = tmp_path / f"dragontail-{VERSAO}.tgz"
    caminho.write_bytes(tarball_bytes)
    return caminho


@pytest.fixture
def destino(tmp_path: Path) -> Path:
    return tmp_path / "indice"


def indexar(tarball: Path, destino: Path, *extra: str) -> Any:
    return runner.invoke(
        app,
        ["index", "--tarball", str(tarball), "--output", str(destino), *extra],
    )


def ler(destino: Path, nome: str) -> Any:
    return json.loads((destino / nome).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _limpar_contexto() -> Any:
    logging_setup.clear_context()
    yield
    logging_setup.clear_context()


# --- caminho feliz --------------------------------------------------------------


def test_escreve_a_arvore_completa_e_sai_zero(tarball_local: Path, destino: Path) -> None:
    resultado = indexar(tarball_local, destino)

    assert resultado.exit_code == 0, resultado.output
    manifesto = ler(destino, "manifest.json")
    validate_manifest(manifesto)

    versao = manifesto["versions"][0]
    validate_catalog(ler(destino, versao["catalog"]["url"]))
    for fatia in versao["shards"]:
        validate_shard(ler(destino, fatia["url"]))


def test_uma_fatia_por_categoria(tarball_local: Path, destino: Path) -> None:
    indexar(tarball_local, destino)
    versao = ler(destino, "manifest.json")["versions"][0]

    assert {fatia["category"] for fatia in versao["shards"]} == CATEGORIAS
    assert versao["totalAssets"] == sum(fatia["assets"] for fatia in versao["shards"])


def test_nao_escreve_imagem_nenhuma(tarball_local: Path, destino: Path) -> None:
    """ADR 0012: o indexador mede e descarta. Só saem JSONs."""
    indexar(tarball_local, destino)

    escritos = sorted(caminho.suffix for caminho in destino.rglob("*") if caminho.is_file())
    assert escritos, "nada foi escrito"
    assert set(escritos) == {".json"}, escritos


def test_o_manifesto_declara_que_nada_foi_copiado(tarball_local: Path, destino: Path) -> None:
    manifesto = (indexar(tarball_local, destino), ler(destino, "manifest.json"))[1]

    assert manifesto["versions"][0]["assetsCopied"] is False
    assert "assetsBaseUrl" not in manifesto, "sem storage não há base pública"


def test_nenhum_registro_do_indice_tem_storage_key(tarball_local: Path, destino: Path) -> None:
    indexar(tarball_local, destino)
    versao = ler(destino, "manifest.json")["versions"][0]

    for fatia in versao["shards"]:
        for asset in ler(destino, fatia["url"])["assets"]:
            assert "storageKey" not in asset, asset["id"]
            assert asset["sourceUrl"].startswith("https://"), asset["id"]


def test_o_catalogo_tem_os_campeoes_e_as_skins_deles(tarball_local: Path, destino: Path) -> None:
    """ADR 0010: navegação por campeão, busca por skin — e chroma não é skin."""
    indexar(tarball_local, destino)
    manifesto = ler(destino, "manifest.json")
    catalogo = ler(destino, manifesto["versions"][0]["catalog"]["url"])

    assert len(catalogo["champions"]) == 2
    campeao = next(c for c in catalogo["champions"] if c["championKey"] == 24)
    assert campeao["championId"] == "Jax"
    assert campeao["skinCount"] == 2, "duas skins de verdade; o chroma não conta"
    assert campeao["chromaCount"] == 1
    assert len(catalogo["skins"]) == sum(c["skinCount"] for c in catalogo["champions"])
    assert {24000, 24004} <= {s["skinId"] for s in catalogo["skins"]}
    assert sum(1 for s in catalogo["skins"] if s["isBase"]) == 2
    assert manifesto["versions"][0]["catalog"]["skins"] == len(catalogo["skins"])


def test_a_miniatura_aponta_para_a_fonte(tarball_local: Path, destino: Path) -> None:
    """Sem storage, o cartão da grade carrega direto do ddragon (ADR 0012)."""
    indexar(tarball_local, destino)
    manifesto = ler(destino, "manifest.json")
    campeoes = ler(destino, manifesto["versions"][0]["catalog"]["url"])["champions"]
    campeao = next(c for c in campeoes if c["championKey"] == 24)

    assert campeao.get("thumbnailKey") is None
    assert campeao["thumbnailUrl"].endswith("/img/champion/Jax.png")


def test_a_miniatura_da_skin_e_o_tile(tarball_local: Path, destino: Path) -> None:
    """O resultado de busca é por skin (ADR 0010), então a miniatura dele é o tile."""
    indexar(tarball_local, destino)
    manifesto = ler(destino, "manifest.json")
    skins = ler(destino, manifesto["versions"][0]["catalog"]["url"])["skins"]

    por_id = {s["skinId"]: s for s in skins}
    assert por_id[24004]["thumbnailUrl"].endswith("/img/champion/tiles/Jax_4.jpg")
    assert por_id[24004].get("thumbnailKey") is None
    # e a do campeão de caixa divergente aponta para o arquivo que existe
    assert por_id[9004]["thumbnailUrl"].endswith("/img/champion/tiles/FiddleSticks_4.jpg")


def test_a_versao_sai_do_nome_do_arquivo(tarball_local: Path, destino: Path) -> None:
    indexar(tarball_local, destino)
    assert ler(destino, "manifest.json")["currentVersion"] == VERSAO


def test_versao_fixada_nao_consulta_a_lista_de_versoes(tarball_local: Path, destino: Path) -> None:
    with respx.mock:
        rota = respx.get(f"{DDRAGON}/api/versions.json")
        resultado = indexar(tarball_local, destino, "--game-version", VERSAO)

    assert resultado.exit_code == 0, resultado.output
    assert not rota.called


@respx.mock
def test_sem_tarball_local_ele_e_baixado(destino: Path, tarball_bytes: bytes) -> None:
    """O caminho de produção: uma requisição para 2,39 GB, medidos no S1."""
    respx.get(f"{DDRAGON}/api/versions.json").mock(
        return_value=httpx.Response(200, json=[VERSAO, "16.16.1"])
    )
    rota = respx.get(f"{DDRAGON}/cdn/dragontail-{VERSAO}.tgz").mock(
        return_value=httpx.Response(200, content=tarball_bytes)
    )

    resultado = runner.invoke(app, ["index", "--output", str(destino)])

    assert resultado.exit_code == 0, resultado.output
    assert rota.called
    assert ler(destino, "manifest.json")["currentVersion"] == VERSAO


# --- dry-run --------------------------------------------------------------------


def test_dry_run_valida_e_nao_escreve_nada(tarball_local: Path, destino: Path) -> None:
    resultado = indexar(tarball_local, destino, "--dry-run")

    assert resultado.exit_code == 0, resultado.output
    assert not destino.exists(), "o --dry-run não pode criar nem a pasta"
    assert "dry-run" in resultado.output


# --- falha alto -----------------------------------------------------------------


def test_registro_invalido_aborta_sem_escrever_nada(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A validação vem antes da escrita. Nada de índice pela metade."""

    def construtor_quebrado(*args: Any, **kwargs: Any) -> dict[str, list[Asset]]:
        # `model_construct` pula a validação do Pydantic de propósito: o que se
        # testa aqui é a trava do JSON Schema, na fronteira da escrita.
        invalido = Asset.model_construct(
            id="rune_icon:8010",
            type="rune_icon",
            category="rune",
            names={"pt_BR": "x"},
            source="ddragon",
            source_url="https://exemplo.invalido/x.jpg",
            file_name="Rune_8010.jpg",
            width=256,
            height=256,
            format="jpeg",
            has_alpha=True,  # alfa em JPEG: proibido pelo ADR 0001 regra 4
            bytes=10,
            sha256="0" * 64,
        )
        return {"rune": [invalido]}

    monkeypatch.setattr("lol_assets_indexer.cli.build_all", construtor_quebrado)
    resultado = indexar(tarball_local, destino)

    assert resultado.exit_code != 0
    assert not destino.exists(), "nada podia ter sido escrito"


@respx.mock
def test_fonte_indisponivel_sai_diferente_de_zero(destino: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(500))
    resultado = runner.invoke(app, ["index", "--output", str(destino)])

    assert resultado.exit_code != 0
    assert not (destino / "manifest.json").exists()


def test_nome_de_tarball_sem_versao_pede_a_versao(tmp_path: Path, destino: Path) -> None:
    estranho = tmp_path / "arquivo.tgz"
    estranho.write_bytes(b"")
    resultado = indexar(estranho, destino)

    assert resultado.exit_code != 0
    assert not destino.exists()


# --- log ------------------------------------------------------------------------


def eventos_de(resultado: Any) -> list[dict[str, Any]]:
    """O log vai para stderr; o CliRunner junta tudo em `output`.

    A linha de resumo do comando não é JSON, então filtra-se pelo `{`.
    """
    saida = resultado.output + getattr(resultado, "stderr", "")
    return [json.loads(linha) for linha in saida.splitlines() if linha.startswith("{")]


def test_o_log_e_uma_linha_json_por_evento_com_a_versao(tarball_local: Path, destino: Path) -> None:
    eventos = eventos_de(indexar(tarball_local, destino))

    assert eventos, "a indexação precisa deixar rastro"
    assert all("event" in evento and "level" in evento for evento in eventos)

    com_versao = [evento for evento in eventos if evento.get("gameVersion") == VERSAO]
    assert com_versao, "nenhum evento carregou o patch"
    assert any(evento.get("source") == "ddragon" for evento in com_versao)


def test_o_log_conta_o_que_foi_descartado(tarball_local: Path, destino: Path) -> None:
    """O filtro de escopo joga fora 44 % do tarball; isso precisa ser auditável."""
    eventos = eventos_de(indexar(tarball_local, destino))
    varredura = next(e for e in eventos if e["event"] == "tarball varrido")

    assert varredura["descartadas"] > 0
    assert varredura["imagens"] > 0


@respx.mock
def test_o_log_de_falha_diz_o_tipo_do_erro(destino: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(500))
    eventos = eventos_de(runner.invoke(app, ["index", "--output", str(destino)]))

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
    for trecho in ("--game-version", "--dry-run", "--output", "--tarball"):
        assert trecho in limpo, limpo
    assert "--champion" not in limpo, "o recorte por campeão morreu com o tarball"
    assert "Patch" in limpo

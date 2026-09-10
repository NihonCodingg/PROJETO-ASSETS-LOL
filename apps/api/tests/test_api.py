"""T-32 — as quatro rotas da API opcional, e a garantia de que ela é opcional.

O teste mais importante deste arquivo não testa rota nenhuma: é o que faz `grep`
no `apps/web` procurando qualquer chamada a esta API. O
[ADR 0006](../../../docs/adr/0006-api-como-componente-opcional.md) diz que o site
funciona sem ela, e "funciona sem ela" é o tipo de promessa que se quebra por
distração num PR de terça-feira.
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from lol_assets_api import __version__
from lol_assets_api.indice import Indice
from lol_assets_api.main import app, indice_atual
from lol_assets_schema import SCHEMA_VERSION

VERSAO = "16.18.1"
FONTE = "https://ddragon.leagueoflegends.com"


def _asset(asset_id: str, arquivo: str, chave: int) -> dict[str, object]:
    return {
        "id": asset_id,
        "type": "square",
        "category": "champion",
        "championKey": chave,
        "championId": arquivo.removesuffix(".png"),
        "names": {"pt_BR": arquivo},
        "source": "ddragon",
        "sourceUrl": f"{FONTE}/cdn/img/{arquivo}",
        "fileName": arquivo,
        "width": 128,
        "height": 128,
        "format": "png",
        "hasAlpha": True,
        "bytes": 10,
        "sha256": "0" * 64,
    }


@pytest.fixture
def indice_em_disco(tmp_path: Path) -> Path:
    """Um índice de mentira com a forma do de verdade."""
    destino = tmp_path / "indice"
    destino.mkdir()

    fatia = {
        "schemaVersion": SCHEMA_VERSION,
        "gameVersion": VERSAO,
        "category": "champion",
        "generatedAt": "2026-09-09T00:00:00Z",
        "assets": [_asset("square:24", "Jax.png", 24), _asset("square:99", "Lux.png", 99)],
    }
    (destino / "index-champion-a.json").write_text(json.dumps(fatia), encoding="utf-8")

    manifesto = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": "2026-09-09T00:00:00Z",
        "currentVersion": VERSAO,
        "generation": {"indexer": 3, "categories": ["champion"]},
        "versions": [
            {
                "gameVersion": VERSAO,
                "indexedAt": "2026-09-09T00:00:00Z",
                "assetsCopied": False,
                "catalog": {"url": "catalog-a.json", "champions": 2, "skins": 2, "bytes": 10},
                "shards": [
                    {
                        "category": "champion",
                        "url": "index-champion-a.json",
                        "assets": 2,
                        "bytes": 10,
                    }
                ],
            }
        ],
    }
    (destino / "manifest.json").write_text(json.dumps(manifesto), encoding="utf-8")
    return destino


@pytest.fixture
def cliente(indice_em_disco: Path) -> Iterator[TestClient]:
    # **Uma** instância para o teste inteiro, como em produção: o cache mora no
    # objeto, e um `Indice` novo por requisição não teria cache nenhum.
    unico = Indice(indice_em_disco)
    app.dependency_overrides[indice_atual] = lambda: unico
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- /health ------------------------------------------------------------------------


def test_health_responde_ok() -> None:
    resposta = TestClient(app).get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "version": __version__}


def test_health_nao_precisa_de_indice(tmp_path: Path) -> None:
    """A sonda tem que responder mesmo com o índice ausente: ela mede o processo."""
    app.dependency_overrides[indice_atual] = lambda: Indice(tmp_path / "vazio")
    try:
        assert TestClient(app).get("/health").status_code == 200
    finally:
        app.dependency_overrides.clear()


# --- /versions ----------------------------------------------------------------------


def test_versions_devolve_o_manifesto_tal_e_qual(
    cliente: TestClient, indice_em_disco: Path
) -> None:
    """Critério 2: o mesmo conteúdo, não uma projeção parecida."""
    resposta = cliente.get("/versions")
    assert resposta.status_code == 200

    do_disco = json.loads((indice_em_disco / "manifest.json").read_text(encoding="utf-8"))
    assert resposta.json() == do_disco


def test_sem_indice_a_api_diz_503(tmp_path: Path) -> None:
    """Indisponível, não "erro interno": não há índice, e isso é temporário."""
    app.dependency_overrides[indice_atual] = lambda: Indice(tmp_path / "vazio")
    try:
        resposta = TestClient(app).get("/versions")
        assert resposta.status_code == 503
        assert "lol-assets-indexer" in resposta.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# --- /index -------------------------------------------------------------------------


def test_index_devolve_a_fatia(cliente: TestClient) -> None:
    resposta = cliente.get(f"/index/{VERSAO}/champion")
    assert resposta.status_code == 200
    assert [a["id"] for a in resposta.json()["assets"]] == ["square:24", "square:99"]


def test_categoria_inexistente_e_404(cliente: TestClient) -> None:
    assert cliente.get(f"/index/{VERSAO}/emote").status_code == 404


def test_versao_inexistente_e_404(cliente: TestClient) -> None:
    assert cliente.get("/index/1.2.3/champion").status_code == 404


def test_a_fatia_e_lida_uma_vez_so(cliente: TestClient, indice_em_disco: Path) -> None:
    """Cache: reler 19 MB de JSON por requisição seria absurdo."""
    cliente.get(f"/index/{VERSAO}/champion")
    (indice_em_disco / "index-champion-a.json").unlink()

    # Sem cache, isto seria 503. Com cache, o conteúdo continua servido.
    assert cliente.get(f"/index/{VERSAO}/champion").status_code == 200


def test_manifesto_novo_invalida_as_fatias(cliente: TestClient, indice_em_disco: Path) -> None:
    """Nunca reler seria pior que reler sempre: serviria o patch de ontem calado."""
    cliente.get(f"/index/{VERSAO}/champion")

    manifesto = json.loads((indice_em_disco / "manifest.json").read_text(encoding="utf-8"))
    manifesto["generatedAt"] = "2026-09-10T00:00:00Z"
    caminho = indice_em_disco / "manifest.json"
    caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    # `mtime` no passado: escrever no mesmo segundo pode não mudar o carimbo, e
    # aí o teste passaria ou falharia conforme o relógio.
    os.utime(caminho, (0, 0))
    (indice_em_disco / "index-champion-a.json").unlink()

    assert cliente.get(f"/index/{VERSAO}/champion").status_code == 503


# --- POST /zip ----------------------------------------------------------------------


@respx.mock
def test_zip_com_n_ids_devolve_n_arquivos(cliente: TestClient) -> None:
    """Critério 3, primeira metade."""
    respx.get(url__startswith=f"{FONTE}/cdn/img/").mock(
        return_value=httpx.Response(200, content=b"bytes de imagem")
    )

    resposta = cliente.post("/zip", json={"ids": ["square:24", "square:99"]})

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as pacote:
        assert sorted(pacote.namelist()) == ["Jax.png", "Lux.png"]
        assert pacote.read("Jax.png") == b"bytes de imagem"


@respx.mock
def test_a_ordem_do_zip_e_a_ordem_pedida(cliente: TestClient) -> None:
    respx.get(url__startswith=f"{FONTE}/cdn/img/").mock(
        return_value=httpx.Response(200, content=b"x")
    )
    resposta = cliente.post("/zip", json={"ids": ["square:99", "square:24"]})

    with zipfile.ZipFile(io.BytesIO(resposta.content)) as pacote:
        assert pacote.namelist() == ["Lux.png", "Jax.png"]


@respx.mock
def test_arquivo_que_nao_vem_nao_derruba_o_lote(cliente: TestClient) -> None:
    """Mesma decisão do T-25: o que faltou vai escrito dentro do zip."""
    respx.get(f"{FONTE}/cdn/img/Jax.png").mock(return_value=httpx.Response(200, content=b"ok"))
    respx.get(f"{FONTE}/cdn/img/Lux.png").mock(return_value=httpx.Response(404))

    resposta = cliente.post("/zip", json={"ids": ["square:24", "square:99"]})

    assert resposta.status_code == 200
    assert resposta.headers["X-Assets-Incluidos"] == "1"
    assert resposta.headers["X-Assets-Falharam"] == "1"
    with zipfile.ZipFile(io.BytesIO(resposta.content)) as pacote:
        assert "Jax.png" in pacote.namelist()
        assert "Lux.png" in pacote.read("FALHAS.txt").decode()


def test_acima_do_limite_e_413(cliente: TestClient) -> None:
    """Critério 3, segunda metade."""
    resposta = cliente.post("/zip", json={"ids": [f"id-{i}" for i in range(501)]})
    assert resposta.status_code == 413
    assert "501" in resposta.json()["detail"]


def test_zip_sem_id_nenhum_e_recusado(cliente: TestClient) -> None:
    assert cliente.post("/zip", json={"ids": []}).status_code == 422


def test_id_que_nao_existe_e_404(cliente: TestClient) -> None:
    assert cliente.post("/zip", json={"ids": ["nao-existe"]}).status_code == 404


@respx.mock
def test_o_zip_guarda_sem_comprimir(cliente: TestClient) -> None:
    """JPEG e PNG já vêm comprimidos; deflatar de novo é CPU por ~0%."""
    respx.get(url__startswith=f"{FONTE}/cdn/img/").mock(
        return_value=httpx.Response(200, content=b"x" * 5000)
    )
    resposta = cliente.post("/zip", json={"ids": ["square:24"]})

    with zipfile.ZipFile(io.BytesIO(resposta.content)) as pacote:
        assert pacote.getinfo("Jax.png").compress_type == zipfile.ZIP_STORED


# --- critério 4: a API é mesmo opcional ------------------------------------------------


def test_o_front_nao_chama_a_api() -> None:
    """O teste de arquitetura do ADR 0006, feito na marra.

    Não é elegante, e é de propósito: qualquer coisa mais sofisticada teria uma
    forma de ser burlada sem querer. Uma varredura de texto por `/health`,
    `/versions`, `/index/` e `localhost:8000` no código do front pega o caso
    real — alguém colando um `fetch` porque foi mais fácil.
    """
    raiz = Path(__file__).resolve().parents[3] / "apps" / "web" / "src"
    suspeitos = re.compile(
        r"""localhost:8000|127\.0\.0\.1:8000|/versions\b|["'`]/zip\b|API_BASE|NEXT_PUBLIC_API""",
    )

    achados = [
        f"{arquivo.relative_to(raiz)}: {linha.strip()}"
        for arquivo in raiz.rglob("*.ts*")
        for linha in arquivo.read_text(encoding="utf-8").splitlines()
        if suspeitos.search(linha)
    ]
    assert achados == [], "o front passou a depender da API opcional"


def test_o_front_nao_declara_a_api_como_dependencia() -> None:
    pacote = Path(__file__).resolve().parents[3] / "apps" / "web" / "package.json"
    conteudo = json.loads(pacote.read_text(encoding="utf-8"))
    dependencias = {**conteudo.get("dependencies", {}), **conteudo.get("devDependencies", {})}
    assert not any("api" in nome for nome in dependencias)

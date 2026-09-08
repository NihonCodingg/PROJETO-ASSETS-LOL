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


def documentos_de_indice(destino: Path) -> set[str]:
    """O que o índice escreveu. `status.json` não conta — é relatório, não índice.

    A promessa de "aborta sem escrever nada" é sobre o índice: o relatório da
    falha é escrito **de propósito** mesmo quando a indexação aborta (T-12).
    """
    if not destino.exists():
        return set()
    return {caminho.name for caminho in destino.glob("*.json") if caminho.name != "status.json"}


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
    assert documentos_de_indice(destino) == set(), "nada de índice podia ter sido escrito"


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
    assert documentos_de_indice(destino) == set()


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


# --- guardas de orçamento e de forma (T-10) ---------------------------------------


def test_orcamento_estourado_aborta_sem_escrever_nada(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RNF-03: o build para. Não escreve e depois reclama."""
    monkeypatch.setattr("lol_assets_indexer.limits.CATALOG_GZIP_LIMIT", 10)
    resultado = indexar(tarball_local, destino)

    assert resultado.exit_code != 0
    assert documentos_de_indice(destino) == set(), "o estouro tem que abortar ANTES da escrita"
    assert "RNF-03" in resultado.output


def test_indice_grande_demais_aborta_antes_de_escrever(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RNF-05: o índice é versionado no repositório desde o ADR 0012."""
    monkeypatch.setattr("lol_assets_indexer.limits.INDEX_RAW_LIMIT", 100)
    resultado = indexar(tarball_local, destino)

    assert resultado.exit_code != 0
    assert documentos_de_indice(destino) == set()
    assert "RNF-05" in resultado.output


def test_dry_run_tambem_aplica_a_guarda(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Senão o ensaio passaria e o build de verdade falharia — o pior dos dois."""
    monkeypatch.setattr("lol_assets_indexer.limits.CATALOG_GZIP_LIMIT", 10)
    assert indexar(tarball_local, destino, "--dry-run").exit_code != 0


def test_catalogo_inconsistente_aborta_sem_escrever_nada(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADR 0010: `skinCount` que não bate com skins[] quebra o seletor em silêncio."""
    from lol_assets_indexer import catalog as modulo

    original = modulo.project_catalog

    def torto(**kwargs: Any) -> Any:
        projetado = original(**kwargs)
        projetado.champions[0].skin_count += 1
        return projetado

    monkeypatch.setattr("lol_assets_indexer.cli.project_catalog", torto)
    resultado = indexar(tarball_local, destino)

    assert resultado.exit_code != 0
    assert documentos_de_indice(destino) == set()
    assert "ADR 0010" in resultado.output


def test_o_resumo_diz_o_tamanho_do_indice(tarball_local: Path, destino: Path) -> None:
    """É o número que decide se o orçamento ainda cabe; não pode ficar só no log."""
    resultado = indexar(tarball_local, destino)
    escrito = sum((destino / nome).stat().st_size for nome in documentos_de_indice(destino))

    esperado = f"{escrito:,}".replace(",", ".")
    assert f"{esperado} bytes" in resultado.output, resultado.output


def test_cada_fatia_traz_sha256_e_contagem_corretos(tarball_local: Path, destino: Path) -> None:
    import hashlib

    indexar(tarball_local, destino)
    versao = ler(destino, "manifest.json")["versions"][0]

    for fatia in versao["shards"]:
        bruto = (destino / fatia["url"]).read_bytes()
        assert fatia["bytes"] == len(bruto)
        assert fatia["sha256"] == hashlib.sha256(bruto).hexdigest()
        assert fatia["assets"] == len(json.loads(bruto)["assets"])

    catalogo = versao["catalog"]
    bruto = (destino / catalogo["url"]).read_bytes()
    assert catalogo["sha256"] == hashlib.sha256(bruto).hexdigest()
    assert catalogo["champions"] == len(json.loads(bruto)["champions"])


# --- uma versão por vez (T-11 / ADR 0013) -------------------------------------------

ANTIGA = "16.16.1"


@pytest.fixture
def depois_de_dois_patches(tarball_local: Path, destino: Path) -> Path:
    """Indexa 16.16.1 e depois 16.17.1 no mesmo destino."""
    assert indexar(tarball_local, destino, "--game-version", ANTIGA).exit_code == 0
    assert indexar(tarball_local, destino, "--game-version", VERSAO).exit_code == 0
    return destino


def test_o_manifesto_tem_uma_versao_so(depois_de_dois_patches: Path) -> None:
    """ADR 0013: guardar histórico custa 4,4 MB por patch e entrega ícone repetido."""
    manifesto = ler(depois_de_dois_patches, "manifest.json")

    assert [v["gameVersion"] for v in manifesto["versions"]] == [VERSAO]
    assert manifesto["currentVersion"] == VERSAO


def test_a_versao_anterior_some_do_destino(depois_de_dois_patches: Path) -> None:
    """Não basta sair do manifesto: o arquivo tem que sair do diretório."""
    manifesto = ler(depois_de_dois_patches, "manifest.json")
    versao = manifesto["versions"][0]
    referenciados = {"manifest.json", versao["catalog"]["url"]}
    referenciados.update(fatia["url"] for fatia in versao["shards"])

    no_disco = documentos_de_indice(depois_de_dois_patches)
    assert no_disco == referenciados, no_disco - referenciados


def test_o_indice_nao_cresce_com_o_numero_de_patches(tarball_local: Path, destino: Path) -> None:
    """A conta que derrubou o histórico: 4,4 MB por patch, ~115 MB/ano."""

    def tamanho() -> int:
        return sum((destino / nome).stat().st_size for nome in documentos_de_indice(destino))

    indexar(tarball_local, destino, "--game-version", "16.15.1")
    primeiro = tamanho()
    indexar(tarball_local, destino, "--game-version", ANTIGA)
    indexar(tarball_local, destino, "--game-version", VERSAO)

    # Os três patches têm o mesmo conteúdo, então o tamanho tem que ser o mesmo.
    assert tamanho() == primeiro


def test_a_varredura_so_roda_depois_do_manifesto(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADR 0007: passo destrutivo nunca antes do índice novo estar escrito.

    Se a publicação do manifesto falhar, o destino tem que continuar servindo a
    versão anterior inteira — não pode ter sido varrido antes.
    """
    indexar(tarball_local, destino, "--game-version", ANTIGA)
    antes = documentos_de_indice(destino)

    def explode(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("falha ao escrever o manifesto")

    monkeypatch.setattr("lol_assets_indexer.publish.storage.Publisher.publish_manifest", explode)
    assert indexar(tarball_local, destino, "--game-version", VERSAO).exit_code != 0

    assert antes <= documentos_de_indice(destino), "a versão anterior foi apagada antes da hora"


def test_reindexar_o_mesmo_patch_nao_duplica_nem_deixa_lixo(
    tarball_local: Path, destino: Path
) -> None:
    indexar(tarball_local, destino)
    primeiro = documentos_de_indice(destino)
    indexar(tarball_local, destino)

    assert documentos_de_indice(destino) == primeiro
    assert len(ler(destino, "manifest.json")["versions"]) == 1


def test_assets_copied_continua_falso(depois_de_dois_patches: Path) -> None:
    manifesto = ler(depois_de_dois_patches, "manifest.json")
    assert all(v["assetsCopied"] is False for v in manifesto["versions"])


def test_a_varredura_nunca_toca_no_manifesto(depois_de_dois_patches: Path) -> None:
    assert (depois_de_dois_patches / "manifest.json").exists()


def test_a_varredura_ignora_arquivo_que_nao_e_do_indice(tarball_local: Path, destino: Path) -> None:
    """Só apaga o que casa com o padrão de nome do índice."""
    indexar(tarball_local, destino, "--game-version", ANTIGA)
    intruso = destino / "anotacoes.json"
    intruso.write_text("{}", encoding="utf-8")

    indexar(tarball_local, destino, "--game-version", VERSAO)
    assert intruso.exists(), "a varredura apagou arquivo que não é dela"


# --- observabilidade (T-12) ---------------------------------------------------------


def test_status_e_escrito_no_sucesso(tarball_local: Path, destino: Path) -> None:
    from lol_assets_schema.validators import validate_status

    indexar(tarball_local, destino)
    status = ler(destino, "status.json")

    validate_status(status)
    assert status["ok"] is True
    assert status["gameVersion"] == VERSAO
    assert status["counts"]["champions"] == 2
    assert status["bytes"]["index"] > 0
    assert status["source"]["caseMismatches"] > 0, "a fixture tem o campeão de caixa divergente"


def test_status_e_escrito_tambem_quando_falha(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """É o critério 1 do T-12: o relatório existe justamente quando dá errado."""
    from lol_assets_schema.validators import validate_status

    monkeypatch.setattr("lol_assets_indexer.limits.CATALOG_GZIP_LIMIT", 10)
    assert indexar(tarball_local, destino).exit_code != 0

    status = ler(destino, "status.json")
    validate_status(status)
    assert status["ok"] is False
    assert status["failure"]["kind"] == "BudgetExceededError"
    assert "RNF-03" in status["failure"]["message"]


def test_status_existe_mesmo_quando_a_falha_e_no_comeco(destino: Path, tmp_path: Path) -> None:
    """Pior caso: nem a versão foi resolvida."""
    vazio = tmp_path / "arquivo.tgz"
    vazio.write_bytes(b"")
    assert indexar(vazio, destino).exit_code != 0

    status = ler(destino, "status.json")
    assert status["ok"] is False
    assert "gameVersion" not in status


def test_o_status_nao_e_varrido_como_orfao(depois_de_dois_patches: Path) -> None:
    assert (depois_de_dois_patches / "status.json").exists()


def test_dry_run_nao_escreve_nem_status(tarball_local: Path, destino: Path) -> None:
    assert indexar(tarball_local, destino, "--dry-run").exit_code == 0
    assert not destino.exists(), "o --dry-run não escreve nada, nem relatório"


def test_o_resumo_do_job_e_escrito_onde_pedirem(
    tarball_local: Path, destino: Path, tmp_path: Path
) -> None:
    resumo = tmp_path / "summary.md"
    indexar(tarball_local, destino, "--summary", str(resumo))

    texto = resumo.read_text(encoding="utf-8")
    assert texto.startswith("## ✅ Indexação")
    assert "| `champion` |" in texto


def test_o_resumo_do_job_sai_pela_variavel_do_actions(
    tarball_local: Path, destino: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """É assim que o T-13 vai ligar isto, sem passar opção nenhuma."""
    resumo = tmp_path / "step-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resumo))
    indexar(tarball_local, destino)

    assert "## ✅ Indexação" in resumo.read_text(encoding="utf-8")


def test_o_resumo_de_falha_tambem_sai(
    tarball_local: Path, destino: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    resumo = tmp_path / "summary.md"
    monkeypatch.setattr("lol_assets_indexer.limits.INDEX_RAW_LIMIT", 100)
    indexar(tarball_local, destino, "--summary", str(resumo))

    texto = resumo.read_text(encoding="utf-8")
    assert texto.startswith("## ❌ Indexação")
    assert "RNF-05" in texto


def test_o_run_id_do_actions_entra_no_status(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_RUN_ID", "987654")
    indexar(tarball_local, destino)

    assert ler(destino, "status.json")["runId"] == "987654"


def test_nenhum_segredo_do_ambiente_aparece_no_status(
    tarball_local: Path, destino: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Critério 4 do T-12. O status é publicado junto com o índice."""
    segredo = "ghp_UmTokenBemLongoQueNaoPodeVazar"
    monkeypatch.setenv("GITHUB_TOKEN", segredo)
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "outra_credencial_bem_longa")
    indexar(tarball_local, destino)

    bruto = (destino / "status.json").read_text(encoding="utf-8")
    assert segredo not in bruto
    assert "outra_credencial_bem_longa" not in bruto


# --- o comando `check` do workflow (T-13) --------------------------------------------


@respx.mock
def test_check_diz_para_indexar_quando_nao_ha_indice(destino: Path, tmp_path: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(
        return_value=httpx.Response(200, json=[VERSAO, ANTIGA])
    )
    saida = tmp_path / "github_output"

    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv("GITHUB_OUTPUT", str(saida))
        resultado = runner.invoke(app, ["check", "--output", str(destino)])

    assert resultado.exit_code == 0
    assert "indexar" in resultado.output
    assert "needs_index=true" in saida.read_text(encoding="utf-8")


@respx.mock
def test_check_nao_baixa_nada(tarball_local: Path, destino: Path) -> None:
    """O ponto do ticket: "nada a fazer" custa segundos, não 2,39 GB."""
    indexar(tarball_local, destino)
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(200, json=[VERSAO]))
    tarball = respx.get(f"{DDRAGON}/cdn/dragontail-{VERSAO}.tgz")

    resultado = runner.invoke(app, ["check", "--output", str(destino)])

    assert resultado.exit_code == 0
    assert "nada a fazer" in resultado.output
    assert not tarball.called


@respx.mock
def test_check_falha_alto_se_a_fonte_estiver_fora(destino: Path) -> None:
    respx.get(f"{DDRAGON}/api/versions.json").mock(return_value=httpx.Response(500))
    assert runner.invoke(app, ["check", "--output", str(destino)]).exit_code != 0

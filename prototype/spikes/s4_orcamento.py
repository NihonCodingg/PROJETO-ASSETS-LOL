"""Spike S4 (decisao D4) — fechar o orcamento de armazenamento do RNF-05.

Emotes e ward skins eram os dois unicos buracos: contados, mas nunca medidos em
bytes. Este spike mede por amostragem, fecha tambem os dois buracos menores que
sobraram (loading vintage e emblemas de elo) e recompoe o orcamento inteiro de
uma versao a partir das medicoes de S1, S2 e S3.

Condicao de parada do ticket T-02: se o total projetado passar de 10 GB, o
resultado vai para docs/SPIKES.md e a Onda 1 nao comeca.

Uso:  python prototype/spikes/s4_orcamento.py
"""

from __future__ import annotations

import asyncio
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import (  # noqa: E402
    MAX_CONCURRENCY,
    RESULTS_DIR,
    Report,
    client,
    human_bytes,
    measure_url,
    request,
)

CDRAGON = "https://raw.communitydragon.org"
GAME_DATA = "plugins/rcp-be-lol-game-data/global/default"
ASSET_PREFIX = "/lol-game-data/assets/"
RIOT_STATIC = "https://static.developer.riotgames.com/docs/lol"

#: 10 GB do tier gratuito do R2; o indexador aborta antes, em 8 GB (RNF-05).
LIMITE_R2 = 10 * 1024**3
LIMITE_ABORTO = 8 * 1024**3

#: Amostra por categoria. O ticket pede >= 30.
TAMANHO_AMOSTRA = 40
SEMENTE = 20260903


def map_asset_path(raw: str) -> str | None:
    """Regra de §B.2.1, a mesma do S2."""
    if not raw or not raw.lower().startswith(ASSET_PREFIX):
        return None
    resto = raw[len(ASSET_PREFIX) :].lower()
    if not resto or resto.endswith("/"):
        return None
    return CDRAGON + "/latest/" + GAME_DATA + "/" + resto


def load(nome: str) -> dict | None:
    caminho = RESULTS_DIR / nome
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


async def medir_amostra(http, urls: list[str], rotulo: str) -> dict:
    """Mede uma amostra e devolve as estatisticas que sustentam a extrapolacao."""
    semaforo = asyncio.Semaphore(MAX_CONCURRENCY)
    medidas = await asyncio.gather(*(measure_url(http, u, semaforo) for u in urls))
    ok = [m for m in medidas if m.status < 400 and m.bytes]
    tamanhos = [m.bytes for m in ok]
    if not tamanhos:
        return {"rotulo": rotulo, "n": 0, "erro": "nenhuma amostra respondeu"}
    dimensoes: dict[str, int] = {}
    formatos: dict[str, int] = {}
    for m in ok:
        chave = f"{m.width}x{m.height}"
        dimensoes[chave] = dimensoes.get(chave, 0) + 1
        formatos[m.format] = formatos.get(m.format, 0) + 1
    return {
        "rotulo": rotulo,
        "n": len(ok),
        "n_tentadas": len(urls),
        "ausentes": len(medidas) - len(ok),
        "bytes_mediano": int(statistics.median(tamanhos)),
        "bytes_medio": int(statistics.fmean(tamanhos)),
        "bytes_min": min(tamanhos),
        "bytes_max": max(tamanhos),
        "dimensoes": dict(sorted(dimensoes.items(), key=lambda kv: -kv[1])[:5]),
        "formatos": formatos,
    }


async def medir_emotes(http) -> dict:
    resposta = await request(http, "GET", CDRAGON + "/latest/" + GAME_DATA + "/v1/summoner-emotes.json")
    entradas = resposta.json()
    caminhos = [u for e in entradas if (u := map_asset_path(e.get("inventoryIcon") or ""))]
    aleatorio = random.Random(SEMENTE)
    amostra = aleatorio.sample(caminhos, min(TAMANHO_AMOSTRA, len(caminhos)))
    stats = await medir_amostra(http, amostra, "emotes")
    stats["total_no_catalogo"] = len(entradas)
    stats["total_com_caminho"] = len(caminhos)
    stats["arquivos_projetados"] = len(caminhos)
    return stats


async def medir_wards(http) -> dict:
    """Ward skin tem DUAS imagens: a sentinela e a sombra."""
    resposta = await request(http, "GET", CDRAGON + "/latest/" + GAME_DATA + "/v1/ward-skins.json")
    entradas = resposta.json()
    caminhos: list[str] = []
    for e in entradas:
        for campo in ("wardImagePath", "wardShadowImagePath"):
            url = map_asset_path(e.get(campo) or "")
            if url:
                caminhos.append(url)
    aleatorio = random.Random(SEMENTE)
    amostra = aleatorio.sample(caminhos, min(TAMANHO_AMOSTRA, len(caminhos)))
    stats = await medir_amostra(http, amostra, "ward skins")
    stats["total_no_catalogo"] = len(entradas)
    stats["imagens_por_ward"] = round(len(caminhos) / max(len(entradas), 1), 2)
    stats["arquivos_projetados"] = len(caminhos)
    return stats


async def medir_emblemas_de_elo(http) -> dict:
    """§B.4: zip oficial da Riot. Um HEAD fecha o buraco sem baixar nada."""
    url = RIOT_STATIC + "/ranked-emblems-latest.zip"
    cabecalho = await request(http, "HEAD", url)
    return {
        "rotulo": "emblemas de elo",
        "url": url,
        "status": cabecalho.status_code,
        "bytes": int(cabecalho.headers.get("Content-Length", "0") or 0),
        "arquivos_projetados": None,
    }


def projetar_loading_vintage(s2: dict | None) -> dict:
    """S2 mediu 23 de 54 skins com loading vintage. Extrapola pela mesma proporcao."""
    if not s2:
        return {"rotulo": "loading vintage", "erro": "S2 ausente"}
    tamanhos: list[int] = []
    skins_medidas = 0
    com_vintage = 0
    for info in (s2.get("data", {}).get("cdragon") or {}).values():
        skins_medidas += info.get("skins_total", 0)
        for entrada in (info.get("por_tipo") or {}).get("skins[].loadScreenVintagePath", []):
            if entrada.get("status", 500) < 400 and entrada.get("bytes"):
                tamanhos.append(entrada["bytes"])
                com_vintage += 1
    if not tamanhos:
        return {"rotulo": "loading vintage", "erro": "sem amostra no S2"}
    return {
        "rotulo": "loading vintage",
        "n": len(tamanhos),
        "skins_medidas": skins_medidas,
        "proporcao_com_vintage": round(com_vintage / max(skins_medidas, 1), 3),
        "bytes_mediano": int(statistics.median(tamanhos)),
    }


def compor_orcamento(s1: dict | None, s3: dict | None, medidas: dict) -> dict:
    """Monta o orcamento de UMA versao, preferindo numero exato a extrapolacao."""
    linhas: list[dict] = []

    # 1) O que o tarball do ddragon entrega: numero EXATO, medido em 100% dos arquivos.
    grupos = ((s1 or {}).get("data", {}).get("tarball") or {}).get("por_grupo") or []
    em_escopo = {
        "img/champion": "square do campeao",
        "img/champion/splash": "splash_wide",
        "img/champion/centered": "splash_centered",
        "img/champion/loading": "loading",
        "img/champion/tiles": "tile",
        "img/item": "icone de item",
        "img/spell": "icone de habilidade e feitico",
        "img/passive": "icone de passiva",
        "img/profileicon": "icone de perfil",
        "img/map": "minimapa",
    }
    for grupo in grupos:
        nome = grupo["grupo"]
        rotulo = em_escopo.get(nome)
        if rotulo is None and nome.startswith("img/perk-images"):
            rotulo = "runas"
        if rotulo is None:
            continue
        linhas.append(
            {
                "categoria": rotulo,
                "fonte_do_numero": "S1 (tarball, exato)",
                "arquivos": grupo["arquivos"],
                "bytes": grupo["bytes"],
            }
        )

    # 2) Chromas: so existem no cdragon; numero do S3 (extrapolado da amostra do S2).
    for linha in ((s3 or {}).get("data", {}).get("extrapolacao") or {}).get("linhas", []):
        if linha["tipo"] == "skins[].chromas[].chromaPath":
            linhas.append(
                {
                    "categoria": "chromas",
                    "fonte_do_numero": "S3 (extrapolado)",
                    "arquivos": linha["unidades"],
                    "bytes": linha["bytes_origem"],
                }
            )

    # 3) Os buracos que este spike fecha.
    emotes = medidas["emotes"]
    if emotes.get("n"):
        linhas.append(
            {
                "categoria": "emotes",
                "fonte_do_numero": f"S4 (amostra de {emotes['n']})",
                "arquivos": emotes["arquivos_projetados"],
                "bytes": emotes["bytes_mediano"] * emotes["arquivos_projetados"],
            }
        )
    wards = medidas["wards"]
    if wards.get("n"):
        linhas.append(
            {
                "categoria": "ward skins",
                "fonte_do_numero": f"S4 (amostra de {wards['n']})",
                "arquivos": wards["arquivos_projetados"],
                "bytes": wards["bytes_mediano"] * wards["arquivos_projetados"],
            }
        )
    vintage = medidas["loading_vintage"]
    if vintage.get("bytes_mediano"):
        skins_totais = ((s3 or {}).get("data", {}).get("extrapolacao") or {}).get("skins", 0)
        arquivos = int(skins_totais * vintage["proporcao_com_vintage"])
        linhas.append(
            {
                "categoria": "loading vintage",
                "fonte_do_numero": "S4 (proporcao do S2)",
                "arquivos": arquivos,
                "bytes": vintage["bytes_mediano"] * arquivos,
            }
        )
    elo = medidas["emblemas"]
    if elo.get("bytes"):
        linhas.append(
            {
                "categoria": "emblemas de elo (zip oficial)",
                "fonte_do_numero": "S4 (Content-Length)",
                "arquivos": elo["arquivos_projetados"],
                "bytes": elo["bytes"],
            }
        )

    # O S1 agrupa por diretorio completo, entao as runas vem em ~85 linhas de 1 arquivo.
    # Agrega por categoria antes de somar, senao o relatorio fica ilegivel.
    agregado: dict[str, dict] = {}
    for linha in linhas:
        alvo = agregado.setdefault(
            linha["categoria"],
            {
                "categoria": linha["categoria"],
                "fonte_do_numero": linha["fonte_do_numero"],
                "arquivos": 0,
                "bytes": 0,
            },
        )
        alvo["arquivos"] += linha["arquivos"] or 0
        alvo["bytes"] += linha["bytes"]
    linhas = list(agregado.values())

    total = sum(linha["bytes"] for linha in linhas)
    for linha in linhas:
        linha["legivel"] = human_bytes(linha["bytes"])
        linha["pct_do_total"] = round(100 * linha["bytes"] / max(total, 1), 1)
    linhas.sort(key=lambda linha: -linha["bytes"])

    return {
        "linhas": linhas,
        "arquivos_total": sum(linha["arquivos"] or 0 for linha in linhas),
        "bytes_total": total,
        "total_legivel": human_bytes(total),
        "pct_do_tier_gratuito": round(100 * total / LIMITE_R2, 1),
        "limite_r2_bytes": LIMITE_R2,
        "limite_aborto_bytes": LIMITE_ABORTO,
        "cabe_em_10gb": total <= LIMITE_R2,
        "abaixo_do_aborto_de_8gb": total <= LIMITE_ABORTO,
        "maior_categoria": linhas[0]["categoria"] if linhas else None,
    }


async def main() -> None:
    s1, s2, s3 = load("s1-ddragon.json"), load("s2-cdragon.json"), load("s3-volume.json")
    if not (s1 and s2 and s3):
        print("S4 precisa dos resultados de S1, S2 e S3.", flush=True)
        return

    medidas: dict = {"loading_vintage": projetar_loading_vintage(s2)}
    async with client() as http:
        print("S4 - medindo emotes...", flush=True)
        medidas["emotes"] = await medir_emotes(http)
        print(f"  n={medidas['emotes']['n']} mediana={human_bytes(medidas['emotes']['bytes_mediano'])}")

        print("S4 - medindo ward skins...", flush=True)
        medidas["wards"] = await medir_wards(http)
        print(f"  n={medidas['wards']['n']} mediana={human_bytes(medidas['wards']['bytes_mediano'])}")

        print("S4 - conferindo o zip de emblemas de elo...", flush=True)
        medidas["emblemas"] = await medir_emblemas_de_elo(http)
        print(f"  HTTP {medidas['emblemas']['status']} · {human_bytes(medidas['emblemas']['bytes'])}")

    orcamento = compor_orcamento(s1, s3, medidas)
    caminho = Report(spike="s4-orcamento", data={"medidas": medidas, "orcamento": orcamento}).save()

    print("\n=== ORCAMENTO DE UMA VERSAO ===", flush=True)
    for linha in orcamento["linhas"]:
        print(
            f"  {linha['categoria']:<32} {str(linha['arquivos'] or '-'):>7} arq  "
            f"{linha['legivel']:>10}  {linha['pct_do_total']:>5}%  [{linha['fonte_do_numero']}]"
        )
    print(f"  {'TOTAL':<32} {orcamento['arquivos_total']:>7} arq  {orcamento['total_legivel']:>10}")
    print(
        f"\n  {orcamento['pct_do_tier_gratuito']}% do tier gratuito de 10 GB · "
        f"cabe={orcamento['cabe_em_10gb']} · abaixo do aborto de 8 GB={orcamento['abaixo_do_aborto_de_8gb']}"
    )
    print(f"\nS4 pronto: {caminho}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

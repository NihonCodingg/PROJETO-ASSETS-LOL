"""Spike S3 — volume real e politica de versoes.

Objetivo (KICKOFF §B.8): extrapolar S1+S2 para o catalogo inteiro usando
contagens reais (nao "170 campeoes / 1.700 skins" de memoria) e medir quanto a
conversao JPG -> PNG custa em bytes, que e o numero que decide a §A.4
("PNG sempre") e a politica de versoes da §B.6.

Depende de: results/s1-ddragon.json e results/s2-cdragon.json

Uso:  python prototype/spikes/s3_volume.py
"""

from __future__ import annotations

import asyncio
import io
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from common import (  # noqa: E402
    MAX_CONCURRENCY,
    RESULTS_DIR,
    Report,
    client,
    human_bytes,
    request,
)

CDRAGON = "https://raw.communitydragon.org"
GAME_DATA = "plugins/rcp-be-lol-game-data/global/default"


def load(name: str) -> dict | None:
    path = RESULTS_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


async def real_counts(http) -> dict:
    """Contagens reais do catalogo, medidas agora."""
    out: dict = {}
    for label, url in (
        ("skins", CDRAGON + "/latest/" + GAME_DATA + "/v1/skins.json"),
        ("champion_summary", CDRAGON + "/latest/" + GAME_DATA + "/v1/champion-summary.json"),
        ("items", CDRAGON + "/latest/" + GAME_DATA + "/v1/items.json"),
        ("profile_icons", CDRAGON + "/latest/" + GAME_DATA + "/v1/profile-icons.json"),
        ("summoner_emotes", CDRAGON + "/latest/" + GAME_DATA + "/v1/summoner-emotes.json"),
        ("ward_skins", CDRAGON + "/latest/" + GAME_DATA + "/v1/ward-skins.json"),
        ("perks", CDRAGON + "/latest/" + GAME_DATA + "/v1/perks.json"),
    ):
        response = await request(http, "GET", url)
        if response.status_code >= 400:
            out[label] = {"url": url, "status": response.status_code}
            continue
        payload = response.json()
        total = len(payload) if isinstance(payload, (list, dict)) else None
        entry: dict = {"url": url, "status": response.status_code, "total": total}
        if label == "skins" and isinstance(payload, dict):
            chromas = 0
            base = 0
            for skin in payload.values():
                chromas += len(skin.get("chromas", []) or [])
                if skin.get("isBase"):
                    base += 1
            entry["chromas"] = chromas
            entry["skins_base"] = base
        if label == "champion_summary" and isinstance(payload, list):
            # Alem do sentinela id=-1, a lista traz os campeoes do modo League
            # Classic com ids na faixa 60xxx. So os ids < 60000 sao campeoes reais.
            entry["campeoes"] = sum(1 for c in payload if 0 < c.get("id", -1) < 60000)
            entry["modo_classic"] = sum(1 for c in payload if c.get("id", -1) >= 60000)
        out[label] = entry
    return out


async def png_conversion_cost(http, urls: list[str]) -> dict:
    """Mede, em bytes, o custo real de reencodar os JPGs da fonte como PNG."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    amostras: list[dict] = []

    async def one(url: str) -> None:
        async with semaphore:
            response = await request(http, "GET", url)
            if response.status_code >= 400:
                return
            source = response.content
            try:
                with Image.open(io.BytesIO(source)) as image:
                    fmt = image.format
                    size = (image.width, image.height)
                    buffer = io.BytesIO()
                    image.convert("RGB").save(buffer, format="PNG", optimize=True)
            except Exception:
                return
            amostras.append(
                {
                    "url": url,
                    "formato_origem": fmt,
                    "w": size[0],
                    "h": size[1],
                    "bytes_origem": len(source),
                    "bytes_png": buffer.tell(),
                    "razao": round(buffer.tell() / max(len(source), 1), 3),
                }
            )

    await asyncio.gather(*(one(u) for u in urls))
    razoes = [a["razao"] for a in amostras]
    return {
        "amostras": amostras,
        "razao_mediana": round(statistics.median(razoes), 3) if razoes else None,
        "razao_media": round(statistics.fmean(razoes), 3) if razoes else None,
        "razao_min": min(razoes) if razoes else None,
        "razao_max": max(razoes) if razoes else None,
    }


def averages_by_type(s2: dict) -> dict:
    """Bytes medios por tipo de asset, a partir das medidas reais do S2."""
    buckets: dict[str, list[int]] = defaultdict(list)
    dims: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for info in (s2.get("data", {}).get("cdragon") or {}).values():
        for tipo, entradas in (info.get("por_tipo") or {}).items():
            for entrada in entradas:
                if entrada.get("status", 500) < 400 and entrada.get("bytes"):
                    buckets[tipo].append(entrada["bytes"])
                    dims[tipo].append((entrada.get("w", 0), entrada.get("h", 0)))
    return {
        tipo: {
            "amostras": len(valores),
            "bytes_medio": int(statistics.fmean(valores)),
            "bytes_mediano": int(statistics.median(valores)),
            "dimensao_mais_comum": max(set(dims[tipo]), key=dims[tipo].count),
        }
        for tipo, valores in sorted(buckets.items())
    }


def extrapolate(medias: dict, contagens: dict, conversao: dict) -> dict:
    """Extrapola o catalogo inteiro a partir das medias reais medidas no S2."""
    skins = (contagens.get("skins") or {}).get("total") or 0
    chromas = (contagens.get("skins") or {}).get("chromas") or 0
    campeoes = (contagens.get("champion_summary") or {}).get("campeoes") or 0

    razao_png = conversao.get("razao_mediana") or 1.0
    # Assets que ja sao PNG na fonte nao pagam custo de conversao.
    unidades = {
        "skins[].splashPath": (skins, "JPEG"),
        "skins[].uncenteredSplashPath": (skins, "JPEG"),
        "skins[].tilePath": (skins, "JPEG"),
        "skins[].loadScreenPath": (skins, "JPEG"),
        "skins[].chromas[].chromaPath": (chromas, "PNG"),
        "squarePortraitPath": (campeoes, "PNG"),
        "spells[].abilityIconPath": (campeoes * 4, "PNG"),
        "passive.abilityIconPath": (campeoes, "PNG"),
    }

    linhas = []
    total_origem = 0
    total_png = 0
    for tipo, (n, formato) in unidades.items():
        media = medias.get(tipo)
        if not media or not n:
            continue
        origem = media["bytes_mediano"] * n
        png = origem if formato == "PNG" else int(origem * razao_png)
        total_origem += origem
        total_png += png
        linhas.append(
            {
                "tipo": tipo,
                "formato_fonte": formato,
                "unidades": n,
                "bytes_medianos": media["bytes_mediano"],
                "dimensao": media["dimensao_mais_comum"],
                "bytes_origem": origem,
                "origem_legivel": human_bytes(origem),
                "bytes_png": png,
                "png_legivel": human_bytes(png),
            }
        )

    return {
        "campeoes": campeoes,
        "skins": skins,
        "chromas": chromas,
        "razao_png_usada": razao_png,
        "linhas": linhas,
        "total_origem_bytes": total_origem,
        "total_origem_legivel": human_bytes(total_origem),
        "total_png_bytes": total_png,
        "total_png_legivel": human_bytes(total_png),
    }


async def main() -> None:
    s1 = load("s1-ddragon.json")
    s2 = load("s2-cdragon.json")
    if s2 is None:
        print("S3 precisa do resultado do S2. Rode s2_cdragon.py antes.", flush=True)
        return

    medias = averages_by_type(s2)

    # amostra real de JPGs para medir o custo do PNG: splashes e tiles ja medidos no S2
    jpgs: list[str] = []
    for info in (s2.get("data", {}).get("cdragon") or {}).values():
        for entrada in info.get("detalhe", []):
            if entrada.get("format") == "JPEG" and entrada.get("status", 500) < 400:
                jpgs.append(entrada["url"])
    jpgs = sorted(set(jpgs))[:12]

    async with client() as http:
        print("S3 - contando o catalogo real...", flush=True)
        contagens = await real_counts(http)
        print(
            "  campeoes="
            + str((contagens.get("champion_summary") or {}).get("campeoes"))
            + " skins="
            + str((contagens.get("skins") or {}).get("total")),
            flush=True,
        )
        print("  medindo o custo de converter " + str(len(jpgs)) + " JPGs para PNG...", flush=True)
        conversao = await png_conversion_cost(http, jpgs)

    extrapolacao = extrapolate(medias, contagens, conversao)

    ddragon_recortes = ((s1 or {}).get("data", {}).get("tarball") or {}).get("recortes")

    result = {
        "contagens_reais": contagens,
        "medias_por_tipo": medias,
        "conversao_png": conversao,
        "extrapolacao": extrapolacao,
        "ddragon_recortes": ddragon_recortes,
    }
    path = Report(spike="s3-volume", data=result).save()
    print("S3 pronto: " + str(path), flush=True)
    print(json.dumps(extrapolacao, indent=2, ensure_ascii=False), flush=True)
    print(
        "razao PNG/JPG mediana: " + str(conversao.get("razao_mediana")),
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())

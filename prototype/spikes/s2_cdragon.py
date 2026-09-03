"""Spike S2 — amostra do Community Dragon.

Objetivo (KICKOFF §B.8): para Jax (24), Lux (99) e Nunu (20), partir de
`v1/champions/{key}.json`, descobrir todos os assets pelos caminhos que o
proprio JSON declara, medir dimensoes/formato/bytes e comparar com o ddragon.

Nao monta caminho na mao: aplica a regra de mapeamento de §B.2.1 sobre os
caminhos `/lol-game-data/assets/...` encontrados no JSON.

Uso:  python prototype/spikes/s2_cdragon.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import (  # noqa: E402
    MAX_CONCURRENCY,
    Report,
    client,
    measure_url,
    request,
)

CDRAGON = "https://raw.communitydragon.org"
DDRAGON = "https://ddragon.leagueoflegends.com"
GAME_DATA = "plugins/rcp-be-lol-game-data/global/default"
ASSET_PREFIX = "/lol-game-data/assets/"

CHAMPIONS = {24: "Jax", 99: "Lux", 20: "Nunu"}
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def map_asset_path(raw: str) -> str | None:
    """Regra de §B.2.1: /lol-game-data/assets/<Path> -> <game-data>/<path minusculo>."""
    if not raw.lower().startswith(ASSET_PREFIX):
        return None
    rest = raw[len(ASSET_PREFIX) :].lower()
    return CDRAGON + "/latest/" + GAME_DATA + "/" + rest


def walk_paths(node, trail: str = ""):
    """Percorre o JSON e devolve (caminho_no_json, valor) de tudo que parece asset."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from walk_paths(value, trail + "." + str(key) if trail else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_paths(value, trail + "[" + str(index) + "]")
    elif isinstance(node, str) and node.lower().endswith(IMAGE_SUFFIXES):
        yield trail, node


async def fetch_json(http, url: str):
    response = await request(http, "GET", url)
    if response.status_code >= 400:
        return None, response.status_code
    return response.json(), response.status_code


async def probe_directory_listing(http) -> dict:
    """Confere a afirmacao de §B.2.1: prefixar com `json/` lista o diretorio."""
    url = CDRAGON + "/json/latest/" + GAME_DATA + "/v1/"
    response = await request(http, "GET", url)
    body = response.json() if response.status_code < 400 else None
    return {
        "url": url,
        "status": response.status_code,
        "entradas": len(body) if isinstance(body, list) else None,
        "amostra": [e.get("name") for e in body[:15]] if isinstance(body, list) else None,
    }


async def collect_for_champion(http, key: int, name: str, semaphore) -> dict:
    """Todos os assets de um campeao, medidos de verdade."""
    champion_url = CDRAGON + "/latest/" + GAME_DATA + "/v1/champions/" + str(key) + ".json"
    payload, status = await fetch_json(http, champion_url)
    if payload is None:
        return {"key": key, "nome": name, "erro": "HTTP " + str(status), "url": champion_url}

    skins = payload.get("skins", []) or []
    declared: dict[str, list[str]] = {}
    unmapped: list[dict] = []
    for json_path, raw in walk_paths(payload):
        url = map_asset_path(raw)
        if url is None:
            unmapped.append({"json_path": json_path, "valor": raw})
            continue
        declared.setdefault(url, []).append(json_path)

    # Caminhos documentados em §B.2.3, montados por skinId para conferencia.
    documented: dict[str, list[str]] = {}
    base = CDRAGON + "/latest/" + GAME_DATA + "/v1/"
    documented.setdefault(base + "champion-icons/" + str(key) + ".png", []).append(
        "B.2.3 champion-icons"
    )
    for skin in skins:
        skin_id = skin.get("id")
        if skin_id is None:
            continue
        for template, label in (
            ("champion-tiles/{k}/{s}.jpg", "B.2.3 champion-tiles"),
            ("champion-splashes/{k}/{s}.jpg", "B.2.3 champion-splashes"),
            ("champion-splashes/uncentered/{k}/{s}.jpg", "B.2.3 champion-splashes/uncentered"),
        ):
            url = base + template.format(k=key, s=skin_id)
            documented.setdefault(url, []).append(label + " skin " + str(skin_id))

    todo = {**{u: list(v) for u, v in declared.items()}}
    for url, labels in documented.items():
        todo.setdefault(url, []).extend(labels)

    urls = sorted(todo)
    measurements = await asyncio.gather(*(measure_url(http, url, semaphore) for url in urls))

    por_tipo: dict[str, list[dict]] = {}
    for url, measurement in zip(urls, measurements, strict=True):
        for origem in todo[url]:
            # skins[3].splashPath -> skins[].splashPath; "B.2.3 x skin 24003" -> "B.2.3 x"
            tipo = re.sub(r"\[\d+\]", "[]", origem).split(" skin ")[0]
            por_tipo.setdefault(tipo, []).append(
                {
                    "url": url,
                    "status": measurement.status,
                    "format": measurement.format,
                    "w": measurement.width,
                    "h": measurement.height,
                    "bytes": measurement.bytes,
                    "mode": measurement.mode,
                }
            )

    # Os caminhos relativos (ex.: champion-abilities/0024/...) nao seguem a regra de
    # §B.2.1. Testamos a base natural (o mesmo v1/ de onde veio o JSON) e registramos.
    relativos = []
    for item in unmapped[:6]:
        url = base + item["valor"]
        medida = await measure_url(http, url, semaphore)
        relativos.append({"json_path": item["json_path"], "valor": item["valor"], **medida.__dict__})

    return {
        "key": key,
        "nome": name,
        "champion_json": champion_url,
        "relativos_testados": relativos,
        "skins_total": len(skins),
        "skins": [
            {
                "id": s.get("id"),
                "nome": s.get("name"),
                "isBase": s.get("isBase"),
                "chromas": len(s.get("chromas", []) or []),
            }
            for s in skins
        ],
        "assets_medidos": len(urls),
        "assets_ok": sum(1 for m in measurements if m.status < 400),
        "assets_ausentes": [m.url for m in measurements if m.status >= 400],
        "por_tipo": por_tipo,
        "caminhos_nao_mapeaveis": unmapped[:20],
        "detalhe": [m.__dict__ for m in measurements],
    }


async def ddragon_comparison(http, semaphore) -> dict:
    """Mede os equivalentes no ddragon para a comparacao de resolucao."""
    versions = (await request(http, "GET", DDRAGON + "/api/versions.json")).json()
    latest = versions[0]
    out: dict = {"versao": latest, "campeoes": {}}
    for key, name in CHAMPIONS.items():
        payload, status = await fetch_json(
            http, DDRAGON + "/cdn/" + latest + "/data/pt_BR/champion/" + name + ".json"
        )
        if payload is None:
            out["campeoes"][name] = {"erro": "HTTP " + str(status)}
            continue
        champion = payload["data"][name]
        skins = champion.get("skins", [])
        urls = [DDRAGON + "/cdn/" + latest + "/img/champion/" + name + ".png"]
        for skin in skins:
            num = skin.get("num")
            # `centered` e `tiles` nao estao em §B.1.3; apareceram no tarball do S1.
            for pasta in ("splash", "loading", "centered", "tiles"):
                urls.append(
                    DDRAGON + "/cdn/img/champion/" + pasta + "/" + name + "_" + str(num) + ".jpg"
                )
        measurements = await asyncio.gather(*(measure_url(http, u, semaphore) for u in urls))
        out["campeoes"][name] = {
            "key_ddragon": champion.get("key"),
            "skins_total": len(skins),
            "skins": [
                {"num": s.get("num"), "nome": s.get("name"), "chromas": s.get("chromas")}
                for s in skins
            ],
            "detalhe": [m.__dict__ for m in measurements],
        }
    return out


async def main() -> None:
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    result: dict = {}
    async with client() as http:
        print("S2 - conferindo a listagem de diretorio em JSON...", flush=True)
        result["listagem_json"] = await probe_directory_listing(http)
        print("  status " + str(result["listagem_json"]["status"]), flush=True)

        result["cdragon"] = {}
        for key, name in CHAMPIONS.items():
            print("  medindo " + name + " (" + str(key) + ") no cdragon...", flush=True)
            result["cdragon"][name] = await collect_for_champion(http, key, name, semaphore)
            info = result["cdragon"][name]
            print(
                "    "
                + str(info.get("assets_ok"))
                + "/"
                + str(info.get("assets_medidos"))
                + " assets respondidos",
                flush=True,
            )

        print("  medindo os equivalentes no ddragon...", flush=True)
        result["ddragon"] = await ddragon_comparison(http, semaphore)

    path = Report(spike="s2-cdragon", data=result).save()
    print("S2 pronto: " + str(path), flush=True)
    resumo = {
        nome: {
            "skins": info.get("skins_total"),
            "assets_ok": info.get("assets_ok"),
            "assets_medidos": info.get("assets_medidos"),
        }
        for nome, info in result["cdragon"].items()
    }
    print(json.dumps(resumo, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

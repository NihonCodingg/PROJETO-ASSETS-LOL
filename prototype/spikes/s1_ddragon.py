"""Spike S1 — amostra do Data Dragon.

Objetivo (KICKOFF §B.8): baixar o tarball do patch atual, medir as dimensões
reais de cada tipo de asset e medir o tamanho em disco de `data/{pt_BR,en_US}`
e de `img/`.

Uso:  python prototype/spikes/s1_ddragon.py
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import sys
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from common import (  # noqa: E402
    CACHE_DIR,
    MAX_CONCURRENCY,
    Report,
    client,
    human_bytes,
    measure_url,
    request,
)

DDRAGON = "https://ddragon.leagueoflegends.com"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


async def discover() -> dict:
    """Versões, idiomas, realm e tamanho dos tarballs — tudo medido, nada suposto."""
    out: dict = {}
    async with client() as http:
        versions = (await request(http, "GET", DDRAGON + "/api/versions.json")).json()
        out["versions_total"] = len(versions)
        out["versions_head"] = versions[:10]
        latest = versions[0]
        out["latest"] = latest

        languages = (await request(http, "GET", DDRAGON + "/cdn/languages.json")).json()
        out["languages_total"] = len(languages)
        out["pt_BR_disponivel"] = "pt_BR" in languages

        realm = (await request(http, "GET", DDRAGON + "/realms/br.json")).json()
        out["realm_br"] = {
            "v": realm.get("v"),
            "dd": realm.get("dd"),
            "l": realm.get("l"),
            "cdn": realm.get("cdn"),
        }

        tarballs = {}
        for name in ("dragontail-" + latest + ".tgz", "cdragontail-" + latest + ".tgz"):
            url = DDRAGON + "/cdn/" + name
            head = await request(http, "HEAD", url)
            tarballs[name] = {
                "url": url,
                "status": head.status_code,
                "bytes": int(head.headers.get("Content-Length", "0") or 0),
                "content_type": head.headers.get("Content-Type", ""),
            }
        out["tarballs"] = tarballs
    return out


async def download_tarball(url: str, destination: Path) -> dict:
    """Baixa em streaming, com cache local. Devolve tamanho e duração."""
    if destination.exists() and destination.stat().st_size > 0:
        return {"cached": True, "bytes": destination.stat().st_size, "seconds": 0.0}

    destination.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    total = 0
    async with client() as http:
        async with http.stream("GET", url) as response:
            response.raise_for_status()
            with destination.open("wb") as handle:
                async for chunk in response.aiter_bytes(1024 * 1024):
                    handle.write(chunk)
                    total += len(chunk)
                    if total % (64 * 1024 * 1024) < 1024 * 1024:
                        print("    ... " + human_bytes(total), flush=True)
    return {"cached": False, "bytes": total, "seconds": round(time.monotonic() - started, 1)}


def group_of(member_path: str) -> tuple[str, str]:
    """Classifica um membro do tarball em (versionado?, grupo)."""
    parts = member_path.split("/")
    versioned = "nao-versionado"
    if parts and VERSION_RE.match(parts[0]):
        versioned = "versionado"
        parts = parts[1:]
    group = "/".join(parts[:-1]) or "(raiz)"
    return versioned, group


def inspect_tarball(path: Path) -> dict:
    """Uma passada pelo tarball medindo tudo o que interessa."""
    counts: Counter = Counter()
    total_bytes: Counter = Counter()
    dimensions: dict = defaultdict(Counter)
    modes: dict = defaultdict(Counter)
    alpha_probe: dict = defaultdict(list)
    failures: Counter = Counter()
    examples: dict = {}

    started = time.monotonic()
    processed = 0
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            suffix = Path(member.name).suffix.lower()
            versioned, group = group_of(member.name)
            key = (versioned, group, suffix)
            counts[key] += 1
            total_bytes[key] += member.size
            examples.setdefault(key, member.name)
            processed += 1
            if processed % 10000 == 0:
                print("    ... " + str(processed) + " arquivos", flush=True)

            if suffix not in IMAGE_EXTS:
                continue
            handle = tar.extractfile(member)
            if handle is None:
                continue
            data = handle.read()
            try:
                with Image.open(io.BytesIO(data)) as image:
                    dimensions[key][(image.width, image.height)] += 1
                    modes[key][image.mode] += 1
                    if len(alpha_probe[key]) < 5 and image.mode in ("RGBA", "LA", "P"):
                        converted = image.convert("RGBA")
                        low, high = converted.getchannel("A").getextrema()
                        alpha_probe[key].append(
                            {"arquivo": member.name, "alpha_min": low, "alpha_max": high}
                        )
            except Exception as exc:  # imagem ilegivel e um dado, nao um erro fatal
                failures[group + suffix + ": " + type(exc).__name__] += 1

    groups = []
    for key, count in counts.most_common():
        versioned, group, suffix = key
        dims = dimensions.get(key, Counter())
        groups.append(
            {
                "versionado": versioned,
                "grupo": group,
                "ext": suffix,
                "arquivos": count,
                "bytes": total_bytes[key],
                "bytes_legivel": human_bytes(total_bytes[key]),
                "exemplo": examples[key],
                "dimensoes_top": [
                    {"w": w, "h": h, "arquivos": n} for (w, h), n in dims.most_common(5)
                ],
                "dimensoes_distintas": len(dims),
                "modos": dict(modes.get(key, Counter())),
                "alpha_amostra": alpha_probe.get(key, []),
            }
        )

    def sum_where(predicate) -> int:
        return sum(total_bytes[k] for k in total_bytes if predicate(k))

    return {
        "arquivos_total": processed,
        "bytes_total": sum(total_bytes.values()),
        "segundos": round(time.monotonic() - started, 1),
        "por_grupo": groups,
        "recortes": {
            "data_pt_BR": sum_where(lambda k: k[1].startswith("data/pt_BR")),
            "data_en_US": sum_where(lambda k: k[1].startswith("data/en_US")),
            "data_todos_idiomas": sum_where(lambda k: k[1].startswith("data/")),
            "img_versionado": sum_where(lambda k: k[0] == "versionado" and k[1].startswith("img")),
            "img_nao_versionado": sum_where(
                lambda k: k[0] == "nao-versionado" and k[1].startswith("img")
            ),
        },
        "falhas": dict(failures),
    }


async def crosscheck(latest: str) -> list[dict]:
    """Confere as URLs de §B.1.3 direto no CDN (o tarball pode nao ser tudo)."""
    urls = [
        DDRAGON + "/cdn/" + latest + "/img/champion/Jax.png",
        DDRAGON + "/cdn/img/champion/splash/Jax_0.jpg",
        DDRAGON + "/cdn/img/champion/loading/Jax_0.jpg",
        DDRAGON + "/cdn/" + latest + "/img/item/3031.png",
        DDRAGON + "/cdn/" + latest + "/img/spell/SummonerFlash.png",
        DDRAGON + "/cdn/" + latest + "/img/profileicon/1.png",
        DDRAGON + "/cdn/" + latest + "/img/map/map11.png",
        DDRAGON + "/cdn/img/perk-images/Styles/7201_Precision.png",
    ]
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    async with client() as http:
        results = await asyncio.gather(*(measure_url(http, url, semaphore) for url in urls))
    return [r.__dict__ for r in results]


async def main() -> None:
    print("S1 - descobrindo versoes e tarballs...", flush=True)
    discovery = await discover()
    latest = discovery["latest"]
    print("  patch mais recente: " + latest, flush=True)
    for name, info in discovery["tarballs"].items():
        print("  " + name + ": HTTP " + str(info["status"]) + " - " + human_bytes(info["bytes"]))

    tarball = discovery["tarballs"]["dragontail-" + latest + ".tgz"]
    result: dict = {"descoberta": discovery}

    if tarball["status"] < 400:
        destination = CACHE_DIR / ("dragontail-" + latest + ".tgz")
        print("  baixando " + human_bytes(tarball["bytes"]) + "...", flush=True)
        result["download"] = await download_tarball(tarball["url"], destination)
        print("  inspecionando o tarball (uma passada, mede tudo)...", flush=True)
        result["tarball"] = inspect_tarball(destination)
    else:
        result["tarball"] = {"erro": "HTTP " + str(tarball["status"]) + " - tarball indisponivel"}

    print("  conferindo as URLs individuais de B.1.3...", flush=True)
    result["crosscheck_cdn"] = await crosscheck(latest)

    path = Report(spike="s1-ddragon", data=result).save()
    print("S1 pronto: " + str(path), flush=True)
    print(json.dumps(result.get("tarball", {}).get("recortes", {}), indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

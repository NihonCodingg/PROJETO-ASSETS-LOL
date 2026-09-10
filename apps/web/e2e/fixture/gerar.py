"""Gera a fixture do e2e: imagens de verdade e um índice que as descreve.

**Determinístico de propósito.** O e2e não toca o ddragon nem o cdragon: um teste
que depende da rede de terceiros falha por motivo errado, e falha vermelho na CI
de quem não mexeu em nada. O que ele precisa provar — três cliques, bytes
idênticos ao `sha256`, PNG com as mesmas dimensões — não fica menos verdadeiro
com bytes de mentira.

As dimensões, sim, são as de verdade: 1280x720 no `splash_centered` e 128x128 no
`square` são o [ADR 0002] medido. Se alguém inverter os cortes, o e2e pega.

Rodar de novo depois de mexer aqui:

    uv run python apps/web/e2e/fixture/gerar.py
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
IMAGENS = AQUI / "imagens"
INDICE = AQUI / "indice"

#: Onde o servidor de fixture atende. Cross-origin em relação ao app, como o
#: ddragon é em produção — é isso que faz o canvas do RF-11 ser testado de fato.
BASE = "http://127.0.0.1:4321"

VERSAO = "16.18.1"

#: Dois campeões bastam para os três cliques e para a busca por skin.
CAMPEOES = [
    {"key": 24, "id": "Jax", "nome": "Jax", "titulo": "Grão-Mestre das Armas"},
    {"key": 99, "id": "Lux", "nome": "Lux", "titulo": "a Dama Luminosa"},
]

SKINS = [
    {"key": 24, "num": 0, "nome": "Jax", "base": True},
    {"key": 24, "num": 7, "nome": "Jax Deus da Guerra", "base": False},
    {"key": 99, "num": 0, "nome": "Lux", "base": True},
]


def desenhar(largura: int, altura: int, texto: str, formato: str) -> bytes:
    """Uma imagem legível a olho, para quando um teste falhar e alguém abrir."""
    modo = "RGB" if formato == "JPEG" else "RGBA"
    cor = (18, 22, 30) if modo == "RGB" else (18, 22, 30, 255)
    imagem = Image.new(modo, (largura, altura), cor)
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle([(4, 4), (largura - 5, altura - 5)], outline=(120, 200, 255), width=3)
    desenho.text((12, 12), f"{texto}\n{largura}x{altura}", fill=(230, 240, 255))
    buffer = io.BytesIO()
    imagem.save(buffer, format=formato, **({"quality": 88} if formato == "JPEG" else {}))
    return buffer.getvalue()


def escrever(nome: str, dados: bytes) -> dict[str, object]:
    (IMAGENS / nome).write_bytes(dados)
    return {"bytes": len(dados), "sha256": hashlib.sha256(dados).hexdigest()}


def asset(
    *,
    asset_id: str,
    tipo: str,
    nome_do_arquivo: str,
    largura: int,
    altura: int,
    formato: str,
    nomes: dict[str, str],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    medido = escrever(nome_do_arquivo, desenhar(largura, altura, asset_id, formato.upper()))
    registro: dict[str, object] = {
        "id": asset_id,
        "type": tipo,
        "category": "champion",
        "names": nomes,
        "source": "ddragon",
        "sourceUrl": f"{BASE}/imagens/{nome_do_arquivo}",
        "fileName": nome_do_arquivo,
        "width": largura,
        "height": altura,
        "format": formato,
        "hasAlpha": formato == "png",
        **medido,
    }
    registro.update(extra or {})
    return registro


def main() -> None:
    IMAGENS.mkdir(parents=True, exist_ok=True)
    INDICE.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, object]] = []
    for campeao in CAMPEOES:
        chave, cid = campeao["key"], campeao["id"]
        comum = {"championKey": chave, "championId": cid}
        assets.append(
            asset(
                asset_id=f"square:{chave}",
                tipo="square",
                nome_do_arquivo=f"{cid}_square.png",
                largura=128,
                altura=128,
                formato="png",
                nomes={"pt_BR": campeao["nome"]},
                extra=comum,
            )
        )
        for skin in [s for s in SKINS if s["key"] == chave]:
            num = skin["num"]
            sufixo = f"{num:03d}"
            de_skin = {
                **comum,
                "skinId": chave * 1000 + num,
                "skinNum": num,
                "isBaseSkin": skin["base"],
            }
            # ADR 0002: o centrado é 1280x720 e o aberto é 1215x717. Nunca o contrário.
            assets.append(
                asset(
                    asset_id=f"splash_centered:{chave}{sufixo}",
                    tipo="splash_centered",
                    nome_do_arquivo=f"{cid}_{sufixo}_splash_centered.jpg",
                    largura=1280,
                    altura=720,
                    formato="jpeg",
                    nomes={"pt_BR": skin["nome"]},
                    extra=de_skin,
                )
            )
            assets.append(
                asset(
                    asset_id=f"splash_wide:{chave}{sufixo}",
                    tipo="splash_wide",
                    nome_do_arquivo=f"{cid}_{sufixo}_splash_wide.jpg",
                    largura=1215,
                    altura=717,
                    formato="jpeg",
                    nomes={"pt_BR": skin["nome"]},
                    extra=de_skin,
                )
            )
            assets.append(
                asset(
                    asset_id=f"tile:{chave}{sufixo}",
                    tipo="tile",
                    nome_do_arquivo=f"{cid}_{sufixo}_tile.jpg",
                    largura=380,
                    altura=380,
                    formato="jpeg",
                    nomes={"pt_BR": skin["nome"]},
                    extra=de_skin,
                )
            )

    por_id = {a["id"]: a for a in assets}
    catalogo = {
        "schemaVersion": "1.2.0",
        "gameVersion": VERSAO,
        "generatedAt": "2026-09-09T00:00:00Z",
        "champions": [
            {
                "championKey": c["key"],
                "championId": c["id"],
                "names": {"pt_BR": c["nome"]},
                "title": {"pt_BR": c["titulo"]},
                "tags": ["Fighter"] if c["id"] == "Jax" else ["Mage", "Support"],
                "skinCount": sum(1 for s in SKINS if s["key"] == c["key"]),
                "baseSkinId": c["key"] * 1000,
                "thumbnailUrl": por_id[f"square:{c['key']}"]["sourceUrl"],
            }
            for c in CAMPEOES
        ],
        "skins": [
            {
                "skinId": s["key"] * 1000 + s["num"],
                "skinNum": s["num"],
                "championKey": s["key"],
                "names": {"pt_BR": s["nome"]},
                "isBase": s["base"],
                "thumbnailUrl": por_id[f"tile:{s['key']}{s['num']:03d}"]["sourceUrl"],
            }
            for s in SKINS
        ],
    }

    fatia = {
        "schemaVersion": "1.2.0",
        "gameVersion": VERSAO,
        "category": "champion",
        "generatedAt": "2026-09-09T00:00:00Z",
        "assets": assets,
    }

    (INDICE / "catalog-e2e.json").write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (INDICE / "index-champion-e2e.json").write_text(
        json.dumps(fatia, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifesto = {
        "schemaVersion": "1.2.0",
        # Recente de propósito: o aviso do T-31 não pode aparecer e atrapalhar.
        "generatedAt": "2026-09-09T00:00:00Z",
        "currentVersion": VERSAO,
        "generation": {"indexer": 3, "categories": ["champion"]},
        "versions": [
            {
                "gameVersion": VERSAO,
                "indexedAt": "2026-09-09T00:00:00Z",
                "assetsCopied": False,
                "catalog": {
                    "url": "catalog-e2e.json",
                    "champions": len(CAMPEOES),
                    "skins": len(SKINS),
                    "bytes": (INDICE / "catalog-e2e.json").stat().st_size,
                },
                "totalAssets": len(assets),
                "totalBytes": sum(int(a["bytes"]) for a in assets),
                "shards": [
                    {
                        "category": "champion",
                        "url": "index-champion-e2e.json",
                        "assets": len(assets),
                        "bytes": (INDICE / "index-champion-e2e.json").stat().st_size,
                    }
                ],
            }
        ],
    }
    (INDICE / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"{len(assets)} assets, {len(list(IMAGENS.iterdir()))} imagens")


if __name__ == "__main__":
    main()

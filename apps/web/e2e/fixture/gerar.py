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
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
IMAGENS = AQUI / "imagens"
INDICE = AQUI / "indice"

#: Onde o servidor de fixture atende. Cross-origin em relação ao app, como o
#: ddragon é em produção — é isso que faz o canvas do RF-11 ser testado de fato.
BASE = "http://127.0.0.1:4321"

VERSAO = "16.18.1"


@dataclass(frozen=True, slots=True)
class Campeao:
    key: int
    champion_id: str
    nome: str
    titulo: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Skin:
    key: int
    num: int
    nome: str
    base: bool


#: Dois campeões bastam para os três cliques e para a busca por skin.
CAMPEOES = (
    Campeao(24, "Jax", "Jax", "Grão-Mestre das Armas", ("Fighter",)),
    Campeao(99, "Lux", "Lux", "a Dama Luminosa", ("Mage", "Support")),
)

SKINS = (
    Skin(24, 0, "Jax", True),
    Skin(24, 7, "Jax Deus da Guerra", False),
    Skin(99, 0, "Lux", True),
)

#: Itens com as etiquetas que o T-21 escreve de verdade — é o que faz a navegação
#: por categoria e os filtros do T-24 terem o que filtrar no e2e.
#:
#: São **220**, e o número não é decorativo: acima do `LIMITE_DE_VIRTUALIZACAO`
#: de 200 a lista vira scroller virtual, e é justamente essa a que já quebrou
#: duas vezes por medir altura zero num pai errado. Com três itens o e2e passava
#: sem nunca exercitar o caminho virtual.
_NOMEADOS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("1001", "Botas de Velocidade", ("compravel", "mapa:sr", "mapa:aram", "classe:boots")),
    ("3031", "Gume do Infinito", ("compravel", "mapa:sr", "classe:criticalstrike")),
    ("2052", "Petisco de Poro", ("compravel", "mapa:aram", "classe:consumable")),
)

_CLASSES = ("damage", "health", "armor", "mana", "boots", "consumable")
ITENS: tuple[tuple[str, str, tuple[str, ...]], ...] = _NOMEADOS + tuple(
    # Todos compráveis e no SR, porque é assim que a categoria `item` **abre**
    # (§B.1.6): o filtro padrão precisa deixar mais de 200 na tela para o
    # caminho virtual ser exercitado. Metade também é de ARAM, para o filtro de
    # mapa continuar tendo o que filtrar.
    (
        str(4000 + i),
        f"Item de Teste {i}",
        ("compravel", "mapa:sr", *(("mapa:aram",) if i % 2 else ()), f"classe:{_CLASSES[i % 6]}"),
    )
    for i in range(220 - len(_NOMEADOS))
)


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
        chave, cid = campeao.key, campeao.champion_id
        comum: dict[str, object] = {"championKey": chave, "championId": cid}
        assets.append(
            asset(
                asset_id=f"square:{chave}",
                tipo="square",
                nome_do_arquivo=f"{cid}_square.png",
                largura=128,
                altura=128,
                formato="png",
                nomes={"pt_BR": campeao.nome},
                extra=comum,
            )
        )
        for skin in [s for s in SKINS if s.key == chave]:
            num = skin.num
            sufixo = f"{num:03d}"
            de_skin: dict[str, object] = {
                **comum,
                "skinId": chave * 1000 + num,
                "skinNum": num,
                "isBaseSkin": skin.base,
            }
            # Chroma só na skin base do Jax: o suficiente para o e2e provar o
            # RF-06 (não aparece sem alguém pedir) e a ordem do `Escape`.
            if chave == 24 and num == 0:
                for chroma in (9, 10):
                    assets.append(
                        asset(
                            asset_id=f"chroma:{chave}{chroma:03d}",
                            tipo="chroma",
                            nome_do_arquivo=f"Chroma_{chave}{chroma:03d}.png",
                            largura=270,
                            altura=303,
                            formato="png",
                            nomes={"pt_BR": f"{skin.nome} chroma {chroma}"},
                            extra={
                                **comum,
                                "skinId": chave * 1000 + chroma,
                                "skinNum": chroma,
                                "parentSkinNum": num,
                            },
                        )
                    )

            # ADR 0002: o centrado é 1280x720 e o aberto é 1215x717. Nunca o contrário.
            assets.append(
                asset(
                    asset_id=f"splash_centered:{chave}{sufixo}",
                    tipo="splash_centered",
                    nome_do_arquivo=f"{cid}_{sufixo}_splash_centered.jpg",
                    largura=1280,
                    altura=720,
                    formato="jpeg",
                    nomes={"pt_BR": skin.nome},
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
                    nomes={"pt_BR": skin.nome},
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
                    nomes={"pt_BR": skin.nome},
                    extra=de_skin,
                )
            )

    # Uma segunda categoria: sem ela o e2e não passa pela navegação por
    # categoria nem pelos filtros do T-24, que são metade da tela.
    itens: list[dict[str, object]] = []
    for indice, (item_id, nome, etiquetas) in enumerate(ITENS):
        # Os três nomeados ficam em 64x64 como o ddragon serve; os de volume
        # ficam em 16x16, porque o que eles provam é a **contagem**, não o pixel.
        lado = 64 if indice < len(_NOMEADOS) else 16
        registro = asset(
            asset_id=f"item_icon:{item_id}",
            tipo="item_icon",
            nome_do_arquivo=f"Item_{item_id}.png",
            largura=lado,
            altura=lado,
            formato="png",
            nomes={"pt_BR": nome},
            extra={"itemId": int(item_id), "refId": item_id, "tags": list(etiquetas)},
        )
        registro["category"] = "item"
        itens.append(registro)

    por_id = {a["id"]: a for a in assets}
    catalogo = {
        "schemaVersion": "1.2.0",
        "gameVersion": VERSAO,
        "generatedAt": "2026-09-09T00:00:00Z",
        "champions": [
            {
                "championKey": c.key,
                "championId": c.champion_id,
                "names": {"pt_BR": c.nome},
                "title": {"pt_BR": c.titulo},
                "tags": list(c.tags),
                "skinCount": sum(1 for s in SKINS if s.key == c.key),
                "baseSkinId": c.key * 1000,
                "thumbnailUrl": por_id[f"square:{c.key}"]["sourceUrl"],
            }
            for c in CAMPEOES
        ],
        "skins": [
            {
                "skinId": s.key * 1000 + s.num,
                "skinNum": s.num,
                "championKey": s.key,
                "names": {"pt_BR": s.nome},
                "isBase": s.base,
                "thumbnailUrl": por_id[f"tile:{s.key}{s.num:03d}"]["sourceUrl"],
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
    (INDICE / "index-item-e2e.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.2.0",
                "gameVersion": VERSAO,
                "category": "item",
                "generatedAt": "2026-09-09T00:00:00Z",
                "assets": itens,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    manifesto = {
        "schemaVersion": "1.2.0",
        # Recente de propósito: o aviso do T-31 não pode aparecer e atrapalhar.
        "generatedAt": "2026-09-09T00:00:00Z",
        "currentVersion": VERSAO,
        "generation": {"indexer": 3, "categories": ["champion", "item"]},
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
                "totalAssets": len(assets) + len(itens),
                "totalBytes": sum(cast("int", a["bytes"]) for a in [*assets, *itens]),
                "shards": [
                    {
                        "category": "champion",
                        "url": "index-champion-e2e.json",
                        "assets": len(assets),
                        "bytes": (INDICE / "index-champion-e2e.json").stat().st_size,
                    },
                    {
                        "category": "item",
                        "url": "index-item-e2e.json",
                        "assets": len(itens),
                        "bytes": (INDICE / "index-item-e2e.json").stat().st_size,
                    },
                ],
            }
        ],
    }
    (INDICE / "manifest.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"{len(assets) + len(itens)} assets, {len(list(IMAGENS.iterdir()))} imagens")


if __name__ == "__main__":
    main()

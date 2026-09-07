"""Peças compartilhadas pelos testes do indexador.

O tarball de mentira vive aqui porque tanto o teste da varredura quanto o da CLI
precisam dele — e montar dois seria garantir que divergissem.
"""

from __future__ import annotations

import io
import json
import tarfile
from typing import Any

import pytest
from lol_assets_indexer.adapters.tarball import TarballScan, scan_tarball
from PIL import Image

VERSAO = "16.17.1"


def imagem(largura: int, altura: int, formato: str, *, alfa: bool = False) -> bytes:
    modo = "RGBA" if alfa else "RGB"
    cor = (10, 20, 30, 0) if alfa else (10, 20, 30)
    buffer = io.BytesIO()
    Image.new(modo, (largura, altura), cor).save(buffer, format=formato)
    return buffer.getvalue()


def ficha_de_campeao(champion_id: str, chave: str, nome: str) -> dict[str, Any]:
    return {
        "data": {
            champion_id: {
                "id": champion_id,
                "key": chave,
                "name": nome,
                "title": "o Grão-Mestre das Armas",
                "tags": ["Fighter"],
                "passive": {"name": "Mestre das Armas", "image": {"full": f"{champion_id}_P.png"}},
                "spells": [
                    {"name": f"{nome} Q", "image": {"full": f"{champion_id}Q.png"}},
                    {"name": f"{nome} W", "image": {"full": f"{champion_id}W.png"}},
                ],
                "skins": [
                    {"id": f"{chave}000", "num": 0, "name": "default"},
                    {"id": f"{chave}004", "num": 4, "name": f"{nome} Deus da Guerra"},
                    # chroma: tem `parentSkin`, então NÃO é skin — KICKOFF §B.1.4
                    {"id": f"{chave}018", "num": 18, "name": "Chroma", "parentSkin": 4},
                ],
            }
        }
    }


def montar_membros() -> dict[str, bytes]:
    """Um caso de cada coisa que importa, por caminho dentro do tarball."""
    membros: dict[str, bytes] = {}

    def json_de(documento: Any) -> bytes:
        return json.dumps(documento).encode("utf-8")

    for idioma in ("pt_BR", "en_US"):
        membros[f"{VERSAO}/data/{idioma}/champion/Jax.json"] = json_de(
            ficha_de_campeao("Jax", "24", "Jax")
        )
        membros[f"{VERSAO}/data/{idioma}/item.json"] = json_de(
            {"data": {"3031": {"name": "Gume do Infinito"}}}
        )
        membros[f"{VERSAO}/data/{idioma}/summoner.json"] = json_de(
            {"data": {"SummonerFlash": {"name": "Flash", "image": {"full": "SummonerFlash.png"}}}}
        )
        membros[f"{VERSAO}/data/{idioma}/runesReforged.json"] = json_de(
            [
                {
                    "id": 8000,
                    "name": "Precisão",
                    "icon": "perk-images/Styles/7201_Precision.png",
                    "slots": [
                        {
                            "runes": [
                                {
                                    "id": 8005,
                                    "name": "Ataque Certeiro",
                                    "icon": "perk-images/Styles/Precision/PressTheAttack.png",
                                }
                            ]
                        }
                    ],
                }
            ]
        )

    # --- dentro do escopo ---
    membros[f"{VERSAO}/img/champion/Jax.png"] = imagem(128, 128, "PNG")
    membros[f"{VERSAO}/img/passive/Jax_P.png"] = imagem(64, 64, "PNG")
    membros[f"{VERSAO}/img/spell/JaxQ.png"] = imagem(64, 64, "PNG")
    membros[f"{VERSAO}/img/spell/JaxW.png"] = imagem(64, 64, "PNG")
    membros[f"{VERSAO}/img/spell/SummonerFlash.png"] = imagem(64, 64, "PNG")
    membros[f"{VERSAO}/img/item/3031.png"] = imagem(64, 64, "PNG")
    membros[f"{VERSAO}/img/profileicon/1.png"] = imagem(300, 300, "PNG")
    membros[f"{VERSAO}/img/map/map11.png"] = imagem(512, 512, "PNG")
    membros["img/perk-images/Styles/7201_Precision.png"] = imagem(32, 32, "PNG", alfa=True)
    membros["img/perk-images/Styles/Precision/PressTheAttack.png"] = imagem(
        256, 256, "PNG", alfa=True
    )
    for num in (0, 4):
        membros[f"img/champion/centered/Jax_{num}.jpg"] = imagem(1280, 720, "JPEG")
        membros[f"img/champion/splash/Jax_{num}.jpg"] = imagem(1215, 717, "JPEG")
        membros[f"img/champion/loading/Jax_{num}.jpg"] = imagem(308, 560, "JPEG")
        membros[f"img/champion/tiles/Jax_{num}.jpg"] = imagem(380, 380, "JPEG")
    # o chroma tem arquivo de splash no tarball, mas NÃO pode virar registro
    membros["img/champion/centered/Jax_18.jpg"] = imagem(1280, 720, "JPEG")

    # --- fora do escopo: 44 % do peso do tarball real (S1) ---
    membros[f"{VERSAO}/img/tft-champion/x.png"] = imagem(256, 128, "PNG")
    membros[f"{VERSAO}/img/tft-item/y.png"] = imagem(128, 128, "PNG")
    membros["img/challenges-images/z.png"] = imagem(256, 256, "PNG", alfa=True)
    membros[f"{VERSAO}/img/mission/w.png"] = imagem(502, 176, "PNG")
    membros[f"{VERSAO}/img/sprite/champion0.png"] = imagem(480, 144, "PNG")
    membros[f"{VERSAO}/img/mode/classic/champion/Jade_Ahri.png"] = imagem(128, 128, "PNG")
    membros[f"{VERSAO}/data/th_TH/champion.json"] = json_de({"data": {}})

    return membros


def montar_tarball(membros: dict[str, bytes]) -> io.BytesIO:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for nome, dados in membros.items():
            info = tarfile.TarInfo(name=nome)
            info.size = len(dados)
            tar.addfile(info, io.BytesIO(dados))
    buffer.seek(0)
    return buffer


@pytest.fixture(scope="session")
def membros() -> dict[str, bytes]:
    """Os bytes que entraram no tarball — a referência para conferir a medição."""
    return montar_membros()


@pytest.fixture(scope="session")
def tarball_bytes(membros: dict[str, bytes]) -> bytes:
    return montar_tarball(membros).getvalue()


@pytest.fixture(scope="session")
def scan(tarball_bytes: bytes) -> TarballScan:
    return scan_tarball(io.BytesIO(tarball_bytes), VERSAO)

"""Varredura do tarball do ddragon — uma passada, tudo medido.

O `dragontail-{versão}.tgz` tem 2,39 GB e 34.305 arquivos (S1). Baixá-lo é uma
requisição em vez de ~15 mil, e é por isso que ele existe.

Desde o [ADR 0012] o indexador **não copia** nada: ele abre cada imagem só para
medir dimensão, formato, canal alfa, bytes e sha256, e descarta os bytes em
seguida. O pico de memória é uma imagem por vez mais os registros acumulados —
cabe folgado no runner do Actions.

A ordem dos membros num tar não é garantida, então a varredura junta tudo em
memória e a montagem dos registros acontece depois, no `records.py`.
"""

from __future__ import annotations

import json
import logging
import re
import tarfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import IO, Any

from lol_assets_indexer.imaging import MeasuredImage, UnsupportedImageFormatError, measure

logger = logging.getLogger(__name__)

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")

#: Diretórios de imagem que a v1 usa. Medidos no S1; o que não está aqui é
#: descartado sem ser aberto — são 44 % do peso de imagem do tarball.
IN_SCOPE_IMAGE_DIRS = (
    "img/champion/",
    "img/item/",
    "img/spell/",
    "img/passive/",
    "img/profileicon/",
    "img/perk-images/",
    "img/map/",
)

#: Explicitamente fora: TFT, challenges, missões, sprites e o modo Classic.
OUT_OF_SCOPE_PREFIXES = (
    "img/tft",
    "img/challenges-images",
    "img/mission",
    "img/sprite",
    "img/mode/",
    "img/bg/",
    "img/global/",
    "img/item-modifiers",
)

#: Os JSONs de `data/` que a v1 lê, por idioma.
IN_SCOPE_DATA_FILES = (
    "champion.json",
    "item.json",
    "summoner.json",
    "profileicon.json",
    "runesReforged.json",
    "map.json",
)

LANGUAGES = ("pt_BR", "en_US")


@dataclass
class TarballScan:
    """O que uma passada pelo tarball produz."""

    game_version: str
    #: `{idioma: {arquivo: conteúdo}}` — ex.: `data["pt_BR"]["champion.json"]`.
    data: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: `{idioma: {championId: ficha}}`, de `data/{idioma}/champion/{Id}.json`.
    champions: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: Caminho relativo (sem a versão) → medição. Ex.: `img/champion/Jax.png`.
    images: dict[str, MeasuredImage] = field(default_factory=dict)
    #: Arquivos vistos no tarball, incluindo os JSONs de `data/`.
    files: int = 0
    skipped: int = 0
    unreadable: dict[str, int] = field(default_factory=dict)
    #: Caminho pedido → caminho real, quando só a caixa diverge. Ver `resolve`.
    case_mismatches: dict[str, str] = field(default_factory=dict)

    #: Índice em minúsculas, montado sob demanda pelo `resolve`.
    _por_minusculas: dict[str, str] = field(default_factory=dict, repr=False)

    def image(self, relative_path: str) -> MeasuredImage | None:
        return self.images.get(relative_path)

    def resolve(self, relative_path: str) -> tuple[str, MeasuredImage] | None:
        """Acha a imagem tolerando divergência de caixa, e devolve o caminho real.

        O ddragon chama o campeão de `Fiddlesticks` em `data/` e de `FiddleSticks`
        em `img/champion/*/`. São 13 skins que sumiriam do índice se a busca fosse
        só exata — e a URL precisa ser a do arquivo que existe, não a deduzida do
        `championId`, senão aponta para um 404.
        """
        exata = self.images.get(relative_path)
        if exata is not None:
            return relative_path, exata
        if not self._por_minusculas:
            self._por_minusculas = {caminho.lower(): caminho for caminho in self.images}
        real = self._por_minusculas.get(relative_path.lower())
        if real is None:
            return None
        # Anotado, não logado: são 52 arquivos por patch, e um resumo no fim vale
        # mais do que 52 linhas iguais no meio da varredura.
        self.case_mismatches[relative_path] = real
        return real, self.images[real]

    def images_under(self, prefix: str) -> Iterator[tuple[str, MeasuredImage]]:
        for path, measured in self.images.items():
            if path.startswith(prefix):
                yield path, measured


def strip_version(member_path: str) -> str:
    """`16.17.1/img/champion/Jax.png` → `img/champion/Jax.png`.

    O tarball mistura caminhos versionados e não versionados; o resto do código
    só quer o caminho relativo.
    """
    parts = member_path.split("/")
    if parts and VERSION_RE.match(parts[0]):
        return "/".join(parts[1:])
    return member_path


def is_in_scope_image(relative_path: str) -> bool:
    if not relative_path.lower().endswith(IMAGE_SUFFIXES):
        return False
    if relative_path.startswith(OUT_OF_SCOPE_PREFIXES):
        return False
    return relative_path.startswith(IN_SCOPE_IMAGE_DIRS)


def data_target(relative_path: str) -> tuple[str, str] | None:
    """Devolve `(idioma, nome)` para os JSONs de `data/` que interessam."""
    parts = relative_path.split("/")
    if len(parts) < 3 or parts[0] != "data" or parts[1] not in LANGUAGES:
        return None
    language = parts[1]
    if len(parts) == 3 and parts[2] in IN_SCOPE_DATA_FILES:
        return language, parts[2]
    if len(parts) == 4 and parts[2] == "champion":
        return language, f"champion/{parts[3]}"
    return None


def scan_tarball(stream: IO[bytes], game_version: str) -> TarballScan:
    """Uma passada. Lê cada arquivo no máximo uma vez e não guarda bytes."""
    scan = TarballScan(game_version=game_version)
    scan.data = {language: {} for language in LANGUAGES}
    scan.champions = {language: {} for language in LANGUAGES}
    processed = 0

    # `r|gz` é streaming puro: não faz seek, então serve para um fileobj de rede
    # ou de disco sem carregar o arquivo inteiro.
    with tarfile.open(fileobj=stream, mode="r|gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            processed += 1
            relative = strip_version(member.name)

            alvo = data_target(relative)
            if alvo is not None:
                handle = tar.extractfile(member)
                if handle is None:
                    continue
                language, nome = alvo
                documento = json.loads(handle.read().decode("utf-8"))
                if nome.startswith("champion/"):
                    champion_id = nome.removeprefix("champion/").removesuffix(".json")
                    # O ddragon embrulha em {"data": {"<Id>": {...}}}; guardamos a
                    # ficha já desembrulhada, que é o que o resto do código quer.
                    ficha = documento.get("data", {}).get(champion_id)
                    if ficha is not None:
                        scan.champions[language][champion_id] = ficha
                else:
                    scan.data[language][nome] = documento
                continue

            if not is_in_scope_image(relative):
                scan.skipped += 1
                continue

            handle = tar.extractfile(member)
            if handle is None:
                continue
            data = handle.read()
            try:
                scan.images[relative] = measure(data)
            except (UnsupportedImageFormatError, OSError, ValueError) as erro:
                chave = f"{relative.rsplit('/', 1)[0]}: {type(erro).__name__}"
                scan.unreadable[chave] = scan.unreadable.get(chave, 0) + 1
            del data  # os bytes morrem aqui — ADR 0012

    scan.files = processed
    logger.info(
        "tarball varrido",
        extra={
            "arquivos": processed,
            "imagens": len(scan.images),
            "descartadas": scan.skipped,
            "ilegiveis": sum(scan.unreadable.values()),
        },
    )
    return scan

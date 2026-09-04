"""Medição de imagem. Lê, nunca escreve.

O ADR 0001 diz que o indexador serve os bytes de origem e nunca re-encoda. Por
isso este módulo só abre a imagem para descobrir dimensão, formato e canal alfa —
e há um teste que falha se aparecer uma chamada de escrita aqui dentro.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Literal

from PIL import Image

ImageFormat = Literal["png", "jpeg"]

_FORMAT_ALIASES = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png"}


class UnsupportedImageFormatError(ValueError):
    """Formato fora do contrato: o índice só declara `png` e `jpeg`."""


@dataclass(frozen=True, slots=True)
class MeasuredImage:
    """O que o contrato precisa saber sobre um arquivo, medido dele mesmo."""

    width: int
    height: int
    format: ImageFormat
    has_alpha: bool
    bytes: int
    sha256: str


def measure(data: bytes) -> MeasuredImage:
    """Mede os bytes recebidos. Não os transforma."""
    with Image.open(io.BytesIO(data)) as image:
        raw_format = (image.format or "").lower()
        image_format = _FORMAT_ALIASES.get(raw_format)
        if image_format is None:
            raise UnsupportedImageFormatError(
                f"formato {raw_format!r} não faz parte do contrato (só png e jpeg)"
            )
        has_alpha = _has_real_alpha(image)
        width, height = image.width, image.height

    return MeasuredImage(
        width=width,
        height=height,
        format=image_format,  # type: ignore[arg-type]
        has_alpha=has_alpha,
        bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def _has_real_alpha(image: Image.Image) -> bool:
    """Modo com alfa não basta: o S1 mediu PNGs RGBA totalmente opacos.

    O que importa para o ADR 0001 é se existe pixel translúcido de verdade — é
    isso que decide se o asset pode ou não virar JPEG.
    """
    if image.mode not in {"RGBA", "LA", "PA", "P"} and "transparency" not in image.info:
        return False
    alpha = image.convert("RGBA").getchannel("A")
    # `getextrema()` devolve (min, max) numa banda só, mas a tipagem do Pillow
    # também cobre imagens multibanda, onde cada item é uma tupla.
    minimum = alpha.getextrema()[0]
    if isinstance(minimum, tuple):
        minimum = minimum[0]
    return bool(minimum < 255)

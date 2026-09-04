"""Nomes previsíveis — §6.2 da Spec e §A.4 item 4 do KICKOFF.

O nome que o usuário vê no disco e a chave no bucket saem daqui, e de mais lugar
nenhum. A extensão é sempre a do formato de ORIGEM: o PNG convertido no navegador
troca só a extensão, no cliente (ADR 0001).
"""

from __future__ import annotations

from lol_assets_schema.models import AssetCategory, AssetType

#: Tipos que existem por skin e por isso levam o número da skin no nome.
SKIN_SCOPED_TYPES = frozenset(
    {"splash_centered", "splash_wide", "loading", "loading_vintage", "tile", "chroma"}
)

_EXTENSION = {"png": "png", "jpeg": "jpg"}


def file_extension(image_format: str) -> str:
    """`jpeg` no contrato vira `.jpg` no disco, que é o que o editor espera."""
    try:
        return _EXTENSION[image_format]
    except KeyError as erro:
        raise ValueError(f"formato sem extensão definida: {image_format!r}") from erro


def champion_file_name(
    champion_id: str,
    asset_type: AssetType,
    image_format: str,
    *,
    skin_num: int | None = None,
) -> str:
    """`Jax_square.png` para o campeão; `Jax_004_splash_centered.jpg` para a skin."""
    extension = file_extension(image_format)
    if asset_type in SKIN_SCOPED_TYPES:
        if skin_num is None:
            raise ValueError(f"{asset_type} é por skin e exige skin_num")
        return f"{champion_id}_{skin_num:03d}_{asset_type}.{extension}"
    return f"{champion_id}_{asset_type}.{extension}"


def storage_key(game_version: str, category: AssetCategory, file_name: str) -> str:
    """`{versão}/{categoria}/{nome}` — §8 da Spec."""
    return f"{game_version}/{category}/{file_name}"


def asset_id(asset_type: AssetType, natural_key: str | int) -> str:
    """Identidade estável entre versões: `splash_centered:24004`."""
    return f"{asset_type}:{natural_key}"


def skin_id(champion_key: int, skin_num: int) -> int:
    """`{championKey}{skinNum:03d}` — a chave natural da skin (KICKOFF §B.7.1)."""
    return champion_key * 1000 + skin_num

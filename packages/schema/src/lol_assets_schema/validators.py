"""Validação contra o JSON Schema, que é a fonte de verdade do contrato.

Os modelos Pydantic impõem as mesmas regras, mas validar aqui é o que garante que
o documento publicado no bucket está conforme — inclusive se alguém montar o
dicionário à mão em vez de passar pelo modelo.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from lol_assets_schema import CATALOG_SCHEMA, MANIFEST_SCHEMA, SHARD_SCHEMA


@lru_cache(maxsize=8)
def _validator(schema_path: Path) -> Draft202012Validator:
    documento = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(documento)
    return Draft202012Validator(documento)


def validate_shard(document: Any) -> None:
    """Levanta `jsonschema.ValidationError` se a fatia não estiver conforme."""
    _validator(SHARD_SCHEMA).validate(document)


def validate_catalog(document: Any) -> None:
    """Levanta `jsonschema.ValidationError` se o catálogo não estiver conforme."""
    _validator(CATALOG_SCHEMA).validate(document)


def validate_manifest(document: Any) -> None:
    """Levanta `jsonschema.ValidationError` se o manifesto não estiver conforme."""
    _validator(MANIFEST_SCHEMA).validate(document)

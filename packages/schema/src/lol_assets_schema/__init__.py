"""Contrato compartilhado entre indexer, API e web.

O JSON Schema em `schemas/` é a fonte de verdade. Os modelos Pydantic e os tipos
TypeScript são gerados a partir dele (ticket da etapa 6); até lá este pacote
expõe os arquivos e a versão do contrato.
"""

from pathlib import Path

__all__ = [
    "ALIASES_FILE",
    "CATALOG_SCHEMA",
    "EXAMPLES_DIR",
    "MANIFEST_SCHEMA",
    "SCHEMA_DIR",
    "SCHEMA_VERSION",
    "SHARD_SCHEMA",
    "__version__",
]

__version__ = "1.1.0"

#: Versão do contrato do índice. Muda junto com um ADR (regra 12).
SCHEMA_VERSION = "1.1.0"

# src/lol_assets_schema/__init__.py -> src -> raiz do pacote.
# Assume instalação editável, que é como o workspace do uv instala os membros.
_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_DIR = _ROOT / "schemas"
MANIFEST_SCHEMA = SCHEMA_DIR / "index-manifest.schema.json"
#: Projeção de navegação (campeões) e busca (skins). Ver ADR 0010.
CATALOG_SCHEMA = SCHEMA_DIR / "catalog.schema.json"
SHARD_SCHEMA = SCHEMA_DIR / "index-shard.schema.json"

#: Apelidos de busca mantidos à mão. Ampliar = editar o arquivo (ADR 0009).
ALIASES_FILE = _ROOT / "data" / "champion-aliases.json"

#: Fixture do contrato: um retrato medido do patch 16.17.1. Usada pelos testes
#: dos dois lados — Python e front — para as duas pontas andarem em paralelo.
EXAMPLES_DIR = _ROOT / "examples"

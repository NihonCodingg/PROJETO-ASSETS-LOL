"""Contrato compartilhado entre indexer, API e web.

O JSON Schema completo do índice e os modelos Pydantic derivados dele chegam
com a Spec (etapa 4). Por enquanto este pacote só carrega a versão do contrato.
"""

__all__ = ["SCHEMA_VERSION", "__version__"]

__version__ = "0.0.0"

#: Versão do contrato do índice. Muda junto com um ADR (regra 12).
SCHEMA_VERSION = "0.0.0"

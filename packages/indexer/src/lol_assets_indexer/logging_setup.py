"""Log estruturado: uma linha JSON por evento.

Sem servidor para instrumentar, o log da indexação é metade da observabilidade
(§11 da Spec). Cada linha carrega o contexto da execução — `gameVersion` e a
fonte — para que um evento isolado ainda diga de que patch está falando.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

#: Campos que o `logging` já põe em todo registro e que não são contexto nosso.
_RESERVED = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}

_context: dict[str, Any] = {}


def bind(**values: Any) -> None:
    """Contexto que passa a acompanhar todo evento seguinte."""
    _context.update(values)


def clear_context() -> None:
    _context.clear()


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for chave, valor in _context.items():
            if not hasattr(record, chave):
                setattr(record, chave, valor)
        return True


class JsonLineFormatter(logging.Formatter):
    """Uma linha, um objeto JSON. Nada de texto livre para alguém ter que parsear."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "event": record.getMessage(),
            "logger": record.name,
        }
        payload.update(
            {
                chave: valor
                for chave, valor in record.__dict__.items()
                if chave not in _RESERVED and not chave.startswith("_")
            }
        )
        if record.exc_info:
            payload["error"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure(level: int = logging.INFO) -> None:
    """Substitui os handlers da raiz: um só, JSON, em stderr."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonLineFormatter())
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    for existente in list(root.handlers):
        root.removeHandler(existente)
    root.addHandler(handler)
    root.setLevel(level)

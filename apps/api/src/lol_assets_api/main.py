"""Aplicação FastAPI.

Só `/health` existe por enquanto. `/versions`, `/index` e a geração de zips
chegam com os tickets da etapa 6, depois que a Spec definir os contratos.
"""

from typing import Literal, TypedDict

from fastapi import FastAPI

from lol_assets_api import __version__

app = FastAPI(title="lol-assets API", version=__version__)


class HealthResponse(TypedDict):
    status: Literal["ok"]
    version: str


@app.get("/health")
def health() -> HealthResponse:
    """Liveness probe usada pelo host e pelos testes de fumaça."""
    return {"status": "ok", "version": __version__}

"""Configuração da API opcional (T-32).

Tudo tem padrão que funciona sem nenhuma variável de ambiente: a API é peça de
portfólio ([ADR 0006](../../../../docs/adr/0006-api-como-componente-opcional.md))
e precisa subir com um comando, não com um manual.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#: `apps/api/src/lol_assets_api/settings.py` -> ... -> raiz do repositório.
_RAIZ = Path(__file__).resolve().parents[4]


class ApiSettings(BaseSettings):
    """Lida do ambiente com prefixo `API_`, como o `.env.example` documenta."""

    model_config = SettingsConfigDict(env_prefix="API_", extra="ignore")

    #: `0.0.0.0` porque quem publica a porta é o compose, não o processo.
    host: str = "0.0.0.0"
    port: int = 8000

    #: De onde o índice é lido.
    #:
    #: **Do disco, não de um bucket.** O ticket original dizia "leitura do
    #: bucket, com MinIO no compose"; o [ADR 0012] tirou o storage do projeto e
    #: não sobrou bucket nenhum para ler. O que existe é o diretório que o
    #: indexador escreve e que o app serve — e é ele que a API lê.
    index_dir: Path = _RAIZ / "apps" / "web" / "public" / "indice"

    #: O front zipa no cliente (T-25). Este limite é da API, para ela sozinha.
    zip_max_items: int = 500

    #: A API não tem origem própria para servir; quem chama é `curl` ou o Swagger.
    cors_origins: str = "http://localhost:3000"

    @property
    def origens(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

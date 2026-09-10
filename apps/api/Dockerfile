# A API opcional do T-32, num contêiner que sobe com um comando.
#
# Sem MinIO e sem bucket: o ADR 0012 tirou o storage do projeto, e o que a API
# lê é o diretório do índice, montado como volume pelo compose. Um contêiner que
# precisasse de outro para responder /health não seria "opcional" coisa nenhuma.

FROM python:3.12-slim AS base

# `uv` porque é o que o repositório usa; a imagem oficial dele é só o binário.
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# As dependências primeiro, e o código depois: mexer numa rota não reinstala nada.
COPY pyproject.toml uv.lock ./
COPY packages/schema/pyproject.toml packages/schema/
COPY packages/indexer/pyproject.toml packages/indexer/
COPY apps/api/pyproject.toml apps/api/
RUN uv sync --frozen --no-install-workspace --package lol-assets-api

COPY packages/ packages/
COPY apps/api/ apps/api/
RUN uv sync --frozen --package lol-assets-api

ENV PATH="/app/.venv/bin:$PATH" \
    API_INDEX_DIR=/indice

EXPOSE 8000

# `--host 0.0.0.0` porque quem publica a porta é o compose, não o processo.
CMD ["uvicorn", "lol_assets_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

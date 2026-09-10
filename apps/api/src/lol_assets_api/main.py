"""A API opcional (T-32) — quatro rotas, e nada do produto depende dela.

O [ADR 0006](../../../../docs/adr/0006-api-como-componente-opcional.md) é
explícito: isto é peça de portfólio. O site inteiro funciona com esta API
desligada, e há teste de arquitetura garantindo que ninguém a chame do front por
distração. Derrubar este processo não quebra nenhum teste do `apps/web`.

**Não há bucket para ler.** O ticket original falava em MinIO e leitura de
storage; o [ADR 0012](../../../../docs/adr/0012-onde-guardar-os-assets.md) tirou
o storage do projeto. O que existe é o diretório que o indexador escreve, e é
dele que estas rotas leem.

O `POST /zip` monta no servidor o que o T-25 monta no cliente. Ele existe para
mostrar o outro caminho, não para ser usado: com o front zipando no navegador,
uma API que baixa 500 arquivos por requisição seria a coisa mais cara do sistema.
"""

from __future__ import annotations

import io
import zipfile
from typing import Annotated, Literal, TypedDict

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from lol_assets_indexer.http import IndexerSettings, SourceClient
from lol_assets_schema.models import Asset, IndexManifest, IndexShard
from pydantic import BaseModel, Field

from lol_assets_api import __version__
from lol_assets_api.indice import Indice, IndiceIndisponivelError
from lol_assets_api.settings import ApiSettings

settings = ApiSettings()
indice = Indice(settings.index_dir)

app = FastAPI(
    title="lol-assets API",
    version=__version__,
    description=(
        "Componente **opcional** (ADR 0006). O site funciona inteiro sem ela; "
        "esta API existe para mostrar o caminho de back-end da mesma arquitetura."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origens,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class HealthResponse(TypedDict):
    status: Literal["ok"]
    version: str


def indice_atual() -> Indice:
    """Injetável: o teste troca o diretório sem mexer em variável global."""
    return indice


Dep = Annotated[Indice, Depends(indice_atual)]


@app.get("/health")
def health() -> HealthResponse:
    """Liveness probe usada pelo host e pelos testes de fumaça."""
    return {"status": "ok", "version": __version__}


# `exclude_none`: campo opcional ausente no arquivo tem que sair ausente aqui.
# Devolver `"assetsBaseUrl": null` faria a resposta divergir do documento que ela
# promete ser — e o critério de aceite compara os dois.
@app.get("/versions", response_model=IndexManifest, response_model_exclude_none=True)
def versions(indice: Dep) -> IndexManifest:
    """O `manifest.json`, tal e qual.

    Devolver o mesmo documento, e não uma projeção, é o que faz esta rota ser
    verificável: o critério de aceite compara com o arquivo.
    """
    try:
        return indice.manifesto()
    except IndiceIndisponivelError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro


@app.get(
    "/index/{game_version}/{category}",
    response_model=IndexShard,
    response_model_exclude_none=True,
)
def index(game_version: str, category: str, indice: Dep) -> IndexShard:
    try:
        return indice.fatia(game_version, category)
    except KeyError as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from erro
    except IndiceIndisponivelError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro


class ZipRequest(BaseModel):
    game_version: str | None = Field(
        default=None,
        description="Vazio = a versão corrente do manifesto.",
    )
    ids: list[str] = Field(min_length=1)


async def _montar(assets: list[Asset]) -> tuple[bytes, list[str]]:
    """Busca os bytes nas fontes e monta o zip. Falha de um não derruba o lote.

    Mesma decisão do T-25, pelo mesmo motivo: abortar 500 arquivos por causa de
    um 404 é hostil. O que não veio entra num `FALHAS.txt` dentro do zip.
    """
    faltando: list[str] = []
    buffer = io.BytesIO()
    # `ZIP_STORED`: JPEG e PNG já vêm comprimidos, e deflatar de novo gasta CPU
    # para economizar ~0%.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as pacote:
        async with SourceClient(IndexerSettings()) as client:
            for asset in assets:
                try:
                    pacote.writestr(asset.file_name, await client.get_bytes(asset.source_url))
                except Exception as erro:
                    faltando.append(f"{asset.file_name}\t{type(erro).__name__}\t{asset.source_url}")
        if faltando:
            pacote.writestr("FALHAS.txt", "\n".join(faltando) + "\n")
    return buffer.getvalue(), faltando


@app.post(
    "/zip",
    responses={
        413: {"description": "Mais ids do que o limite da instância."},
        404: {"description": "Nenhum dos ids existe na versão pedida."},
    },
)
async def zip_de_selecao(pedido: ZipRequest, indice: Dep) -> Response:
    """O que o T-25 faz no navegador, feito aqui. Ver o cabeçalho do módulo."""
    if len(pedido.ids) > settings.zip_max_items:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"{len(pedido.ids)} ids acima do limite de {settings.zip_max_items} desta instância",
        )

    try:
        versao = pedido.game_version or indice.versao_atual()
        assets = indice.assets_por_id(versao, pedido.ids)
    except KeyError as erro:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(erro)) from erro
    except IndiceIndisponivelError as erro:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(erro)) from erro

    if not assets:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "nenhum dos ids existe nesta versão")

    conteudo, faltando = await _montar(assets)
    return Response(
        content=conteudo,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="lol-assets-{versao}.zip"',
            # Quem chamou merece saber sem precisar abrir o arquivo.
            "X-Assets-Incluidos": str(len(assets) - len(faltando)),
            "X-Assets-Falharam": str(len(faltando)),
        },
    )

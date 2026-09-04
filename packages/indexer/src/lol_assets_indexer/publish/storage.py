"""Publicação no bucket — e a ordem que torna a publicação atômica sem transação.

O `manifest.json` é o único arquivo de nome fixo e o único ponto de invalidação
(§9 da Spec). Ele é o **último** a subir e o **primeiro** a ser lido: enquanto ele
não muda, o site continua servindo a versão antiga, íntegra.

Este módulo impõe essa ordem por código. Publicar o manifesto antes das fatias, ou
uma fatia cujos assets ainda não subiram, levanta exceção — não fica para a
revisão de PR notar.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from lol_assets_schema.models import Catalog, CatalogRef, IndexManifest, IndexShard, ShardRef
from lol_assets_schema.validators import validate_catalog, validate_manifest, validate_shard

if TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)

#: §9 da Spec. Conteúdo novo = nome novo, então tudo com hash é imutável.
CACHE_IMMUTABLE = "max-age=31536000, immutable"
#: O manifesto é o único ponto de invalidação, então tem TTL curto.
CACHE_MANIFEST = "max-age=300, stale-while-revalidate=86400"

MANIFEST_KEY = "manifest.json"

_CONTENT_TYPES = {
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".zip": "application/zip",
}


class PublicationError(RuntimeError):
    """A ordem de publicação foi violada."""


def content_type_for(key: str) -> str:
    return _CONTENT_TYPES.get(Path(key).suffix.lower(), "application/octet-stream")


def _canonical_json(document: Any) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def hashed_name(prefix: str, payload: bytes, suffix: str = ".json") -> str:
    """`catalog-1a2b3c4d5e6f.json` — o hash no nome é o que permite cache imutável."""
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:12]}{suffix}"


class ObjectStore(Protocol):
    """O mínimo que a publicação precisa de um bucket."""

    def put(self, key: str, data: bytes, *, content_type: str, cache_control: str) -> None: ...

    def get(self, key: str) -> bytes: ...


@dataclass
class LocalObjectStore:
    """Destino do `--dry-run`: uma árvore em disco, sem nenhuma chamada de rede."""

    root: Path
    metadata: dict[str, dict[str, str]] = field(default_factory=dict)

    def put(self, key: str, data: bytes, *, content_type: str, cache_control: str) -> None:
        destino = self.root / key
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(data)
        self.metadata[key] = {"content_type": content_type, "cache_control": cache_control}

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()


@dataclass
class S3ObjectStore:
    """Cloudflare R2 por API compatível com S3."""

    client: S3Client
    bucket: str

    def put(self, key: str, data: bytes, *, content_type: str, cache_control: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl=cache_control,
        )

    def get(self, key: str) -> bytes:
        resposta = self.client.get_object(Bucket=self.bucket, Key=key)
        return bytes(resposta["Body"].read())


class Publisher:
    """Publica na ordem certa e recusa a ordem errada."""

    def __init__(self, store: ObjectStore) -> None:
        self._store = store
        self._published: set[str] = set()

    @property
    def published_keys(self) -> frozenset[str]:
        return frozenset(self._published)

    # --- assets ---------------------------------------------------------------

    def publish_asset(self, storage_key: str, data: bytes) -> str:
        """Sobe os bytes de origem. Sem re-encode — ADR 0001."""
        self._put(storage_key, data, CACHE_IMMUTABLE)
        return storage_key

    # --- índice ---------------------------------------------------------------

    def publish_catalog(self, catalog: Catalog) -> CatalogRef:
        """A projeção de navegação e busca (ADR 0010)."""
        documento = catalog.model_dump(by_alias=True, exclude_none=True, mode="json")
        validate_catalog(documento)
        payload = _canonical_json(documento)
        key = hashed_name("catalog", payload)
        self._put(key, payload, CACHE_IMMUTABLE)
        return CatalogRef(
            url=key,
            champions=len(catalog.champions),
            skins=len(catalog.skins),
            bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )

    def publish_shard(self, shard: IndexShard) -> ShardRef:
        """Uma fatia de assets. Recusa se algum asset dela ainda não subiu."""
        faltando = sorted(
            asset.storage_key
            for asset in shard.assets
            if asset.storage_key and asset.storage_key not in self._published
        )
        if faltando:
            raise PublicationError(
                f"fatia {shard.category!r} aponta para {len(faltando)} asset(s) que não foram "
                f"publicados; o primeiro é {faltando[0]!r}. Publique os assets antes da fatia."
            )

        documento = shard.model_dump(by_alias=True, exclude_none=True, mode="json")
        validate_shard(documento)
        payload = _canonical_json(documento)
        key = hashed_name(f"index-{shard.category}", payload)
        self._put(key, payload, CACHE_IMMUTABLE)
        return ShardRef(
            category=shard.category,
            url=key,
            assets=len(shard.assets),
            bytes=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )

    # --- manifesto: sempre por último ----------------------------------------

    def publish_manifest(self, manifest: IndexManifest) -> str:
        """Só sobe depois de tudo que a versão atual referencia já estar no bucket."""
        atual = next(
            (v for v in manifest.versions if v.game_version == manifest.current_version),
            None,
        )
        if atual is None:
            raise PublicationError(
                f"o manifesto declara currentVersion={manifest.current_version!r} "
                "mas não traz essa versão em versions[]"
            )

        referenciados = [atual.catalog.url, *(shard.url for shard in atual.shards)]
        referenciados += [zip_ref.url for zip_ref in (atual.zips or [])]
        faltando = [url for url in referenciados if url not in self._published]
        if faltando:
            raise PublicationError(
                "o manifesto não pode subir antes do que ele referencia. "
                f"Faltam {len(faltando)}: {', '.join(faltando[:3])}"
            )

        documento = manifest.model_dump(by_alias=True, exclude_none=True, mode="json")
        validate_manifest(documento)
        self._put(MANIFEST_KEY, _canonical_json(documento), CACHE_MANIFEST)
        return MANIFEST_KEY

    def read_manifest(self) -> IndexManifest:
        """Releitura do bucket — é o que o T-11 exige antes de remover qualquer coisa."""
        return IndexManifest.model_validate(json.loads(self._store.get(MANIFEST_KEY)))

    # --- interno --------------------------------------------------------------

    def _put(self, key: str, data: bytes, cache_control: str) -> None:
        self._store.put(
            key,
            data,
            content_type=content_type_for(key),
            cache_control=cache_control,
        )
        self._published.add(key)
        # Só chave e tamanho: nada de credencial, nada de conteúdo.
        logger.info(
            "objeto publicado",
            extra={"storage_key": key, "bytes": len(data), "cache_control": cache_control},
        )

"""Construção do cliente do bucket a partir da configuração.

Separado do `storage.py` de propósito: aquele módulo não deve saber de onde vêm
credenciais, e este é o único lugar que as toca. Nenhuma delas aparece em log.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import boto3

from lol_assets_indexer.http import IndexerSettings
from lol_assets_indexer.publish.storage import S3ObjectStore

if TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_s3.client import S3Client


class MissingBucketCredentialsError(RuntimeError):
    """Faltam as variáveis do bucket. Rode com `--dry-run` ou configure o R2."""


def build_store(settings: IndexerSettings) -> S3ObjectStore:
    """Cliente S3 apontando para o R2. Falha alto se faltar credencial."""
    if not settings.has_bucket_credentials():
        raise MissingBucketCredentialsError(
            "faltam S3_ENDPOINT_URL, S3_ACCESS_KEY_ID e S3_SECRET_ACCESS_KEY. "
            "Sem elas só é possível publicar com --dry-run."
        )
    client: S3Client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )
    return S3ObjectStore(client=client, bucket=settings.s3_bucket)

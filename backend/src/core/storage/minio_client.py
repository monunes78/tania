"""
Wrapper MinIO — upload, download e remoção de objetos.
"""
import io
from typing import Optional
from minio import Minio
from minio.error import S3Error
import structlog

from src.config import settings

log = structlog.get_logger()

_client: Optional[Minio] = None


def get_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def ensure_bucket(bucket: str) -> None:
    client = get_client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        log.info("minio.bucket_created", bucket=bucket)


def upload_bytes(bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Faz upload de bytes e retorna o caminho object_name."""
    client = get_client()
    ensure_bucket(bucket)
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    log.info("minio.upload", bucket=bucket, object=object_name, size=len(data))
    return object_name


def download_bytes(bucket: str, object_name: str) -> bytes:
    """Baixa objeto e retorna bytes."""
    client = get_client()
    response = client.get_object(bucket_name=bucket, object_name=object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_object(bucket: str, object_name: str) -> None:
    client = get_client()
    try:
        client.remove_object(bucket_name=bucket, object_name=object_name)
        log.info("minio.delete", bucket=bucket, object=object_name)
    except S3Error as e:
        log.warning("minio.delete_error", bucket=bucket, object=object_name, error=str(e))

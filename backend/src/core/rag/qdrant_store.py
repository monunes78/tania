"""
Wrapper Qdrant — cria coleções, upsert de vetores e busca semântica.
"""
from typing import List, Optional
import uuid
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    ScoredPoint,
)

from src.config import settings
from src.core.rag.embedder import VECTOR_DIM

log = structlog.get_logger()

_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
    return _client


def ensure_collection(collection_name: str) -> None:
    """Cria a coleção se não existir."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        log.info("qdrant.collection_created", collection=collection_name)


def upsert_chunks(
    collection_name: str,
    document_id: str,
    chunks: List[str],
    vectors: List[List[float]],
    metadata: Optional[dict] = None,
) -> int:
    """
    Faz upsert de todos os chunks de um documento.
    Remove chunks antigos do mesmo document_id primeiro.
    Retorna quantidade de pontos inseridos.
    """
    client = get_client()
    ensure_collection(collection_name)

    # Remove versão anterior do documento
    delete_document(collection_name, document_id)

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        payload = {
            "document_id": document_id,
            "chunk_index": i,
            "text": chunk,
            **(metadata or {}),
        }
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload,
            )
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)
        log.info("qdrant.upsert", collection=collection_name, points=len(points))

    return len(points)


def search(
    collection_name: str,
    query_vector: List[float],
    top_k: int = 5,
    score_threshold: float = 0.35,
    filter_document_ids: Optional[List[str]] = None,
) -> List[ScoredPoint]:
    """Busca semântica. Retorna chunks com score >= threshold."""
    client = get_client()

    qdrant_filter = None
    if filter_document_ids:
        # Filtra por lista de document_ids permitidos (controle de acesso)
        qdrant_filter = Filter(
            should=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=doc_id),
                )
                for doc_id in filter_document_ids
            ]
        )

    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return results


def delete_document(collection_name: str, document_id: str) -> None:
    """Remove todos os chunks de um documento da coleção."""
    client = get_client()
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
    except Exception:
        pass  # Coleção pode não existir ainda


def delete_collection(collection_name: str) -> None:
    """Remove a coleção inteira (ao deletar agente)."""
    client = get_client()
    try:
        client.delete_collection(collection_name)
        log.info("qdrant.collection_deleted", collection=collection_name)
    except Exception:
        pass

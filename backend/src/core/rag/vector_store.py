"""
Vector store usando pgvector (PostgreSQL).
Substitui o Qdrant — tudo armazenado no Supabase.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import structlog

from src.models.document_chunk import DocumentChunk

log = structlog.get_logger()


def upsert_chunks(
    db: Session,
    document_id: str,
    agent_id: str,
    chunks: List[str],
    vectors: List[List[float]],
) -> int:
    """
    Remove chunks antigos do documento e insere os novos.
    Retorna quantidade de chunks inseridos.
    """
    # Remove versão anterior
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

    new_chunks = []
    for i, (content, embedding) in enumerate(zip(chunks, vectors)):
        new_chunks.append(DocumentChunk(
            document_id=document_id,
            agent_id=agent_id,
            chunk_index=i,
            content=content,
            embedding=embedding,
        ))

    db.bulk_save_objects(new_chunks)
    db.commit()
    log.info("vector_store.upsert", document_id=document_id, chunks=len(new_chunks))
    return len(new_chunks)


def search(
    db: Session,
    agent_id: str,
    query_vector: List[float],
    top_k: int = 5,
    score_threshold: float = 0.35,
    allowed_document_ids: Optional[List[str]] = None,
) -> List[dict]:
    """
    Busca semântica por similaridade coseno usando pgvector.
    Retorna lista de {content, document_id, chunk_index, score}.
    """
    # Constrói filtro de documentos acessíveis
    doc_filter = ""
    params: dict = {
        "agent_id": agent_id,
        "query": str(query_vector),
        "top_k": top_k,
        "threshold": 1.0 - score_threshold,  # pgvector usa distância (menor = mais similar)
    }

    if allowed_document_ids:
        doc_filter = "AND dc.document_id = ANY(:doc_ids)"
        params["doc_ids"] = allowed_document_ids

    sql = text(f"""
        SELECT
            dc.id,
            dc.document_id,
            dc.chunk_index,
            dc.content,
            1 - (dc.embedding <=> :query::vector) AS score
        FROM tania.document_chunks dc
        WHERE dc.agent_id = :agent_id::uuid
          {doc_filter}
          AND 1 - (dc.embedding <=> :query::vector) >= (1 - :threshold)
        ORDER BY dc.embedding <=> :query::vector
        LIMIT :top_k
    """)

    rows = db.execute(sql, params).fetchall()

    return [
        {
            "id": str(row.id),
            "document_id": str(row.document_id),
            "chunk_index": row.chunk_index,
            "content": row.content,
            "score": float(row.score),
        }
        for row in rows
    ]


def delete_document_chunks(db: Session, document_id: str) -> None:
    """Remove todos os chunks de um documento."""
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
    db.commit()

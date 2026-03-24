"""
Celery task: ingestão de documentos → parse → chunk → embed → Qdrant.
"""
import structlog
from datetime import datetime

from src.workers.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(name="ingest_document", bind=True, max_retries=2)
def ingest_document(self, document_id: str):
    """
    Pipeline completo de ingestão:
    1. Busca documento no banco
    2. Download do MinIO
    3. Parse do arquivo
    4. Chunking
    5. Embedding (sentence-transformers local)
    6. Upsert no Qdrant
    7. Atualiza status no banco
    """
    from src.db.session import SessionLocal
    from src.models.document import Document
    from src.models.agent import Agent
    from src.core.storage import minio_client
    from src.core.rag import parsers, chunker, embedder, qdrant_store
    from src.config import settings

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            log.error("ingest.doc_not_found", document_id=document_id)
            return

        agent = db.query(Agent).filter(Agent.id == doc.agent_id).first()
        if not agent or not agent.qdrant_collection:
            _fail(db, doc, "Agente sem coleção Qdrant configurada")
            return

        # Marca como processando
        doc.status = "processing"
        db.commit()

        log.info("ingest.start", document_id=document_id, filename=doc.original_name)

        # 1. Download MinIO
        raw = minio_client.download_bytes(settings.MINIO_BUCKET, doc.minio_path)

        # 2. Parse
        text = parsers.extract_text(raw, doc.file_type)
        if not text.strip():
            _fail(db, doc, "Arquivo sem conteúdo extraível")
            return

        # 3. Chunking
        chunks = chunker.chunk_text(text, chunk_size=400, overlap=50)
        if not chunks:
            _fail(db, doc, "Nenhum chunk gerado")
            return

        # 4. Embedding (em lotes de 64)
        vectors = []
        batch_size = 64
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            vectors.extend(embedder.embed(batch))

        # 5. Upsert no Qdrant
        metadata = {
            "agent_id": str(agent.id),
            "filename": doc.original_name,
            "classification": doc.classification,
        }
        count = qdrant_store.upsert_chunks(
            collection_name=agent.qdrant_collection,
            document_id=document_id,
            chunks=chunks,
            vectors=vectors,
            metadata=metadata,
        )

        # 6. Atualiza documento
        doc.status = "indexed"
        doc.chunk_count = count
        doc.indexed_at = datetime.utcnow()
        doc.error_message = None
        db.commit()

        log.info("ingest.done", document_id=document_id, chunks=count)

    except Exception as exc:
        log.error("ingest.error", document_id=document_id, error=str(exc))
        db.rollback()
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                _fail(db, doc, str(exc))
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


def _fail(db, doc: "Document", message: str):
    doc.status = "error"
    doc.error_message = message[:500]
    db.commit()
    log.warning("ingest.failed", document_id=doc.id, reason=message)

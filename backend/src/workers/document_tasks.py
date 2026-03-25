"""
Celery task: ingestão de documentos → parse → chunk → embed → pgvector.
"""
import structlog
from datetime import datetime

from src.workers.celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(name="ingest_document", bind=True, max_retries=2)
def ingest_document(self, document_id: str):
    """
    Pipeline de ingestão:
    1. Busca documento no banco
    2. Download do MinIO
    3. Parse do arquivo (PDF/DOCX/XLSX/TXT)
    4. Chunking por palavras com overlap
    5. Embedding local (MiniLM-L12-v2)
    6. Upsert no pgvector (PostgreSQL)
    7. Atualiza status no banco
    """
    from src.db.session import SessionLocal
    from src.models.document import Document
    from src.models.agent import Agent
    from src.core.storage import minio_client
    from src.core.rag import parsers, chunker, embedder
    from src.core.rag.vector_store import upsert_chunks
    from src.config import settings

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            log.error("ingest.doc_not_found", document_id=document_id)
            return

        agent = db.query(Agent).filter(Agent.id == doc.agent_id).first()
        if not agent:
            _fail(db, doc, "Agente não encontrado")
            return

        doc.status = "processing"
        db.commit()

        log.info("ingest.start", document_id=document_id, filename=doc.original_name)

        # Download MinIO
        raw = minio_client.download_bytes(settings.MINIO_BUCKET, doc.minio_path)

        # Parse
        text = parsers.extract_text(raw, doc.file_type)
        if not text.strip():
            _fail(db, doc, "Arquivo sem conteúdo extraível")
            return

        # Chunking
        chunks = chunker.chunk_text(text, chunk_size=400, overlap=50)
        if not chunks:
            _fail(db, doc, "Nenhum chunk gerado")
            return

        # Embedding em lotes de 64
        vectors = []
        for i in range(0, len(chunks), 64):
            vectors.extend(embedder.embed(chunks[i:i + 64]))

        # Upsert no pgvector
        count = upsert_chunks(
            db=db,
            document_id=str(doc.id),
            agent_id=str(doc.agent_id),
            chunks=chunks,
            vectors=vectors,
        )

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


def _fail(db, doc, message: str):
    doc.status = "error"
    doc.error_message = message[:500]
    db.commit()
    log.warning("ingest.failed", document_id=doc.id, reason=message)

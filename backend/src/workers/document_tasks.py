from src.workers.celery_app import celery_app


@celery_app.task(name="ingest_document")
def ingest_document(document_id: str):
    """Processa e indexa documento no Qdrant. Implementado na Fase 3."""
    pass

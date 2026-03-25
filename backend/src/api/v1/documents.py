"""
CRUD de documentos — upload, listagem, re-indexação e exclusão.
Apenas admins e key_users do departamento.
"""
import uuid
import os
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.api.dependencies import get_admin_user, get_current_user
from src.models.user import User
from src.models.agent import Agent
from src.models.document import Document
from src.schemas.document import DocumentResponse
from src.core.storage import minio_client
from src.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"pdf", "docx", "xlsx", "txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lstrip(".").lower()


def _to_response(doc: Document, db: Session) -> DocumentResponse:
    from src.models.user import User as UserModel
    uploaded_by_name = None
    if doc.uploaded_by:
        u = db.query(UserModel).filter(UserModel.id == doc.uploaded_by).first()
        uploaded_by_name = u.display_name if u else None

    return DocumentResponse(
        id=doc.id,
        agent_id=doc.agent_id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        classification=doc.classification,
        version=doc.version,
        status=doc.status,
        error_message=doc.error_message,
        file_size_bytes=doc.file_size_bytes,
        chunk_count=doc.chunk_count,
        expires_at=doc.expires_at,
        indexed_at=doc.indexed_at,
        created_at=doc.created_at,
        uploaded_by_name=uploaded_by_name,
    )


@router.get("/{agent_id}", response_model=List[DocumentResponse])
def list_documents(
    agent_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    docs = (
        db.query(Document)
        .filter(Document.agent_id == agent_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_to_response(d, db) for d in docs]


@router.post("/{agent_id}", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    agent_id: str,
    file: UploadFile = File(...),
    classification: str = Form(default="public"),
    expires_at: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    file_type = _ext(file.filename or "")
    if file_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado. Use: {', '.join(ALLOWED_TYPES)}",
        )

    if classification not in ("public", "confidential"):
        raise HTTPException(status_code=400, detail="classification deve ser 'public' ou 'confidential'.")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande (máximo 50 MB).")

    # Versão: incrementa se já existe documento com mesmo nome
    existing = (
        db.query(Document)
        .filter(Document.agent_id == agent_id, Document.original_name == file.filename)
        .order_by(Document.version.desc())
        .first()
    )
    version = (existing.version + 1) if existing else 1

    doc_id = str(uuid.uuid4())
    minio_path = f"{agent_id}/{doc_id}.{file_type}"

    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "txt": "text/plain",
    }

    minio_client.upload_bytes(
        bucket=settings.MINIO_BUCKET,
        object_name=minio_path,
        data=data,
        content_type=content_types.get(file_type, "application/octet-stream"),
    )

    expires_dt = None
    if expires_at:
        try:
            expires_dt = datetime.fromisoformat(expires_at)
        except ValueError:
            pass

    doc = Document(
        id=doc_id,
        agent_id=agent_id,
        uploaded_by=str(current_user.id),
        filename=f"{doc_id}.{file_type}",
        original_name=file.filename,
        file_type=file_type,
        classification=classification,
        version=version,
        status="pending",
        minio_path=minio_path,
        file_size_bytes=len(data),
        expires_at=expires_dt,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Dispara task de ingestão
    from src.workers.document_tasks import ingest_document
    ingest_document.delay(doc_id)

    return _to_response(doc, db)


@router.post("/{agent_id}/{doc_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    agent_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.agent_id == agent_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    doc.status = "pending"
    doc.error_message = None
    db.commit()

    from src.workers.document_tasks import ingest_document
    ingest_document.delay(doc_id)

    db.refresh(doc)
    return _to_response(doc, db)


@router.delete("/{agent_id}/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    agent_id: str,
    doc_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.agent_id == agent_id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()

    # Remove chunks do pgvector
    from src.core.rag.vector_store import delete_document_chunks
    delete_document_chunks(db, doc_id)

    # Remove do MinIO
    try:
        minio_client.delete_object(settings.MINIO_BUCKET, doc.minio_path)
    except Exception:
        pass

    db.delete(doc)
    db.commit()

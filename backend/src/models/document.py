import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.agents.id"),
        nullable=False,
    )
    uploaded_by = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.users.id"),
        nullable=True,
    )
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf | docx | xlsx | txt
    # Classificação: 'public' | 'confidential'
    classification = Column(String(20), nullable=False, default="public")
    version = Column(Integer, nullable=False, default=1)
    # Status: pending | processing | indexed | error | expired
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text)
    minio_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(BigInteger)
    chunk_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")
    access_list = relationship("DocumentAccess", back_populates="document")


class DocumentAccess(Base):
    """Acesso individual a documentos confidenciais."""
    __tablename__ = "document_access"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.documents.id"),
        nullable=False,
    )
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.users.id"),
        nullable=False,
    )
    granted_by = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.users.id"),
        nullable=True,
    )
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="access_list")

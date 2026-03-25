"""
DocumentChunk — armazena chunks de texto com embedding pgvector.
Substitui o Qdrant: tudo fica no PostgreSQL/Supabase.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.models.base import Base

VECTOR_DIM = 384  # paraphrase-multilingual-MiniLM-L12-v2


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        # HNSW index para busca ANN eficiente (pgvector)
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        {"schema": "tania"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("tania.documents.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("tania.agents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(VECTOR_DIM))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="chunks")
    agent = relationship("Agent", back_populates="chunks")

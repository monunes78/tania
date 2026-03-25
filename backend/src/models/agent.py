import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("tania.departments.id"), nullable=False)
    llm_config_id = Column(UUID(as_uuid=True), ForeignKey("tania.llm_configurations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    system_prompt = Column(Text)
    temperature = Column(Numeric(3, 2), default=0.1)
    max_context_chunks = Column(Integer, default=5)
    enable_sql_access = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="agents")
    llm_config = relationship("LLMConfiguration")
    documents = relationship("Document", back_populates="agent")
    conversations = relationship("Conversation", back_populates="agent")
    db_connections = relationship("DBConnection", back_populates="agent")
    schedules = relationship("Schedule", back_populates="agent")
    chunks = relationship("DocumentChunk", back_populates="agent")

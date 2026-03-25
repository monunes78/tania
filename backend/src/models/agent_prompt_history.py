import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class AgentPromptHistory(Base):
    """Histórico de versões do system prompt de cada agente."""
    __tablename__ = "agent_prompt_history"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("tania.agents.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("tania.users.id"), nullable=True)
    system_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent")
    updated_by_user = relationship("User")

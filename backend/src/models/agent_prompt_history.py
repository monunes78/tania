import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class AgentPromptHistory(Base):
    """Histórico de versões do system prompt de cada agente."""
    __tablename__ = "agent_prompt_history"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(UNIQUEIDENTIFIER, ForeignKey("tania.agents.id"), nullable=False)
    updated_by = Column(UNIQUEIDENTIFIER, ForeignKey("tania.users.id"), nullable=True)
    system_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent")
    updated_by_user = relationship("User")

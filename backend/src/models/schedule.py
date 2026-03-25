import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        ForeignKey("tania.users.id"),
        nullable=False,
    )
    agent_id = Column(
        ForeignKey("tania.agents.id"),
        nullable=False,
    )
    name = Column(String(200), nullable=False)
    # task_type: 'sql_query' | 'rag_query'
    task_type = Column(String(50), nullable=False)
    # JSON: {query, context, ...}
    task_payload = Column(Text, nullable=False)
    cron_expression = Column(String(50), nullable=False)
    # JSON: ["chat", "email", "teams"]
    channels = Column(String(500), nullable=False, default='["chat"]')
    is_active = Column(Boolean, default=True, nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="schedules")
    agent = relationship("Agent", back_populates="schedules")

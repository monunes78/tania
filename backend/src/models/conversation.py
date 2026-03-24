import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.users.id"),
        nullable=False,
    )
    agent_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.agents.id"),
        nullable=False,
    )
    title = Column(String(200))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.conversations.id"),
        nullable=False,
    )
    # role: 'user' | 'assistant'
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    # JSON: [{doc_id, chunk_id, score, filename}]
    rag_chunks_used = Column(Text)
    model_used = Column(String(100))
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

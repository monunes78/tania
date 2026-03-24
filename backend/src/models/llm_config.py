import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class LLMConfiguration(Base):
    __tablename__ = "llm_configurations"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.users.id"),
        nullable=True,
    )
    name = Column(String(100), nullable=False)
    # provider: openrouter | anthropic | openai | ollama | azure
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    api_key_enc = Column(Text)          # criptografado com AES-256
    api_base_url = Column(String(500))  # URL customizada (Ollama, Azure)
    extra_params = Column(Text)         # JSON: {temperature, max_tokens, ...}
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

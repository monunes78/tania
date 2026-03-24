import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class DBConnection(Base):
    """Conexões de banco de dados por agente (para análise de dados)."""
    __tablename__ = "db_connections"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("tania.agents.id"),
        nullable=False,
    )
    # Nome exibido ao LLM para orientação contextual
    display_name = Column(String(100), nullable=False)
    server_host = Column(String(200), nullable=False)
    server_port = Column(String(10), default="1433")
    database_name = Column(String(100), nullable=False)
    # JSON: lista de schemas/tabelas permitidos
    allowed_schemas = Column(Text, nullable=False, default="[]")
    # Credenciais criptografadas
    credentials_enc = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="db_connections")

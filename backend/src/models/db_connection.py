import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class DBConnection(Base):
    """Conexões de banco de dados por agente (para análise de dados)."""
    __tablename__ = "db_connections"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("tania.agents.id"), nullable=False)
    display_name = Column(String(100), nullable=False)
    # db_type: sqlserver | postgresql | mysql
    db_type = Column(String(20), nullable=False, default="sqlserver")
    server_host = Column(String(200), nullable=False)
    server_port = Column(String(10), default="1433")
    database_name = Column(String(100), nullable=False)
    # JSON: lista de schemas/tabelas permitidos
    allowed_schemas = Column(Text, nullable=False, default="[]")
    # Credenciais criptografadas
    credentials_enc = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="db_connections")

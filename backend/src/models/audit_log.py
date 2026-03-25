from datetime import datetime
from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "tania"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        ForeignKey("tania.users.id"),
        nullable=True,
    )
    # Ex: 'auth.login', 'document.upload', 'agent.prompt.update', 'sql.query'
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    details = Column(Text)  # JSON com contexto adicional
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")

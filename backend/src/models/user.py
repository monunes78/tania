import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from src.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "tania"}

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_object_id = Column(String(256), nullable=False, unique=True)
    username = Column(String(100), nullable=False)
    email = Column(String(256), nullable=False)
    display_name = Column(String(256))
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversations = relationship("Conversation", back_populates="user")
    uploaded_documents = relationship("Document", back_populates="uploaded_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")

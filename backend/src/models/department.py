import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.models.base import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True)
    description = Column(String(500))
    icon = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agents = relationship("Agent", back_populates="department")
    access_groups = relationship("DepartmentAccess", back_populates="department")


class DepartmentAccess(Base):
    """Mapeia grupos AD a departamentos com perfil de acesso."""
    __tablename__ = "department_access"
    __table_args__ = {"schema": "tania"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("tania.departments.id"), nullable=False)
    ad_group_dn = Column(String(500), nullable=False)
    # Perfil: 'user' | 'editor' | 'key_user'
    role = Column(String(20), nullable=False, default="user")

    department = relationship("Department", back_populates="access_groups")

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DepartmentAccessSchema(BaseModel):
    id: str
    ad_group_dn: str
    role: str

    class Config:
        from_attributes = True


class DepartmentBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = "users"
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: str
    created_at: datetime
    agent_count: int = 0

    class Config:
        from_attributes = True


class DepartmentAccessCreate(BaseModel):
    ad_group_dn: str
    role: str = "user"  # user | editor | key_user

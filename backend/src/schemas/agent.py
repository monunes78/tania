from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[Decimal] = Decimal("0.1")
    max_context_chunks: int = 5
    enable_sql_access: bool = False
    is_active: bool = True


class AgentCreate(AgentBase):
    department_id: str
    llm_config_id: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    temperature: Optional[Decimal] = None
    max_context_chunks: Optional[int] = None
    enable_sql_access: Optional[bool] = None
    llm_config_id: Optional[str] = None
    is_active: Optional[bool] = None


class AgentPromptUpdate(BaseModel):
    system_prompt: str


class AgentPromptHistoryResponse(BaseModel):
    id: str
    system_prompt: Optional[str]
    updated_by_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentResponse(AgentBase):
    id: str
    department_id: str
    department_name: Optional[str] = None
    llm_config_id: Optional[str] = None
    llm_config_name: Optional[str] = None
    qdrant_collection: Optional[str] = None
    document_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

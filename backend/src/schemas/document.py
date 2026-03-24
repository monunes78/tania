from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    agent_id: str
    filename: str
    original_name: str
    file_type: str
    classification: str
    version: int
    status: str
    error_message: Optional[str] = None
    file_size_bytes: Optional[int] = None
    chunk_count: int
    expires_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    created_at: datetime
    uploaded_by_name: Optional[str] = None

    class Config:
        from_attributes = True

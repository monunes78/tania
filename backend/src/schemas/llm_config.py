from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LLMConfigBase(BaseModel):
    name: str
    provider: str  # openrouter | anthropic | openai | ollama | azure
    model_name: str
    api_base_url: Optional[str] = None
    extra_params: Optional[str] = None
    is_default: bool = False
    is_active: bool = True


class LLMConfigCreate(LLMConfigBase):
    api_key: Optional[str] = None  # plain text — será criptografado


class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    extra_params: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class LLMConfigResponse(LLMConfigBase):
    id: str
    has_api_key: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class LLMTestResult(BaseModel):
    success: bool
    latency_ms: int
    response: Optional[str] = None
    error: Optional[str] = None

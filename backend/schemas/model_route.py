"""Pydantic schemas for ModelRoute."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ModelRouteUpdate(BaseModel):
    provider: Optional[str] = Field(None, max_length=50)
    model_name: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = Field(None, description="Plaintext API key — will be encrypted before storage")
    api_base_url: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ModelRouteResponse(BaseModel):
    task_key: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key_masked: Optional[str] = None
    api_base_url: Optional[str] = None
    enabled: bool
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

"""Pydantic schemas for ModelApi."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ModelApiCreate(BaseModel):
    name: str = Field(..., max_length=100)
    provider: str = Field(..., max_length=50)
    model_name: str = Field(..., max_length=255)
    api_key: Optional[str] = Field(None, description="Plaintext API key")
    api_base_url: Optional[str] = Field(None, max_length=500)
    enabled: bool = True
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ModelApiUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, max_length=50)
    model_name: Optional[str] = Field(None, max_length=255)
    api_key: Optional[str] = Field(None, description="Plaintext API key — set to update")
    api_base_url: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ModelApiResponse(BaseModel):
    id: int
    name: str
    provider: str
    model_name: str
    api_key_masked: Optional[str] = None
    api_base_url: Optional[str] = None
    enabled: bool
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

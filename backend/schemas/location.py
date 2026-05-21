"""Pydantic schemas for Location."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Location name")
    location_type: Optional[str] = Field(None, max_length=50, description="continent / country / city / landmark / region")
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    location_type: Optional[str] = None
    description: Optional[str] = None
    is_locked: Optional[bool] = None


class LocationResponse(BaseModel):
    id: int
    name: str
    location_type: Optional[str] = None
    description: Optional[str] = None
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

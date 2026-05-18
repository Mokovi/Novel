"""Pydantic schemas for Book CRUD."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Book name")
    description: Optional[str] = None


class BookUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    outline: Optional[str] = None


class BookWorldviewUpdate(BaseModel):
    worldview: str = Field(..., description="Worldview JSON string")


class BookOutlineUpdate(BaseModel):
    outline: str


class BookWritingStyleUpdate(BaseModel):
    writing_style: str = Field(..., description="Writing style JSON string")


class BookBrief(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookStats(BaseModel):
    volume_count: int = 0
    chapter_count: int = 0
    character_count: int = 0


class BookResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    outline: Optional[str] = None
    worldview: Optional[str] = None
    writing_style: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

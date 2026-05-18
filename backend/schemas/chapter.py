"""Pydantic schemas for Volume and Chapter."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VolumeCreate(BaseModel):
    title: str = Field(..., max_length=255, description="Volume title")
    description: Optional[str] = None
    sort_order: int = 0


class VolumeResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChapterCreate(BaseModel):
    volume_id: int
    title: str = Field(..., max_length=255, description="Chapter title")
    summary: Optional[str] = None
    sort_order: int = 0


class ChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    ai_summary: Optional[str] = None
    content: Optional[str] = None
    worldview_level: Optional[str] = Field(None, pattern=r"^(high|medium|low)$")


class ChapterResponse(BaseModel):
    id: int
    volume_id: int
    title: str
    summary: Optional[str] = None
    ai_summary: Optional[str] = None
    content: Optional[str] = None
    word_count: int
    status: str
    sort_order: int
    worldview_level: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderItem(BaseModel):
    id: int
    sort_order: int


class ReorderRequest(BaseModel):
    items: list[ReorderItem]


class CharacterBrief(BaseModel):
    id: int
    name: str
    role_type: Optional[str] = None

    model_config = {"from_attributes": True}


class ChapterCharactersUpdate(BaseModel):
    character_ids: list[int]

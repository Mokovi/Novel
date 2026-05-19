"""Pydantic schemas for Book CRUD."""

from datetime import datetime

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class BookUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    outline: str | None = None
    worldview: str | None = None
    writing_style: str | None = None


class BookResponse(BaseModel):
    id: int
    name: str
    description: str | None
    outline: str | None
    worldview: str | None
    writing_style: str | None
    created_at: datetime
    updated_at: datetime

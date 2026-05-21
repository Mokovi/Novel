"""Pydantic schemas for Character and CharacterRelation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Character name")
    aliases: Optional[str] = None
    role_type: Optional[str] = Field(None, max_length=50, description="protagonist / antagonist / supporting / minor")
    status: str = "active"
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    goals: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    aliases: Optional[str] = None
    role_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    goals: Optional[str] = None
    is_locked: Optional[bool] = None


class CharacterResponse(BaseModel):
    id: int
    name: str
    aliases: Optional[str] = None
    role_type: Optional[str] = None
    status: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    goals: Optional[str] = None
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterRelationCreate(BaseModel):
    character_id_from: int
    character_id_to: int
    relation_type: str = Field(..., max_length=50, description="ally / enemy / neutral / blood / mentor / romance")
    description: Optional[str] = None


class CharacterRelationUpdate(BaseModel):
    relation_type: Optional[str] = None
    description: Optional[str] = None


class CharacterRelationResponse(BaseModel):
    id: int
    character_id_from: int
    character_id_to: int
    relation_type: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class CharacterImportItem(BaseModel):
    name: str = Field(..., max_length=255, description="Character name")
    aliases: Optional[str] = None
    role_type: Optional[str] = Field(None, max_length=50)
    status: str = "active"
    description: Optional[str] = None
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    goals: Optional[str] = None


class CharacterImportRequest(BaseModel):
    format_version: int = 1
    overwrite: bool = False
    characters: list[CharacterImportItem]


class CharacterImportResult(BaseModel):
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    errors: list[str] = []

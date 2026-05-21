"""Pydantic schemas for generation endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class InjectionOverrides(BaseModel):
    """Controls which context variables to exclude and what to add."""

    exclude_variables: list[str] = Field(default_factory=list)
    extra_variables: dict[str, str] = Field(default_factory=dict)
    added_character_ids: list[int] = Field(default_factory=list)
    added_location_ids: list[int] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    """Optional overrides for generation."""

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    user_prompt: Optional[str] = None
    injection_overrides: Optional[InjectionOverrides] = None


class OutlineGenerateRequest(BaseModel):
    """Request body for outline generation with optional user prompt."""

    user_prompt: Optional[str] = None
    injection_overrides: Optional[InjectionOverrides] = None


class GenerateProgress(BaseModel):
    """SSE payload sent per chunk during streaming."""

    event: str = "token"  # token | start | done | error
    data: str = ""

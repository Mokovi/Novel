"""Pydantic schemas for generation endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Optional overrides for generation."""

    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class GenerateProgress(BaseModel):
    """SSE payload sent per chunk during streaming."""

    event: str = "token"  # token | start | done | error
    data: str = ""

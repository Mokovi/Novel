"""Pydantic schemas for prompt template CRUD."""

from typing import Optional

from pydantic import BaseModel, Field


class TemplateMetadata(BaseModel):
    """Metadata returned in template list responses."""

    file_name: str
    task_type: Optional[str] = None
    name: Optional[str] = None
    is_default: bool = False
    version: Optional[str] = None
    description: Optional[str] = None


class TemplateResponse(BaseModel):
    """Full template content returned on read/create/update."""

    file_name: str
    frontmatter: dict
    body: str
    token_estimate: Optional[int] = None

    model_config = {"from_attributes": True}


class TemplateCreate(BaseModel):
    file_name: str = Field(..., description="File name, e.g. 'my_template.md'")
    frontmatter: dict = Field(default_factory=dict)
    body: str = ""


class TemplateUpdate(BaseModel):
    frontmatter: Optional[dict] = None
    body: Optional[str] = None


class BuildPreviewRequest(BaseModel):
    file_name: str
    variables: dict = Field(default_factory=dict)


class BuildPreviewResponse(BaseModel):
    prompt: str
    token_estimate: int

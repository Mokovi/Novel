"""System settings endpoints — generation config, etc."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.config import load_config, save_config
from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class GenerationSettings(BaseModel):
    previous_chapter_count: int = Field(1, ge=0, le=10)
    outline_generation_count: int = Field(1, ge=1, le=5)
    outline_injection_depth: int = Field(1, ge=0, le=3)


@router.get("/generation", response_model=GenerationSettings)
def get_generation_settings(
    current_user: User = Depends(get_current_user),
):
    """Return the current generation configuration."""
    cfg = load_config()
    gen = cfg.get("generation", {})
    return GenerationSettings(
        previous_chapter_count=gen.get("previous_chapter_count", 1),
        outline_generation_count=gen.get("outline_generation_count", 1),
        outline_injection_depth=gen.get("outline_injection_depth", 1),
    )


@router.put("/generation", response_model=GenerationSettings)
def update_generation_settings(
    body: GenerationSettings,
    current_user: User = Depends(get_current_user),
):
    """Update the generation configuration."""
    cfg = load_config()
    cfg["generation"] = {
        "previous_chapter_count": body.previous_chapter_count,
        "outline_generation_count": body.outline_generation_count,
        "outline_injection_depth": body.outline_injection_depth,
    }
    save_config(cfg)
    return body

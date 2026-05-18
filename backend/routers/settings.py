"""System settings endpoints — generation config, etc."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.config import load_config, save_config

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class GenerationSettings(BaseModel):
    previous_chapter_count: int = Field(1, ge=0, le=10)
    auto_split_target_words: int = Field(2000, ge=500, le=10000)


@router.get("/generation", response_model=GenerationSettings)
def get_generation_settings():
    """Return the current generation configuration."""
    cfg = load_config()
    gen = cfg.get("generation", {})
    return GenerationSettings(
        previous_chapter_count=gen.get("previous_chapter_count", 1),
        auto_split_target_words=gen.get("auto_split_target_words", 2000),
    )


@router.put("/generation", response_model=GenerationSettings)
def update_generation_settings(body: GenerationSettings):
    """Update the generation configuration."""
    cfg = load_config()
    cfg["generation"] = {
        "previous_chapter_count": body.previous_chapter_count,
        "auto_split_target_words": body.auto_split_target_words,
    }
    save_config(cfg)
    return body

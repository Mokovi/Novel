"""SSE streaming endpoint for chapter generation."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.generate import GenerateRequest
from backend.services.generator import build_prompt_variables, generate_chapter_stream

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])


@router.post("/chapter/{chapter_id}")
async def generate_chapter(
    chapter_id: int,
    body: GenerateRequest = GenerateRequest(),
    db: Session = Depends(get_db),
):
    """Stream chapter generation via SSE.

    Returns a ``text/event-stream`` response. Each event is a JSON line::

        data: {"event": "start", "model": "...", "token_estimate": N}
        data: {"event": "token", "token": "..."}
        data: {"event": "done", "word_count": N, "model": "..."}
        data: {"event": "error", "message": "..."}
    """
    return StreamingResponse(
        generate_chapter_stream(db, chapter_id, body.temperature, body.max_tokens),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chapter/{chapter_id}/preview")
async def preview_chapter_prompt(
    chapter_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for a chapter without generating."""
    ctx = build_prompt_variables(db, chapter_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }

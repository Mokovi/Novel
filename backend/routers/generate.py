"""SSE streaming endpoints for chapter and outline generation."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories import chapter_repo
from backend.schemas.generate import GenerateRequest
from backend.services.generator import (
    build_arc_prompt_variables,
    build_book_prompt_variables,
    build_prompt_variables,
    build_volume_prompt_variables,
    generate_ai_summary,
    generate_chapter_stream,
    generate_outline_stream,
)

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])


# ── Chapter generation ─────────────────────────────────────


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


@router.post("/chapter/{chapter_id}/summary")
async def regenerate_chapter_summary(
    chapter_id: int,
    db: Session = Depends(get_db),
):
    """Regenerate the AI summary for a chapter (non-streaming)."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if not chapter.content:
        raise HTTPException(status_code=400, detail="Chapter has no content")
    summary = await generate_ai_summary(
        db, chapter.content, chapter.title or "", chapter.summary or "",
    )
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    chapter_repo.save_chapter_ai_summary(db, chapter_id, summary)
    return {"summary": summary}


# ── Arc outline generation ─────────────────────────────────


@router.post("/arc/{arc_id}")
async def generate_arc_outline(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Stream arc outline generation via SSE."""
    ctx = build_arc_prompt_variables(db, arc_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])

    async def _stream_and_save():
        full_content = ""
        async for event in generate_outline_stream(db, ctx):
            yield event
            # Capture the done event content to save
            import json
            if event.startswith("data: "):
                try:
                    parsed = json.loads(event[6:].strip())
                    if parsed.get("event") == "done":
                        full_content = parsed.get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if full_content:
            chapter_repo.save_arc_outline(db, arc_id, full_content)

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/arc/{arc_id}/preview")
async def preview_arc_prompt(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for an arc without generating."""
    ctx = build_arc_prompt_variables(db, arc_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Volume outline generation ──────────────────────────────


@router.post("/volume/{volume_id}")
async def generate_volume_outline(
    volume_id: int,
    db: Session = Depends(get_db),
):
    """Stream volume outline generation via SSE."""
    ctx = build_volume_prompt_variables(db, volume_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])

    async def _stream_and_save():
        full_content = ""
        async for event in generate_outline_stream(db, ctx):
            yield event
            import json
            if event.startswith("data: "):
                try:
                    parsed = json.loads(event[6:].strip())
                    if parsed.get("event") == "done":
                        full_content = parsed.get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if full_content:
            chapter_repo.save_volume_outline(db, volume_id, full_content)

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/volume/{volume_id}/preview")
async def preview_volume_prompt(
    volume_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for a volume without generating."""
    ctx = build_volume_prompt_variables(db, volume_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Book outline generation ────────────────────────────────


@router.post("/book")
async def generate_book_outline(
    db: Session = Depends(get_db),
):
    """Stream book-level outline generation via SSE."""
    ctx = build_book_prompt_variables(db)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])

    async def _stream_and_save():
        full_content = ""
        async for event in generate_outline_stream(db, ctx):
            yield event
            import json
            if event.startswith("data: "):
                try:
                    parsed = json.loads(event[6:].strip())
                    if parsed.get("event") == "done":
                        full_content = parsed.get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if full_content:
            from backend.config import load_config, save_config
            cfg = load_config()
            cfg["book_outline"] = full_content
            save_config(cfg)

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/book/preview")
async def preview_book_prompt(
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for the book outline without generating."""
    ctx = build_book_prompt_variables(db)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


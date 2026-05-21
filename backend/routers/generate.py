"""SSE streaming endpoints for chapter and outline generation."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.repositories import chapter_repo
from backend.repositories import character_repo
from backend.schemas.generate import GenerateRequest, InjectionOverrides, OutlineGenerateRequest
from backend.repositories import book_repo
from backend.services import character_parser
from backend.services import prompt_builder
from backend.services.generator import (
    apply_injection_overrides,
    build_arc_prompt_variables,
    build_book_prompt_variables,
    build_character_prompt_variables,
    build_map_prompt_variables,
    build_prompt_variables,
    build_volume_prompt_variables,
    build_worldview_prompt_variables,
    generate_ai_summary,
    generate_chapter_stream,
    generate_outline_stream,
    _sse_event,
)

router = APIRouter(prefix="/api/v1/generate", tags=["generate"])

_VARIABLE_LABELS: dict[str, str] = {
    "book_name": "书名",
    "book_description": "书籍描述",
    "worldview": "世界观设定",
    "writing_style": "文风设定",
    "character_profiles": "角色档案",
    "chapter_title": "章节标题",
    "chapter_summary": "章节摘要",
    "previous_chapter_summary": "前文摘要",
    "chapter_outline": "章节大纲",
    "volume_title": "卷标题",
    "volume_description": "卷描述",
    "volume_outline": "卷纲",
    "arc_title": "事件标题",
    "arc_description": "事件描述",
    "event_outline": "事件纲",
    "book_outline": "全书纲",
    "chapter_summaries": "章节摘要列表",
    "arc_outlines": "事件纲列表",
    "volume_outlines": "卷纲列表",
    "current_worldview": "当前世界观设定",
    "current_map": "当前地图设定",
    "map_data": "地图设定",
    "current_characters": "当前人物列表",
}


def _apply_overrides_and_rebuild(ctx: dict, overrides: InjectionOverrides, db: Session) -> dict:
    """Apply injection overrides to a prompt context dict and rebuild the prompt."""
    ctx["variables"] = apply_injection_overrides(ctx["variables"], overrides, db)
    try:
        ctx["prompt"] = prompt_builder.build_prompt(ctx["template"], ctx["variables"])
    except ValueError as e:
        ctx["error"] = str(e)
    return ctx


def _build_injection_items(ctx: dict) -> list[dict]:
    """Build injection metadata items from a prompt context dict."""
    items = []
    for var_name in ctx.get("variables", {}):
        label = _VARIABLE_LABELS.get(var_name, var_name)
        value = ctx["variables"][var_name]
        items.append({
            "variable": var_name,
            "label": label,
            "source": "system",
            "default_enabled": True,
            "required": False,
            "available": bool(value and value.strip()),
        })
    return items


# ── Chapter generation ─────────────────────────────────────


@router.post("/chapter/{chapter_id}")
async def generate_chapter(
    chapter_id: int,
    body: GenerateRequest = GenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream chapter generation via SSE."""
    return StreamingResponse(
        generate_chapter_stream(
            db, chapter_id, body.temperature, body.max_tokens,
            current_user.id, body.user_prompt, body.injection_overrides,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chapter/{chapter_id}/preview")
async def preview_chapter_prompt(
    chapter_id: int,
    book_id: int = Query(..., description="Book ID for context"),
    body: GenerateRequest = GenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for a chapter without generating."""
    ctx = build_prompt_variables(db, chapter_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
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
    current_user: User = Depends(get_current_user),
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
    book_id: int = Query(..., description="Book ID for context"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream arc outline generation via SSE."""
    ctx = build_arc_prompt_variables(db, arc_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

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
            chapter_repo.save_arc_outline(db, arc_id, full_content)

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/arc/{arc_id}/preview")
async def preview_arc_prompt(
    arc_id: int,
    book_id: int = Query(..., description="Book ID for context"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for an arc without generating."""
    ctx = build_arc_prompt_variables(db, arc_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
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
    book_id: int = Query(..., description="Book ID for context"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream volume outline generation via SSE."""
    ctx = build_volume_prompt_variables(db, volume_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

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
    book_id: int = Query(..., description="Book ID for context"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for a volume without generating."""
    ctx = build_volume_prompt_variables(db, volume_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Book outline generation ────────────────────────────────


@router.post("/book")
async def generate_book_outline(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream book-level outline generation via SSE."""
    ctx = build_book_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

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
            from backend.repositories import book_repo as br
            book = br.get_book_for_user(db, book_id, current_user.id)
            if book:
                book.outline = full_content
                db.commit()

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/book/preview")
async def preview_book_prompt(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for the book outline without generating."""
    ctx = build_book_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Worldview generation ────────────────────────────────────


@router.post("/worldview")
async def generate_worldview(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream worldview content generation via SSE."""
    ctx = build_worldview_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

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
            book = book_repo.get_book_for_user(db, book_id, current_user.id)
            if book:
                book.worldview = full_content
                db.commit()

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/worldview/preview")
async def preview_worldview_prompt(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for worldview generation without generating."""
    ctx = build_worldview_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Map generation ──────────────────────────────────────────


@router.post("/map")
async def generate_map(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream map content generation via SSE."""
    ctx = build_map_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

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
            book = book_repo.get_book_for_user(db, book_id, current_user.id)
            if book:
                book.map = full_content
                db.commit()

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/map/preview")
async def preview_map_prompt(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for map generation without generating."""
    ctx = build_map_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


@router.post("/map/injections")
async def map_injection_items(
    book_id: int = Query(..., description="Book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a map generation."""
    ctx = build_map_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


# ── Character generation ─────────────────────────────────────


@router.post("/characters")
async def generate_characters(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream character profile generation via SSE."""
    ctx = build_character_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    if body.user_prompt:
        ctx["prompt"] = ctx["prompt"] + "\n\n## 用户补充要求\n\n" + body.user_prompt

    import json

    async def _stream_and_save():
        full_content = ""
        async for event in generate_outline_stream(db, ctx):
            yield event
            if event.startswith("data: "):
                try:
                    parsed = json.loads(event[6:].strip())
                    if parsed.get("event") == "done":
                        full_content = parsed.get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        if full_content:
            parsed_chars = character_parser.parse_character_markdown(full_content)
            if parsed_chars:
                result = character_repo.bulk_create_characters(db, parsed_chars, book_id)
                yield _sse_event("summary", {
                    "summary": {
                        "created_count": result["created_count"],
                        "skipped_count": result["skipped_count"],
                        "errors": result["errors"],
                    }
                })

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/characters/preview")
async def preview_character_prompt(
    book_id: int = Query(..., description="Book ID"),
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return assembled prompt and metadata for character generation without generating."""
    ctx = build_character_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    if body.injection_overrides:
        ctx = _apply_overrides_and_rebuild(ctx, body.injection_overrides, db)
        if ctx.get("error"):
            raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


@router.post("/characters/injections")
async def character_injection_items(
    book_id: int = Query(..., description="Book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a character generation."""
    ctx = build_character_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


# ── Injection metadata endpoints ────────────────────────────


@router.post("/chapter/{chapter_id}/injections")
async def chapter_injection_items(
    chapter_id: int,
    book_id: int = Query(..., description="Book ID for context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a chapter generation."""
    ctx = build_prompt_variables(db, chapter_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


@router.post("/arc/{arc_id}/injections")
async def arc_injection_items(
    arc_id: int,
    book_id: int = Query(..., description="Book ID for context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for an arc outline generation."""
    ctx = build_arc_prompt_variables(db, arc_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


@router.post("/volume/{volume_id}/injections")
async def volume_injection_items(
    volume_id: int,
    book_id: int = Query(..., description="Book ID for context"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a volume outline generation."""
    ctx = build_volume_prompt_variables(db, volume_id, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


@router.post("/book/injections")
async def book_injection_items(
    book_id: int = Query(..., description="Book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a book outline generation."""
    ctx = build_book_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }


@router.post("/worldview/injections")
async def worldview_injection_items(
    book_id: int = Query(..., description="Book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return injection metadata for a worldview generation."""
    ctx = build_worldview_prompt_variables(db, book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "items": _build_injection_items(ctx),
        "template_name": ctx["template_name"],
        "model": ctx["model_name"],
    }

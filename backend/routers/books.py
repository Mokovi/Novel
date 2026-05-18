"""REST endpoints for Book CRUD — top-level book management."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories import book_repo, chapter_repo, character_repo
from backend.schemas.book import (
    BookBrief,
    BookCreate,
    BookOutlineUpdate,
    BookResponse,
    BookStats,
    BookUpdate,
    BookWorldviewUpdate,
    BookWritingStyleUpdate,
)
from backend.schemas.character import CharacterCreate, CharacterResponse
from backend.schemas.generate import GenerateRequest, OutlineGenerateRequest
from backend.services.generator import (
    build_arc_prompt_variables,
    build_book_prompt_variables,
    build_prompt_variables,
    build_volume_prompt_variables,
    generate_ai_summary,
    generate_chapter_stream,
    generate_outline_stream,
)
router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("", response_model=list[BookBrief])
def list_books(db: Session = Depends(get_db)):
    """List all books ordered by most recently updated."""
    return book_repo.list_books(db)


@router.post("", response_model=BookResponse, status_code=201)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    """Create a new book."""
    return book_repo.create_book(db, body)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get book detail by ID."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, body: BookUpdate, db: Session = Depends(get_db)):
    """Update book metadata."""
    book = book_repo.update_book(db, book_id, body)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book and cascade-delete all associated data."""
    deleted = book_repo.delete_book(db, book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    return None


@router.get("/{book_id}/stats", response_model=BookStats)
def get_book_stats(book_id: int, db: Session = Depends(get_db)):
    """Get aggregate stats for a book (volume/chapter/character counts)."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookStats(**book_repo.get_book_stats(db, book_id))


# ── Worldview sub-routes ───────────────────────────────────


@router.get("/{book_id}/worldview")
def get_book_worldview(book_id: int, db: Session = Depends(get_db)):
    """Get the worldview JSON for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    import json
    if book.worldview:
        try:
            return json.loads(book.worldview)
        except json.JSONDecodeError:
            pass
    return {}


@router.put("/{book_id}/worldview")
def update_book_worldview(book_id: int, body: BookWorldviewUpdate, db: Session = Depends(get_db)):
    """Update the worldview JSON for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.worldview = body.worldview
    db.commit()
    db.refresh(book)
    import json
    try:
        return json.loads(book.worldview)
    except json.JSONDecodeError:
        return {}


# ── Outline sub-routes ─────────────────────────────────────


@router.get("/{book_id}/outline", response_model=BookOutlineUpdate)
def get_book_outline(book_id: int, db: Session = Depends(get_db)):
    """Get the outline text for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookOutlineUpdate(outline=book.outline or "")


@router.put("/{book_id}/outline", response_model=BookOutlineUpdate)
def update_book_outline(book_id: int, body: BookOutlineUpdate, db: Session = Depends(get_db)):
    """Update the outline text for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.outline = body.outline
    db.commit()
    db.refresh(book)
    return BookOutlineUpdate(outline=book.outline or "")


# ── Characters sub-routes ──────────────────────────────────


@router.get("/{book_id}/characters", response_model=list[CharacterResponse])
def list_book_characters(
    book_id: int,
    db: Session = Depends(get_db),
):
    """Get characters for a book."""
    return character_repo.list_characters(db, book_id=book_id)


@router.post("/{book_id}/characters", response_model=CharacterResponse, status_code=201)
def create_book_character(book_id: int, body: CharacterCreate, db: Session = Depends(get_db)):
    """Create a new character under a book."""
    character = character_repo.create_character(db, body)
    character.book_id = book_id
    db.commit()
    db.refresh(character)
    return character


@router.get("/{book_id}/characters/relations", response_model=dict)
def get_book_relations_graph(book_id: int, db: Session = Depends(get_db)):
    """Get relations graph scoped to a specific book."""
    return character_repo.get_relations_graph(db, book_id=book_id)


# ── Writing Style sub-routes ───────────────────────────────


@router.get("/{book_id}/writing-style")
def get_book_writing_style(book_id: int, db: Session = Depends(get_db)):
    """Get the writing style JSON for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    import json
    if book.writing_style:
        try:
            return json.loads(book.writing_style)
        except json.JSONDecodeError:
            pass
    return {}


@router.put("/{book_id}/writing-style")
def update_book_writing_style(book_id: int, body: BookWritingStyleUpdate, db: Session = Depends(get_db)):
    """Update the writing style JSON for a book."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.writing_style = body.writing_style
    db.commit()
    db.refresh(book)
    import json
    try:
        return json.loads(book.writing_style)
    except json.JSONDecodeError:
        return {}


# ── Book-scoped generate endpoints ─────────────────────────


@router.post("/{book_id}/generate/book")
async def generate_book_outline(
    book_id: int,
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
):
    """Stream book-level outline generation for a specific book via SSE."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    ctx = build_book_prompt_variables(db, book_id=book_id)
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
            book.outline = full_content
            db.commit()

    return StreamingResponse(
        _stream_and_save(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{book_id}/generate/book/preview")
async def preview_book_outline(
    book_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for a book's outline without generating."""
    book = book_repo.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    ctx = build_book_prompt_variables(db, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=400, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Chapter generation ─────────────────────────────────────


@router.post("/{book_id}/generate/chapter/{chapter_id}")
async def generate_book_chapter(
    book_id: int,
    chapter_id: int,
    body: GenerateRequest = GenerateRequest(),
    db: Session = Depends(get_db),
):
    """Stream chapter generation for a specific book via SSE."""
    return StreamingResponse(
        generate_chapter_stream(db, chapter_id, body.temperature, body.max_tokens, book_id=book_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{book_id}/generate/chapter/{chapter_id}/preview")
async def preview_book_chapter_prompt(
    book_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for a chapter without generating."""
    ctx = build_prompt_variables(db, chapter_id, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


@router.post("/{book_id}/generate/chapter/{chapter_id}/summary")
async def regenerate_book_chapter_summary(
    book_id: int,
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


@router.post("/{book_id}/generate/arc/{arc_id}")
async def generate_book_arc_outline(
    book_id: int,
    arc_id: int,
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
):
    """Stream arc outline generation for a specific book via SSE."""
    ctx = build_arc_prompt_variables(db, arc_id, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
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


@router.post("/{book_id}/generate/arc/{arc_id}/preview")
async def preview_book_arc_prompt(
    book_id: int,
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for an arc without generating."""
    ctx = build_arc_prompt_variables(db, arc_id, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }


# ── Volume outline generation ──────────────────────────────


@router.post("/{book_id}/generate/volume/{volume_id}")
async def generate_book_volume_outline(
    book_id: int,
    volume_id: int,
    body: OutlineGenerateRequest = OutlineGenerateRequest(),
    db: Session = Depends(get_db),
):
    """Stream volume outline generation for a specific book via SSE."""
    ctx = build_volume_prompt_variables(db, volume_id, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
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


@router.post("/{book_id}/generate/volume/{volume_id}/preview")
async def preview_book_volume_prompt(
    book_id: int,
    volume_id: int,
    db: Session = Depends(get_db),
):
    """Return assembled prompt and metadata for a volume without generating."""
    ctx = build_volume_prompt_variables(db, volume_id, book_id=book_id)
    if ctx.get("error"):
        raise HTTPException(status_code=404, detail=ctx["error"])
    return {
        "prompt": ctx["prompt"],
        "token_estimate": ctx["token_estimate"],
        "model": ctx["model_name"],
        "template_name": ctx["template_name"],
    }

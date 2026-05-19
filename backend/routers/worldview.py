"""REST endpoints for worldview settings — now per-book via books router.

Deprecated: these file-based endpoints remain for backward compatibility
but new clients should use ``GET /api/v1/books/{book_id}/worldview``.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import DATA_DIR
from backend.database import get_db
from backend.models.user import User
from backend.repositories import book_repo
from backend.routers.deps import get_current_user
from backend.services.prompt_builder import estimate_tokens
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/worldview", tags=["worldview"])

WORLDVIEW_PATH = DATA_DIR / "worldview.json"


def _read_worldview() -> str:
    if not WORLDVIEW_PATH.exists():
        return ""
    return WORLDVIEW_PATH.read_text(encoding="utf-8")


def _write_worldview(text: str) -> None:
    WORLDVIEW_PATH.write_text(text, encoding="utf-8")


@router.get("")
def get_worldview(
    book_id: int | None = Query(None, description="Book ID for per-book worldview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return worldview — from book if book_id given, else legacy file."""
    if book_id is not None:
        book = book_repo.get_book_for_user(db, book_id, current_user.id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"worldview": book.worldview or ""}
    return {"worldview": _read_worldview()}


@router.put("")
def update_worldview(
    body: dict,
    book_id: int | None = Query(None, description="Book ID for per-book worldview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update worldview settings."""
    text = body.get("worldview", "")
    if book_id is not None:
        book = book_repo.get_book_for_user(db, book_id, current_user.id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        book.worldview = text
        db.commit()
        return {"worldview": text}

    _write_worldview(text)
    return {"worldview": _read_worldview()}


@router.get("/inject-preview")
def inject_preview(
    book_id: int | None = Query(None, description="Book ID for per-book worldview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview how the worldview will appear when injected into a prompt."""
    if book_id is not None:
        book = book_repo.get_book_for_user(db, book_id, current_user.id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        text = book.worldview or ""
    else:
        text = _read_worldview()
    return {
        "text": text,
        "token_estimate": estimate_tokens(text),
        "section_count": text.count("## "),
    }

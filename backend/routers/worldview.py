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


def _read_worldview() -> dict:
    if not WORLDVIEW_PATH.exists():
        return {}
    with open(WORLDVIEW_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_worldview(data: dict) -> None:
    WORLDVIEW_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _format_section(name: str, content) -> str:
    """Format a single worldview section into readable text."""
    lines = [f"## {name}"]

    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                lines.extend(f"- {k}: {v}" for k, v in item.items() if v)
            elif item:
                lines.append(f"- {item}")
    elif isinstance(content, dict):
        for key, value in content.items():
            if isinstance(value, list):
                if not value:
                    continue
                lines.append(f"\n### {key}")
                for item in value:
                    if isinstance(item, dict):
                        lines.extend(f"  - {k}: {v}" for k, v in item.items() if v)
                    elif item:
                        lines.append(f"  - {item}")
            elif isinstance(value, str) and value:
                lines.append(f"- {key}: {value}")
    else:
        lines.append(str(content))

    return "\n".join(lines)


def _format_worldview_text(data: dict) -> str:
    """Format the entire worldview as readable text for prompt injection."""
    sections = []
    for name, content in data.items():
        text = _format_section(name, content)
        if text.strip():
            sections.append(text)
    return "\n\n".join(sections)


@router.get("")
def get_worldview(
    book_id: int | None = Query(None, description="Book ID for per-book worldview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return worldview settings — from book if book_id given, else legacy file."""
    if book_id is not None:
        book = book_repo.get_book_for_user(db, book_id, current_user.id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        if book.worldview:
            try:
                return json.loads(book.worldview)
            except (json.JSONDecodeError, TypeError):
                pass
        return {}
    return _read_worldview()


@router.put("")
def update_worldview(
    body: dict,
    section: str = Query(None, description="Section key to update (e.g. '背景'). If omitted, replaces the entire worldview."),
    book_id: int | None = Query(None, description="Book ID for per-book worldview"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update worldview settings."""
    if book_id is not None:
        book = book_repo.get_book_for_user(db, book_id, current_user.id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        current = {}
        if book.worldview:
            try:
                current = json.loads(book.worldview)
            except (json.JSONDecodeError, TypeError):
                pass
        if section:
            current[section] = body
        else:
            current = body
        book.worldview = json.dumps(current, ensure_ascii=False)
        db.commit()
        return current

    current = _read_worldview()
    if section:
        if section not in current:
            raise HTTPException(status_code=400, detail=f"Unknown section: {section}")
        current[section] = body
        _write_worldview(current)
        return {section: current[section]}
    else:
        _write_worldview(body)
        return _read_worldview()


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
        data = {}
        if book.worldview:
            try:
                data = json.loads(book.worldview)
            except (json.JSONDecodeError, TypeError):
                pass
    else:
        data = _read_worldview()
    text = _format_worldview_text(data)
    return {
        "text": text,
        "token_estimate": estimate_tokens(text),
        "section_count": len(data),
    }

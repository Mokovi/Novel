"""REST endpoints for Book CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.repositories import book_repo
from backend.schemas.book import BookCreate, BookResponse, BookUpdate

router = APIRouter(prefix="/api/v1/books", tags=["books"])


@router.get("", response_model=list[BookResponse])
def list_books(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all books belonging to the current user."""
    return book_repo.list_books(db, current_user.id)


@router.post("", response_model=BookResponse, status_code=201)
def create_book(
    body: BookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new book."""
    return book_repo.create_book(db, current_user.id, body)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single book by ID."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    body: BookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book's name, description, outline, worldview, or writing_style."""
    book = book_repo.update_book(db, book_id, current_user.id, body)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a book by ID."""
    deleted = book_repo.delete_book(db, book_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    return None


@router.get("/{book_id}/stats")
def get_book_stats(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregate stats for a book."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    stats = book_repo.get_book_stats(db, book_id)
    return stats


# ── Per-book worldview, writing_style, outline ────────────────


@router.get("/{book_id}/worldview")
def get_book_worldview(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a book's worldview markdown."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"worldview": book.worldview or ""}


@router.put("/{book_id}/worldview")
def update_book_worldview(
    book_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book's worldview (stored as markdown text)."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.worldview = body.get("worldview", "")
    db.commit()
    return {"worldview": book.worldview}


@router.get("/{book_id}/writing-style")
def get_book_writing_style(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a book's writing style JSON."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    import json
    if book.writing_style:
        try:
            return json.loads(book.writing_style)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


@router.put("/{book_id}/writing-style")
def update_book_writing_style(
    book_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book's writing style (stored as JSON text)."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    import json
    book.writing_style = json.dumps(body, ensure_ascii=False)
    db.commit()
    return body


@router.get("/{book_id}/outline")
def get_book_outline(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a book's outline text."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"outline": book.outline or ""}


@router.put("/{book_id}/outline")
def update_book_outline(
    book_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book's outline text."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.outline = body.get("outline", "")
    db.commit()
    return {"outline": book.outline}

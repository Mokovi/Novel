"""REST endpoints for Book CRUD."""

import io
import uuid
from pathlib import Path as FsPath

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.repositories import book_repo
from backend.schemas.book import BookCreate, BookResponse, BookUpdate

UPLOADS_DIR = FsPath(__file__).parent.parent.parent / "uploads" / "covers"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_SIZE_MB = 5
TARGET_RATIO = 3 / 4
RATIO_TOLERANCE = 0.05

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


@router.post("/{book_id}/cover")
async def upload_book_cover(
    book_id: int,
    file: UploadFile = File(...),
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from PIL import Image
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_SIZE_MB}MB.")

    try:
        img = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    w, h = img.size
    ratio = w / h
    within_tolerance = abs(ratio - TARGET_RATIO) <= RATIO_TOLERANCE

    warning = None
    if not within_tolerance and not force:
        warning = {
            "aspect_ratio": f"{w}x{h} ({ratio:.2f})",
            "expected_near": TARGET_RATIO,
            "message": f"Aspect ratio is {ratio:.2f}, expected ~{TARGET_RATIO:.2f}. Set force=true to auto-crop.",
        }

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    save_path = UPLOADS_DIR / filename

    if not within_tolerance and force:
        img = _crop_to_ratio(img, TARGET_RATIO)
        img.save(save_path)
    else:
        img.save(save_path)

    url_path = f"/uploads/covers/{filename}"
    book.cover_image = url_path
    db.commit()

    result = {"cover_image": url_path}
    if warning:
        result["warning"] = warning
    return result


def _crop_to_ratio(img, target_ratio):
    w, h = img.size
    current_ratio = w / h
    if abs(current_ratio - target_ratio) < 0.001:
        return img
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        return img.crop((0, top, w, top + new_h))


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


# ── Per-book map ───────────────────────────────────────────


@router.get("/{book_id}/map")
def get_book_map(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a book's map markdown."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"map": book.map or ""}


@router.put("/{book_id}/map")
def update_book_map(
    book_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book's map (stored as markdown text)."""
    book = book_repo.get_book_for_user(db, book_id, current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.map = body.get("map", "")
    db.commit()
    return {"map": book.map}

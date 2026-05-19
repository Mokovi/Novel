"""REST endpoints for Volume and Chapter CRUD."""

from io import BytesIO
from urllib.parse import quote
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.models.chapter import Volume
from backend.routers.deps import get_current_user
from backend.repositories import book_repo, chapter_repo
from backend.schemas.chapter import (
    ArcCreate,
    ArcReorderRequest,
    ArcResponse,
    ArcUpdate,
    ChapterCharactersUpdate,
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    CharacterBrief,
    ReorderRequest,
    VolumeCreate,
    VolumeResponse,
    VolumeUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["chapters"])


def _verify_book_access(db: Session, book_id: int, user_id: int):
    """Verify the user owns the book. Raises 404 if not."""
    book = book_repo.get_book_for_user(db, book_id, user_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# ── Volumes ────────────────────────────────────────────────


@router.get("/volumes", response_model=list[VolumeResponse])
def list_volumes(
    book_id: int = Query(..., description="Filter by book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all volumes for a book, sorted by sort_order."""
    _verify_book_access(db, book_id, current_user.id)
    return chapter_repo.list_volumes(db, book_id=book_id)


@router.post("/volumes", response_model=VolumeResponse, status_code=201)
def create_volume(
    body: VolumeCreate,
    book_id: int = Query(..., description="Book ID to create volume under"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new volume within a book."""
    _verify_book_access(db, book_id, current_user.id)
    return chapter_repo.create_volume(db, body, book_id=book_id)


@router.put("/volumes/{volume_id}", response_model=VolumeResponse)
def update_volume(
    volume_id: int,
    body: VolumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update volume title, description, or outline."""
    volume = db.get(Volume, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    _verify_book_access(db, volume.book_id, current_user.id)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(volume, key, value)
    db.commit()
    db.refresh(volume)
    return volume


@router.delete("/volumes/{volume_id}", status_code=204)
def delete_volume(
    volume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a volume and cascade-delete its chapters."""
    volume = db.get(Volume, volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    _verify_book_access(db, volume.book_id, current_user.id)
    deleted = chapter_repo.delete_volume(db, volume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Volume not found")
    return None


# ── Chapters ───────────────────────────────────────────────


@router.get("/chapters", response_model=list[ChapterResponse])
def list_chapters(
    book_id: int = Query(..., description="Filter by book ID"),
    volume_id: int | None = Query(None, description="Filter by volume ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chapters with optional volume filter and pagination."""
    _verify_book_access(db, book_id, current_user.id)
    return chapter_repo.list_chapters(db, book_id=book_id, volume_id=volume_id, skip=skip, limit=limit)


@router.post("/chapters", response_model=ChapterResponse, status_code=201)
def create_chapter(
    body: ChapterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chapter."""
    # Verify volume's book ownership
    volume = db.get(Volume, body.volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    _verify_book_access(db, volume.book_id, current_user.id)
    return chapter_repo.create_chapter(db, body)


@router.put("/chapters/reorder", status_code=204)
def reorder_chapters(
    body: ReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-update chapter sort_order values."""
    if body.items:
        first_chapter = chapter_repo.get_chapter(db, body.items[0].id)
        if first_chapter:
            volume = db.get(Volume, first_chapter.volume_id)
            if volume:
                _verify_book_access(db, volume.book_id, current_user.id)
    chapter_repo.reorder_chapters(db, body.items)
    return None


@router.get("/chapters/download-all")
def download_all_chapters(
    book_id: int = Query(..., description="Book ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download all chapters grouped by volume as a ZIP file."""
    _verify_book_access(db, book_id, current_user.id)
    volumes = chapter_repo.list_volumes(db, book_id=book_id)
    volume_map = {v.id: v.title for v in volumes}
    chapters = chapter_repo.list_chapters(db, book_id=book_id, limit=10000)

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for ch in chapters:
            vol_title = volume_map.get(ch.volume_id, "未分类")
            filename = f"{vol_title}/{ch.title}.txt"
            zf.writestr(filename, ch.content or "")

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=chapters.zip"},
    )


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
def get_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chapter detail by ID."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    return chapter


@router.get("/chapters/{chapter_id}/download")
def download_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a single chapter as a TXT file."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    filename = quote(chapter.title or f"chapter_{chapter_id}")
    return Response(
        content=chapter.content or "",
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}.txt"
        },
    )


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_id: int,
    body: ChapterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update chapter title, summary, or content."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    chapter = chapter_repo.update_chapter(db, chapter_id, body)
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=204)
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chapter by ID."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    deleted = chapter_repo.delete_chapter(db, chapter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return None


# ── Chapter-Character Associations ─────────────────────────


@router.get(
    "/chapters/{chapter_id}/characters",
    response_model=list[CharacterBrief],
)
def get_chapter_characters(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all characters associated with a chapter."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    characters = chapter_repo.get_chapter_characters(db, chapter_id)
    return characters


@router.put(
    "/chapters/{chapter_id}/characters",
    response_model=list[CharacterBrief],
)
def set_chapter_characters(
    chapter_id: int,
    body: ChapterCharactersUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set all character associations for a chapter (replaces existing)."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    volume = db.get(Volume, chapter.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    try:
        characters = chapter_repo.set_chapter_characters(db, chapter_id, body.character_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return characters


# ── Arcs ────────────────────────────────────────────────────


@router.get("/arcs", response_model=list[ArcResponse])
def list_arcs(
    book_id: int = Query(..., description="Filter by book ID"),
    volume_id: int | None = Query(None, description="Filter by volume ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all arcs for a book, optionally filtered by volume."""
    _verify_book_access(db, book_id, current_user.id)
    return chapter_repo.list_arcs_by_book(db, book_id=book_id, volume_id=volume_id)


@router.post("/arcs", response_model=ArcResponse, status_code=201)
def create_arc(
    body: ArcCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new arc."""
    volume = db.get(Volume, body.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    return chapter_repo.create_arc(db, body)


@router.put("/arcs/reorder", status_code=204)
def reorder_arcs(
    body: ArcReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-update arc sort_order values."""
    chapter_repo.reorder_arcs(db, body.items)
    return None


@router.get("/arcs/{arc_id}", response_model=ArcResponse)
def get_arc(
    arc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get arc detail by ID."""
    arc = chapter_repo.get_arc(db, arc_id)
    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")
    volume = db.get(Volume, arc.volume_id)
    if volume:
        _verify_book_access(db, volume.book_id, current_user.id)
    return arc


@router.put("/arcs/{arc_id}", response_model=ArcResponse)
def update_arc(
    arc_id: int,
    body: ArcUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update arc title, description, or outline."""
    arc = chapter_repo.update_arc(db, arc_id, body)
    if not arc:
        raise HTTPException(status_code=404, detail="Arc not found")
    return arc


@router.delete("/arcs/{arc_id}", status_code=204)
def delete_arc(
    arc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an arc (chapters' arc_id set to NULL)."""
    deleted = chapter_repo.delete_arc(db, arc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Arc not found")
    return None


# ── Book-scoped routes ─────────────────────────────────────


@router.get("/books/{book_id}/volumes", response_model=list[VolumeResponse])
def list_book_volumes(book_id: int, db: Session = Depends(get_db)):
    """Get all volumes for a book, sorted by sort_order."""
    return chapter_repo.list_volumes(db, book_id=book_id)


@router.post("/books/{book_id}/volumes", response_model=VolumeResponse, status_code=201)
def create_book_volume(book_id: int, body: VolumeCreate, db: Session = Depends(get_db)):
    """Create a new volume under a book."""
    volume = chapter_repo.create_volume(db, body)
    volume.book_id = book_id
    db.commit()
    db.refresh(volume)
    return volume


@router.get("/books/{book_id}/chapters", response_model=list[ChapterResponse])
def list_book_chapters(
    book_id: int,
    volume_id: int | None = Query(None, description="Filter by volume ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get chapters for a book, with optional volume filter."""
    return chapter_repo.list_chapters(db, volume_id=volume_id, book_id=book_id, skip=skip, limit=limit)


@router.get("/books/{book_id}/arcs", response_model=list[ArcResponse])
def list_book_arcs(
    book_id: int,
    volume_id: int | None = Query(None, description="Filter by volume ID"),
    db: Session = Depends(get_db),
):
    """Get all arcs for a book, optionally filtered by volume."""
    return chapter_repo.list_arcs(db, volume_id=volume_id, book_id=book_id)

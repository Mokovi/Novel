"""REST endpoints for Volume and Chapter CRUD."""

from io import BytesIO
from urllib.parse import quote
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories import chapter_repo
from backend.schemas.chapter import (
    ChapterCreate,
    ChapterResponse,
    ChapterUpdate,
    ReorderRequest,
    VolumeCreate,
    VolumeResponse,
)

router = APIRouter(prefix="/api/v1", tags=["chapters"])


# ── Volumes ────────────────────────────────────────────────


@router.get("/volumes", response_model=list[VolumeResponse])
def list_volumes(db: Session = Depends(get_db)):
    """Get all volumes sorted by sort_order."""
    return chapter_repo.list_volumes(db)


@router.post("/volumes", response_model=VolumeResponse, status_code=201)
def create_volume(body: VolumeCreate, db: Session = Depends(get_db)):
    """Create a new volume."""
    return chapter_repo.create_volume(db, body)


@router.delete("/volumes/{volume_id}", status_code=204)
def delete_volume(volume_id: int, db: Session = Depends(get_db)):
    """Delete a volume and cascade-delete its chapters."""
    deleted = chapter_repo.delete_volume(db, volume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Volume not found")
    return None


# ── Chapters ───────────────────────────────────────────────


@router.get("/chapters", response_model=list[ChapterResponse])
def list_chapters(
    volume_id: int | None = Query(None, description="Filter by volume ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get chapters with optional volume filter and pagination."""
    return chapter_repo.list_chapters(db, volume_id=volume_id, skip=skip, limit=limit)


@router.post("/chapters", response_model=ChapterResponse, status_code=201)
def create_chapter(body: ChapterCreate, db: Session = Depends(get_db)):
    """Create a new chapter."""
    return chapter_repo.create_chapter(db, body)


@router.put("/chapters/reorder", status_code=204)
def reorder_chapters(body: ReorderRequest, db: Session = Depends(get_db)):
    """Batch-update chapter sort_order values."""
    chapter_repo.reorder_chapters(db, body.items)
    return None


@router.get("/chapters/download-all")
def download_all_chapters(db: Session = Depends(get_db)):
    """Download all chapters grouped by volume as a ZIP file."""
    volumes = chapter_repo.list_volumes(db)
    volume_map = {v.id: v.title for v in volumes}
    chapters = chapter_repo.list_chapters(db, limit=10000)

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
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Get chapter detail by ID."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/chapters/{chapter_id}/download")
def download_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Download a single chapter as a TXT file."""
    chapter = chapter_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    filename = quote(chapter.title or f"chapter_{chapter_id}")
    return Response(
        content=chapter.content or "",
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}.txt"
        },
    )


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(chapter_id: int, body: ChapterUpdate, db: Session = Depends(get_db)):
    """Update chapter title, summary, or content."""
    chapter = chapter_repo.update_chapter(db, chapter_id, body)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=204)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Delete a chapter by ID."""
    deleted = chapter_repo.delete_chapter(db, chapter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return None

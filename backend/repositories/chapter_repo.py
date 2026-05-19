"""Repository for Volume and Chapter database operations."""

from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.models.chapter import Arc, Chapter, ChapterVersion, Volume
from backend.models.story_line import ChapterCharacter
from backend.schemas.chapter import (
    ArcCreate,
    ArcUpdate,
    ChapterCreate,
    ChapterUpdate,
    ReorderItem,
    VolumeCreate,
)


def list_volumes(db: Session, book_id: int | None = None) -> list[Volume]:
    query = db.query(Volume)
    if book_id is not None:
        query = query.filter(Volume.book_id == book_id)
    return query.order_by(Volume.sort_order, Volume.id).all()


def create_volume(db: Session, data: VolumeCreate, book_id: int = 1) -> Volume:
    volume = Volume(**data.model_dump(), book_id=book_id)
    db.add(volume)
    db.commit()
    db.refresh(volume)
    return volume


def list_chapters(
    db: Session,
    book_id: int | None = None,
    volume_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Chapter]:
    query = db.query(Chapter).join(Volume)
    if book_id is not None:
        query = query.filter(Volume.book_id == book_id)
    if volume_id is not None:
        query = query.filter(Chapter.volume_id == volume_id)
    return query.order_by(Chapter.sort_order, Chapter.id).offset(skip).limit(limit).all()


def get_chapter(db: Session, chapter_id: int) -> Optional[Chapter]:
    return db.get(Chapter, chapter_id)


def create_chapter(db: Session, data: ChapterCreate) -> Chapter:
    chapter = Chapter(**data.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


def update_chapter(db: Session, chapter_id: int, data: ChapterUpdate) -> Optional[Chapter]:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return chapter
    for key, value in update_data.items():
        setattr(chapter, key, value)
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, chapter_id: int) -> bool:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        return False
    db.delete(chapter)
    db.commit()
    return True


def save_generated_content(
    db: Session,
    chapter_id: int,
    content: str,
    word_count: int,
    prompt_snapshot: str,
    model_used: str,
) -> Chapter:
    """Save generated content: create ChapterVersion and update Chapter."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise ValueError(f"Chapter {chapter_id} not found")

    # Create version record
    version = ChapterVersion(
        chapter_id=chapter_id,
        content=content,
        word_count=word_count,
        prompt_snapshot=prompt_snapshot,
        model_used=model_used,
        version_type="generated",
    )
    db.add(version)

    # Update chapter
    chapter.content = content
    chapter.word_count = word_count
    chapter.status = "completed"
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_volume(db: Session, volume_id: int) -> bool:
    volume = db.get(Volume, volume_id)
    if not volume:
        return False
    db.delete(volume)
    db.commit()
    return True


def reorder_chapters(db: Session, items: list[ReorderItem]) -> None:
    for item in items:
        db.execute(
            update(Chapter)
            .where(Chapter.id == item.id)
            .values(sort_order=item.sort_order)
        )
    db.commit()


def get_chapter_characters(db: Session, chapter_id: int) -> list:
    """Get all characters associated with a chapter."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        return []
    return [cc.character for cc in chapter.character_associations]


def save_chapter_ai_summary(db: Session, chapter_id: int, ai_summary: str) -> bool:
    """Update a chapter's ai_summary field. Returns True if found, False otherwise."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        return False
    chapter.ai_summary = ai_summary
    db.commit()
    return True


def get_previous_chapter_summaries(
    db: Session, chapter_id: int, count: int
) -> list[str]:
    """Get AI summaries from the previous *count* chapters (same volume, earlier sort_order)."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        return []

    summaries = (
        db.query(Chapter.ai_summary)
        .filter(
            Chapter.volume_id == chapter.volume_id,
            Chapter.sort_order < chapter.sort_order,
            Chapter.ai_summary.isnot(None),
            Chapter.ai_summary != "",
        )
        .order_by(Chapter.sort_order.desc())
        .limit(count)
        .all()
    )
    # Reverse to get chronological order
    return [s[0] for s in reversed(summaries)]



def set_chapter_characters(db: Session, chapter_id: int, character_ids: list[int]) -> list:
    """Replace all character associations for a chapter. Returns the new list of characters."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise ValueError(f"Chapter {chapter_id} not found")

    # Remove existing associations
    db.query(ChapterCharacter).filter(
        ChapterCharacter.chapter_id == chapter_id
    ).delete()

    # Add new associations
    for cid in character_ids:
        assoc = ChapterCharacter(chapter_id=chapter_id, character_id=cid)
        db.add(assoc)

    db.commit()
    db.refresh(chapter)
    return [cc.character for cc in chapter.character_associations]


# ── Arc CRUD ───────────────────────────────────────────────


def list_arcs(db: Session, volume_id: Optional[int] = None) -> list[Arc]:
    query = db.query(Arc)
    if volume_id is not None:
        query = query.filter(Arc.volume_id == volume_id)
    return query.order_by(Arc.sort_order, Arc.id).all()


def list_arcs_by_book(db: Session, book_id: int, volume_id: int | None = None) -> list[Arc]:
    """List arcs filtered by book (and optionally volume)."""
    query = db.query(Arc).join(Volume, Arc.volume_id == Volume.id).filter(Volume.book_id == book_id)
    if volume_id is not None:
        query = query.filter(Arc.volume_id == volume_id)
    return query.order_by(Arc.sort_order, Arc.id).all()


def create_arc(db: Session, data: ArcCreate) -> Arc:
    arc = Arc(**data.model_dump())
    db.add(arc)
    db.commit()
    db.refresh(arc)
    return arc


def get_arc(db: Session, arc_id: int) -> Optional[Arc]:
    return db.get(Arc, arc_id)


def update_arc(db: Session, arc_id: int, data: ArcUpdate) -> Optional[Arc]:
    arc = db.get(Arc, arc_id)
    if not arc:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return arc
    for key, value in update_data.items():
        setattr(arc, key, value)
    db.commit()
    db.refresh(arc)
    return arc


def delete_arc(db: Session, arc_id: int) -> bool:
    arc = db.get(Arc, arc_id)
    if not arc:
        return False
    db.delete(arc)
    db.commit()
    return True


def reorder_arcs(db: Session, items: list) -> None:
    for item in items:
        db.execute(
            update(Arc)
            .where(Arc.id == item.id)
            .values(sort_order=item.sort_order)
        )
    db.commit()


# ── Outline helper queries ─────────────────────────────────


def save_arc_outline(db: Session, arc_id: int, outline: str) -> bool:
    arc = db.get(Arc, arc_id)
    if not arc:
        return False
    arc.outline = outline
    db.commit()
    return True


def save_volume_outline(db: Session, volume_id: int, outline: str) -> bool:
    volume = db.get(Volume, volume_id)
    if not volume:
        return False
    volume.outline = outline
    db.commit()
    return True


def get_arc_chapter_summaries(db: Session, arc_id: int) -> list[dict]:
    """Get all chapters in an arc with their title, summary, and ai_summary."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.arc_id == arc_id)
        .order_by(Chapter.sort_order, Chapter.id)
        .all()
    )
    return [
        {
            "title": c.title or "",
            "summary": c.summary or "",
            "ai_summary": c.ai_summary or "",
        }
        for c in chapters
    ]


def get_volume_arc_outlines(db: Session, volume_id: int) -> list[dict]:
    """Get all arcs in a volume with their outline and chapter summaries."""
    arcs = (
        db.query(Arc)
        .filter(Arc.volume_id == volume_id)
        .order_by(Arc.sort_order, Arc.id)
        .all()
    )
    result = []
    for arc in arcs:
        chapters = get_arc_chapter_summaries(db, arc.id)
        result.append({
            "arc_id": arc.id,
            "arc_title": arc.title or "",
            "arc_description": arc.description or "",
            "arc_outline": arc.outline or "",
            "chapters": chapters,
        })
    return result


def get_all_volume_outlines(db: Session, book_id: int | None = None) -> list[dict]:
    """Get all volumes with their outline for book-level generation."""
    query = db.query(Volume).order_by(Volume.sort_order, Volume.id)
    if book_id is not None:
        query = query.filter(Volume.book_id == book_id)
    volumes = query.all()
    return [
        {
            "volume_id": v.id,
            "volume_title": v.title or "",
            "volume_description": v.description or "",
            "volume_outline": v.outline or "",
        }
        for v in volumes
    ]

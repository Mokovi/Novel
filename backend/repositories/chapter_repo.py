"""Repository for Volume and Chapter database operations."""

from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from backend.models.chapter import Chapter, ChapterVersion, Volume
from backend.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ReorderItem,
    VolumeCreate,
)


def list_volumes(db: Session) -> list[Volume]:
    return db.query(Volume).order_by(Volume.sort_order, Volume.id).all()


def create_volume(db: Session, data: VolumeCreate) -> Volume:
    volume = Volume(**data.model_dump())
    db.add(volume)
    db.commit()
    db.refresh(volume)
    return volume


def list_chapters(
    db: Session,
    volume_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Chapter]:
    query = db.query(Chapter)
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

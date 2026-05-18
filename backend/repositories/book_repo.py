"""Repository for Book database operations."""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.book import Book
from backend.models.chapter import Chapter, Volume
from backend.models.character import Character
from backend.schemas.book import BookCreate, BookUpdate


def list_books(db: Session) -> list[Book]:
    return db.query(Book).order_by(Book.updated_at.desc()).all()


def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.get(Book, book_id)


def create_book(db: Session, data: BookCreate) -> Book:
    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, data: BookUpdate) -> Optional[Book]:
    book = db.get(Book, book_id)
    if not book:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return book
    for key, value in update_data.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> bool:
    book = db.get(Book, book_id)
    if not book:
        return False
    db.delete(book)
    db.commit()
    return True


def get_book_stats(db: Session, book_id: int) -> dict:
    """Return aggregate stats for a book."""
    volume_count = (
        db.query(func.count(Volume.id))
        .filter(Volume.book_id == book_id)
        .scalar()
        or 0
    )
    chapter_count = (
        db.query(func.count(Chapter.id))
        .join(Volume, Chapter.volume_id == Volume.id)
        .filter(Volume.book_id == book_id)
        .scalar()
        or 0
    )
    character_count = (
        db.query(func.count(Character.id))
        .filter(Character.book_id == book_id)
        .scalar()
        or 0
    )
    return {
        "volume_count": volume_count,
        "chapter_count": chapter_count,
        "character_count": character_count,
    }

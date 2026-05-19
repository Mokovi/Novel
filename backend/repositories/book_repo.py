"""Repository for Book database operations."""

from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.book import Book
from backend.models.chapter import Volume
from backend.schemas.book import BookCreate, BookUpdate


def list_books(db: Session, user_id: int) -> list[Book]:
    return db.query(Book).filter(Book.user_id == user_id).order_by(Book.id).all()


def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.get(Book, book_id)


def get_book_for_user(db: Session, book_id: int, user_id: int) -> Optional[Book]:
    return (
        db.query(Book)
        .filter(Book.id == book_id, Book.user_id == user_id)
        .first()
    )


def create_book(db: Session, user_id: int, data: BookCreate) -> Book:
    book = Book(user_id=user_id, **data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book_id: int, user_id: int, data: BookUpdate) -> Optional[Book]:
    book = get_book_for_user(db, book_id, user_id)
    if not book:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return book
    for key, value in update_data.items():
        if value is not None:
            setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int, user_id: int) -> bool:
    book = get_book_for_user(db, book_id, user_id)
    if not book:
        return False
    if book.cover_image:
        cover_path = Path(__file__).parent.parent.parent / book.cover_image.lstrip("/")
        if cover_path.exists():
            cover_path.unlink()
    db.delete(book)
    db.commit()
    return True


def get_book_stats(db: Session, book_id: int) -> dict:
    """Return aggregate stats for a book."""
    volume_count = (
        db.query(Volume).filter(Volume.book_id == book_id).count()
    )
    return {
        "volume_count": volume_count,
    }

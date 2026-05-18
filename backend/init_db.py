#!/usr/bin/env python3
"""Database initialization script — creates all tables and applies migrations."""

import json
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa
from sqlalchemy import inspect, text

from backend.database import Base, engine, DATABASE_PATH, SessionLocal
from backend.models import (  # noqa: F401 — registers all models on Base.metadata
    ApiPlan,
    Arc,
    Book,
    Chapter,
    ChapterCharacter,
    ChapterStoryLine,
    ChapterVersion,
    Character,
    CharacterRelation,
    EventParticipant,
    Item,
    ItemOwnershipHistory,
    ModelApi,
    PlanApi,
    StoryLine,
    TaskPlanBinding,
    Volume,
    WorldEvent,
)
from backend.config import DATA_DIR


def _add_column(table: str, column_name: str, type_clause: str):
    """Add a column if it doesn't already exist (SQLite-compatible)."""
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns(table)}
    if column_name not in existing:
        with engine.connect() as conn:
            conn.execute(
                sa.text(f"ALTER TABLE {table} ADD COLUMN {column_name} {type_clause}")
            )
            conn.commit()
        print(f"  + Added column {table}.{column_name}")


def _has_rows(table: str) -> bool:
    """Check if a table has any rows."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return result.scalar() > 0


def _read_json_file(path: Path) -> str:
    """Read a JSON file and return its content as a JSON string, or '{}'/'""."""
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    return "{}" if path.suffix == ".json" else ""


def main():
    print(f"Database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("New tables created (if any).")

    # Manual migrations for columns added to existing tables
    print("Applying schema migrations...")
    _add_column("volumes", "outline", "TEXT")
    _add_column("chapters", "arc_id", "INTEGER REFERENCES arcs(id) ON DELETE SET NULL")
    _add_column("volumes", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("characters", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("world_events", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("items", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("story_lines", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")

    # Create default book from existing disk files if no books exist
    db = SessionLocal()
    try:
        existing_books = db.query(Book).count()
        if existing_books == 0:
            print("Migrating existing data to default book...")

            worldview_raw = _read_json_file(DATA_DIR / "worldview.json")
            writing_style_raw = _read_json_file(DATA_DIR / "writing_style.json")

            # Read book outline from config.json
            config_path = DATA_DIR / "config.json"
            book_outline = ""
            if config_path.exists():
                try:
                    cfg = json.loads(config_path.read_text(encoding="utf-8"))
                    book_outline = cfg.get("book_outline", "")
                except (json.JSONDecodeError, Exception):
                    pass

            default_book = Book(
                name="未命名作品",
                description="",
                outline=book_outline or None,
                worldview=worldview_raw if worldview_raw.strip("{} \n") else None,
                writing_style=writing_style_raw if writing_style_raw.strip("{} \n") else None,
            )
            db.add(default_book)
            db.commit()
            db.refresh(default_book)
            print(f"  Created default book: id={default_book.id}, name={default_book.name}")

            # Update all existing rows to point to the default book
            for table in ("volumes", "characters", "world_events", "items", "story_lines"):
                if _has_rows(table):
                    db.execute(
                        text(
                            f"UPDATE {table} SET book_id = :book_id WHERE book_id IS NULL"
                        ),
                        {"book_id": default_book.id},
                    )
                    print(f"  Updated existing {table} rows -> book_id={default_book.id}")
            db.commit()
        else:
            print(f"  Found {existing_books} existing book(s), skipping migration.")
    finally:
        db.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    main()

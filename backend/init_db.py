#!/usr/bin/env python3
"""Database initialization script — creates all tables and applies migrations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from backend.database import Base, engine, DATABASE_PATH
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
    User,
    Volume,
    WorldEvent,
)
from backend.services.auth import hash_password


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


def _has_table(name: str) -> bool:
    inspector = inspect(engine)
    return name in inspector.get_table_names()


def main():
    print(f"Database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("New tables created (if any).")

    # Manual migrations for columns added to existing tables
    print("Applying schema migrations...")
    _add_column("volumes", "outline", "TEXT")
    _add_column("chapters", "arc_id", "INTEGER REFERENCES arcs(id) ON DELETE SET NULL")

    # Book-book_id columns
    _add_column("volumes", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("characters", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("world_events", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("items", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")
    _add_column("story_lines", "book_id", "INTEGER REFERENCES books(id) ON DELETE CASCADE")

    # User_id columns
    _add_column("model_apis", "user_id", "INTEGER REFERENCES users(id) ON DELETE CASCADE")
    _add_column("api_plans", "user_id", "INTEGER REFERENCES users(id) ON DELETE CASCADE")

    # Seed default admin user if not exists
    db = Session(engine)
    try:
        existing_user = db.query(User).filter(User.username == "admin").first()
        if not existing_user:
            user = User(
                username="admin",
                password_hash=hash_password("admin123"),
            )
            db.add(user)
            db.flush()
            print(f"  + Seeded default admin user (id={user.id})")

            # Create a default book for the admin user
            book = Book(
                user_id=user.id,
                name="默认作品",
                description="自动创建的默认作品",
            )
            db.add(book)
            db.flush()
            print(f"  + Created default book (id={book.id})")

            # Backfill existing volumes with default book_id
            db.execute(
                sa.text("UPDATE volumes SET book_id = :bid WHERE book_id IS NULL"),
                {"bid": book.id},
            )
            db.execute(
                sa.text("UPDATE characters SET book_id = :bid WHERE book_id IS NULL"),
                {"bid": book.id},
            )
            db.execute(
                sa.text("UPDATE world_events SET book_id = :bid WHERE book_id IS NULL"),
                {"bid": book.id},
            )
            db.execute(
                sa.text("UPDATE items SET book_id = :bid WHERE book_id IS NULL"),
                {"bid": book.id},
            )
            db.execute(
                sa.text("UPDATE story_lines SET book_id = :bid WHERE book_id IS NULL"),
                {"bid": book.id},
            )

            # Backfill existing model_apis and api_plans with default user_id
            db.execute(
                sa.text("UPDATE model_apis SET user_id = :uid WHERE user_id IS NULL"),
                {"uid": user.id},
            )
            db.execute(
                sa.text("UPDATE api_plans SET user_id = :uid WHERE user_id IS NULL"),
                {"uid": user.id},
            )

            db.commit()
            print("  + Backfilled existing data with default user/book IDs")
        else:
            print("  - Admin user already exists, skipping seed")

        # Ensure all volumes have book_id set (in case backfill ran on partial data)
        db.execute(
            sa.text(
                "UPDATE volumes SET book_id = (SELECT MIN(id) FROM books) "
                "WHERE book_id IS NULL"
            )
        )
        db.commit()
    finally:
        db.close()

    # Migrate legacy worldview.json → first book if book has no worldview
    worldview_path = Path(__file__).resolve().parent.parent / "data" / "worldview.json"
    if worldview_path.exists():
        db2 = Session(engine)
        try:
            first_book = db2.query(Book).order_by(Book.id).first()
            if first_book and not first_book.worldview:
                import json as _json
                try:
                    legacy = _json.loads(worldview_path.read_text(encoding="utf-8"))
                    if legacy:
                        first_book.worldview = _json.dumps(legacy, ensure_ascii=False)
                        db2.commit()
                        print(f"  + Migrated worldview.json to book id={first_book.id}")
                except (_json.JSONDecodeError, Exception) as e:
                    print(f"  ~ worldview.json migration skipped: {e}")
        finally:
            db2.close()

    print("Database initialization complete.")


if __name__ == "__main__":
    main()

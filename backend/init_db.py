#!/usr/bin/env python3
"""Database initialization script — creates all tables and applies migrations."""

import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa
from sqlalchemy import inspect

from backend.database import Base, engine, DATABASE_PATH
from backend.models import (  # noqa: F401 — registers all models on Base.metadata
    ApiPlan,
    Arc,
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


def main():
    print(f"Database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("New tables created (if any).")

    # Manual migrations for columns added to existing tables
    print("Applying schema migrations...")
    _add_column("volumes", "outline", "TEXT")
    _add_column("chapters", "arc_id", "INTEGER REFERENCES arcs(id) ON DELETE SET NULL")

    print("Database initialization complete.")


if __name__ == "__main__":
    main()

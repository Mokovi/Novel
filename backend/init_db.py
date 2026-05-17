#!/usr/bin/env python3
"""Database initialization script — creates all tables."""

import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import Base, engine, DATABASE_PATH
from backend.models import (  # noqa: F401 — registers all models on Base.metadata
    Chapter,
    ChapterCharacter,
    ChapterStoryLine,
    ChapterVersion,
    Character,
    CharacterRelation,
    EventParticipant,
    Item,
    ItemOwnershipHistory,
    ModelRoute,
    StoryLine,
    Volume,
    WorldEvent,
)


PRESEED_TASK_KEYS = [
    "outline_design",
    "chapter_writing",
    "character_design",
    "worldbuilding",
    "revision",
]


def _seed_model_routes():
    """Insert placeholder rows for predefined task keys if they don't exist."""
    from backend.database import SessionLocal
    from backend.models.model_route import ModelRoute

    db = SessionLocal()
    try:
        existing = {r.task_key for r in db.query(ModelRoute).all()}
        for key in PRESEED_TASK_KEYS:
            if key not in existing:
                db.add(ModelRoute(task_key=key))
        db.commit()
        print(f"Seeded {len(PRESEED_TASK_KEYS)} model route presets.")
    finally:
        db.close()


def main():
    print(f"Creating database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")
    _seed_model_routes()
    print("Database initialization complete.")


if __name__ == "__main__":
    main()

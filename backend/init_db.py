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


def main():
    print(f"Creating database at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    main()

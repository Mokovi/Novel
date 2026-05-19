"""Migrate existing JSON worldview data to markdown format.

Run once after updating to the worldview markdown storage system.
For each book, if world view is stored as JSON, convert it to markdown text.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import SessionLocal
from backend.models.book import Book


def _format_worldview_text_dict(data: dict) -> str:
    """Format worldview dict as readable markdown text."""

    def _format_section(name: str, content) -> str:
        lines = [f"## {name}"]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    lines.extend(f"- {k}: {v}" for k, v in item.items() if v)
                elif item:
                    lines.append(f"- {item}")
        elif isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list):
                    if not value:
                        continue
                    lines.append(f"\n### {key}")
                    for item in value:
                        if isinstance(item, dict):
                            lines.extend(f"  - {k}: {v}" for k, v in item.items() if v)
                        elif item:
                            lines.append(f"  - {item}")
                elif isinstance(value, str) and value:
                    lines.append(f"- {key}: {value}")
        else:
            lines.append(str(content))
        return "\n".join(lines)

    sections = []
    for name, content in data.items():
        text = _format_section(name, content)
        if text.strip():
            sections.append(text)
    return "\n\n".join(sections)


def migrate():
    db = SessionLocal()
    try:
        books = db.query(Book).all()
        migrated = 0
        for book in books:
            if not book.worldview:
                continue
            try:
                parsed = json.loads(book.worldview)
                if isinstance(parsed, dict):
                    book.worldview = _format_worldview_text_dict(parsed)
                    migrated += 1
                    print(f"  Book {book.id} ('{book.name}'): converted JSON to markdown ({len(book.worldview)} chars)")
                else:
                    print(f"  Book {book.id} ('{book.name}'): already plain text (skipped)")
            except (json.JSONDecodeError, TypeError):
                print(f"  Book {book.id} ('{book.name}'): already plain text (skipped)")
        db.commit()
        print(f"\nMigration complete. {migrated} book(s) converted.")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

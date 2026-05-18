"""StoryLine, ChapterStoryLine, and ChapterCharacter ORM models."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class StoryLine(Base):
    __tablename__ = "story_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_type: Mapped[str] = mapped_column(
        String(20), default="main", nullable=False
    )
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chapter_associations: Mapped[list["ChapterStoryLine"]] = relationship(
        "ChapterStoryLine",
        back_populates="story_line",
        cascade="all, delete-orphan",
    )


class ChapterStoryLine(Base):
    __tablename__ = "chapter_story_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    story_line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("story_lines.id", ondelete="CASCADE"), nullable=False
    )

    story_line: Mapped["StoryLine"] = relationship(
        "StoryLine", back_populates="chapter_associations"
    )


class ChapterCharacter(Base):
    __tablename__ = "chapter_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False
    )

    chapter: Mapped["Chapter"] = relationship("Chapter", back_populates="character_associations")
    character: Mapped["Character"] = relationship("Character")

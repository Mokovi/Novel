"""WorldEvent and EventParticipant ORM models."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class WorldEvent(Base):
    __tablename__ = "world_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    event_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    participants: Mapped[list["EventParticipant"]] = relationship(
        "EventParticipant", back_populates="event", cascade="all, delete-orphan"
    )


class EventParticipant(Base):
    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("world_events.id", ondelete="CASCADE"), nullable=False
    )
    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    event: Mapped["WorldEvent"] = relationship(
        "WorldEvent", back_populates="participants"
    )

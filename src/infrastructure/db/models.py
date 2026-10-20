from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base


class Place(Base):
    """Площадка проведения мероприятий."""

    __tablename__ = "places"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    seats_pattern: Mapped[str] = mapped_column(Text, nullable=False)

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    events: Mapped[list[Event]] = relationship(
        back_populates="place",
        lazy="raise",
    )

    __table_args__ = (Index("ix_places_changed_at", "changed_at"),)


class Event(Base):
    """Мероприятие из Events Provider API."""

    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    place_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("places.id", ondelete="RESTRICT"),
        nullable=False,
    )

    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    number_of_visitors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    place: Mapped[Place] = relationship(
        back_populates="events",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_events_event_time_id", "event_time", "id"),
        Index("ix_events_status", "status"),
        Index("ix_events_changed_at", "changed_at"),
    )


class SyncState(Base):
    """Состояние синхронизации с внешним провайдером."""

    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    last_sync_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="never",
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_cursor_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

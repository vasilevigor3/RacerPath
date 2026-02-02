"""Penalty model: penalty records per participation (time, drive-through, stop-and-go, DSQ)."""

from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PenaltyType(str, Enum):
    """Penalty type codes (stored as string in DB)."""
    time_penalty = "time_penalty"       # +5s, +10s, etc.
    drive_through = "drive_through"     # go through pit lane
    stop_and_go = "stop_and_go"         # stop in pit
    dsq = "dsq"                         # disqualification


class Penalty(Base):
    __tablename__ = "penalties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    participation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("participations.id"), nullable=False, index=True
    )
    penalty_type: Mapped[str] = mapped_column(String(32), nullable=False)
    time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

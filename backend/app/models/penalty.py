"""Penalty model: penalty records per incident (time, drive-through, stop-and-go, DSQ). Participation via incident."""

from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    incident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    penalty_type: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # UI/result only; CRS uses Incident.score
    time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="penalties")

    @property
    def participation_id(self) -> str:
        """Derived from incident for API/backward compatibility."""
        return self.incident.participation_id

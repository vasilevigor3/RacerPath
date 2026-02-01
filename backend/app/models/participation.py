from __future__ import annotations

from datetime import datetime
import uuid
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Discipline(str, Enum):
    formula = "formula"
    gt = "gt"
    rally = "rally"
    karting = "karting"
    historic = "historic"


class ParticipationStatus(str, Enum):
    finished = "finished"
    dnf = "dnf"
    dsq = "dsq"
    dns = "dns"


class ParticipationState(str, Enum):
    registered = "registered"
    withdrawn = "withdrawn"
    started = "started"
    completed = "completed"


class Participation(Base):
    __tablename__ = "participations"
    __table_args__ = (
        UniqueConstraint("driver_id", "event_id", name="uq_participations_driver_event"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.id"), nullable=False, index=True)
    classification_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("classifications.id", ondelete="SET NULL"), nullable=True, index=True
    )

    discipline: Mapped[Discipline] = mapped_column(
        SAEnum(Discipline, name="discipline_enum"),
        nullable=False,
    )

    status: Mapped[ParticipationStatus] = mapped_column(
        SAEnum(ParticipationStatus, name="participation_status_enum"),
        nullable=False,
        server_default="finished",
    )

    participation_state: Mapped[ParticipationState] = mapped_column(
        SAEnum(ParticipationState, name="participation_state_enum"),
        nullable=False,
        server_default="registered",
    )

    position_overall: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_class: Mapped[int | None] = mapped_column(Integer, nullable=True)

    laps_completed: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    incidents_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    penalties_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    pace_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    consistency_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    @property
    def duration_minutes(self) -> int | None:
        if not self.started_at or not self.finished_at:
            return None
        delta = self.finished_at - self.started_at
        return abs(int(delta.total_seconds() // 60))

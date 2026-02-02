from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskCompletion(Base):
    __tablename__ = "task_completions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_definitions.id"), nullable=False)
    participation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("participations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    notes: Mapped[str | None] = mapped_column(String(240), nullable=True)
    event_signature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    score_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    # periodic: YYYY-MM-DD (daily), YYYY-Www (weekly), YYYY-MM (monthly)
    period_key: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # for rolling_window / audit: list of participation_id or aggregates
    achieved_by: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    # when event finished but requirements not met: status -> in_progress
    evaluation_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evaluation_failure_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of str

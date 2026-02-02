from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskDefinition(Base):
    __tablename__ = "task_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    min_event_tier: Mapped[str] = mapped_column(String(10), nullable=True)
    max_event_tier: Mapped[str] = mapped_column(String(10), nullable=True)
    min_duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_incidents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_penalties: Mapped[int | None] = mapped_column(Integer, nullable=True)
    require_night: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    require_dynamic_weather: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    require_team_event: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    require_clean_finish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_non_finish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_position_overall: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_position_overall: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_laps_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repeatable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_completions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooldown_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    diversity_window_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_same_event_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    require_event_diversity: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    max_same_signature_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signature_cooldown_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    diminishing_returns: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    diminishing_step: Mapped[float | None] = mapped_column(Float, nullable=True)
    diminishing_floor: Mapped[float | None] = mapped_column(Float, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    event_related: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="per_participation")
    cooldown_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period: Mapped[str | None] = mapped_column(String(16), nullable=True)
    window_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
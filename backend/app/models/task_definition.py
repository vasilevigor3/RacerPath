from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
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
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # scope: how task is counted (global once, per participation, rolling window, periodic)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="per_participation")
    cooldown_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period: Mapped[str | None] = mapped_column(String(16), nullable=True)  # daily, weekly, monthly
    window_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # participations, days
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    readiness_status: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    inputs_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    algo_version: Mapped[str] = mapped_column(String(32), nullable=False, default="rec_v1")
    computed_from_participation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("participations.id", ondelete="SET NULL"), nullable=True
    )
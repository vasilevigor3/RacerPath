from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Classification(Base):
    __tablename__ = "classifications"
    __table_args__ = (UniqueConstraint("event_id", name="uq_classifications_event_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id: Mapped[str] = mapped_column(String(36), ForeignKey("events.id"), nullable=False)
    event_tier: Mapped[str] = mapped_column(String(10), nullable=False)
    tier_label: Mapped[str] = mapped_column(String(40), nullable=False)
    difficulty_score: Mapped[float] = mapped_column(Float, nullable=False)
    seriousness_score: Mapped[float] = mapped_column(Float, nullable=False)
    realism_score: Mapped[float] = mapped_column(Float, nullable=False)
    discipline_compatibility: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    caps_applied: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    classification_version: Mapped[str] = mapped_column(String(20), nullable=False)
    inputs_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    inputs_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

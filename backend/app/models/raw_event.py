from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    source_event_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    normalized_event: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    event_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("events.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    participation_id: Mapped[str] = mapped_column(String(36), ForeignKey("participations.id"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    lap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
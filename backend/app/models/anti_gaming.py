from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AntiGamingReport(Base):
    __tablename__ = "anti_gaming_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
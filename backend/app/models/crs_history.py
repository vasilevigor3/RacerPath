from datetime import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CRSHistory(Base):
    __tablename__ = "crs_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
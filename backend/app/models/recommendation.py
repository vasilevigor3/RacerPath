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
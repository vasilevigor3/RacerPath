from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DriverLicense(Base):
    __tablename__ = "driver_licenses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_id: Mapped[str] = mapped_column(String(36), ForeignKey("drivers.id"), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    level_code: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="earned")
    awarded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
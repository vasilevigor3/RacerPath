from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RealWorldFormat(Base):
    __tablename__ = "real_world_formats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    min_crs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    required_license_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    required_task_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    required_event_tiers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    primary_discipline: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sim_platforms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    rig: Mapped[str | None] = mapped_column(String(120), nullable=True)
    goals: Mapped[str | None] = mapped_column(String(240), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

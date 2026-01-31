from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    primary_discipline: Mapped[str] = mapped_column(String(40), nullable=False)
    sim_games: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

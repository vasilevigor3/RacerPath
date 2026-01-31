from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TaskDefinition(Base):
    __tablename__ = "task_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    discipline: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    min_event_tier: Mapped[str] = mapped_column(String(10), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
"""Tier progression rules: min_events with difficulty_score > threshold to advance to next tier."""

from sqlalchemy import CheckConstraint, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

TIER_VALUES = ("E0", "E1", "E2", "E3", "E4", "E5")


class TierProgressionRule(Base):
    __tablename__ = "tier_progression_rules"
    __table_args__ = (
        CheckConstraint(
            "tier IN ('E0', 'E1', 'E2', 'E3', 'E4', 'E5')",
            name="ck_tier_progression_rules_tier",
        ),
    )

    tier: Mapped[str] = mapped_column(String(10), primary_key=True)
    min_events: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    difficulty_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    required_license_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

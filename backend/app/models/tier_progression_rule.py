"""Tier progression rules: minimum number of events with classification.difficulty_score > threshold."""

from sqlalchemy import CheckConstraint, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.core.constants import VALID_TIERS


class TierProgressionRule(Base):
    """
    Rule for advancing from this tier to the next.
    - min_events: minimum number of finished events required where
      event's classification.difficulty_score > difficulty_threshold.
    - difficulty_threshold: only events with difficulty_score strictly above this count.
    - required_license_codes: license level_codes the driver must have earned.
    """

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

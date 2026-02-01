"""Progress toward next tier: events with classification.difficulty_score > tier rule threshold + licenses."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.event import Event
from app.models.participation import Participation, ParticipationStatus
from app.models.tier_progression_rule import TierProgressionRule

TIER_TOP = "E5"


def compute_next_tier_progress(session: Session, user_id: str) -> tuple[int, dict[str, Any] | None]:
    """
    Progress (0–100) toward next driver tier and data about what's missing.
    - Driver's current tier has a rule: min_events, difficulty_threshold, required_license_codes.
    - Count finished participations where event's classification.difficulty_score > difficulty_threshold.
    - progress = min(100, count / min_events * 100).
    - next_tier_data: events_done, events_required, difficulty_threshold, missing_license_codes.
    - If tier is E5 or no rule, return (100, None).
    """
    driver = session.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        return 0, None

    tier = (driver.tier or "E0").strip()
    if tier == TIER_TOP:
        return 100, None

    rule = session.query(TierProgressionRule).filter(TierProgressionRule.tier == tier).first()
    if not rule or rule.min_events <= 0:
        return 0, {
            "events_done": 0,
            "events_required": rule.min_events if rule else 0,
            "difficulty_threshold": rule.difficulty_threshold if rule else 0.0,
            "missing_license_codes": list(rule.required_license_codes or []) if rule else [],
        }

    # Count finished participations where event has classification with difficulty_score > threshold
    count = (
        session.query(Participation.id)
        .join(Event, Participation.event_id == Event.id)
        .join(Classification, Classification.event_id == Event.id)
        .filter(
            Participation.driver_id == driver.id,
            Participation.status == ParticipationStatus.finished,
            Classification.difficulty_score > rule.difficulty_threshold,
        )
        .count()
    )

    # Driver's earned license level_codes
    driver_codes = {
        row[0]
        for row in session.query(DriverLicense.level_code)
        .filter(DriverLicense.driver_id == driver.id, DriverLicense.status == "earned")
        .all()
    }
    required_codes = list(rule.required_license_codes or [])
    missing_license_codes = [c for c in required_codes if c not in driver_codes]

    progress = min(100, int(round(count / rule.min_events * 100)))
    next_tier_data = {
        "events_done": count,
        "events_required": rule.min_events,
        "difficulty_threshold": rule.difficulty_threshold,
        "missing_license_codes": missing_license_codes,
    }
    return progress, next_tier_data

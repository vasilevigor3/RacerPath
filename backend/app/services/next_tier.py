"""Progress toward next tier: min number of events with classification.difficulty_score > threshold."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.event import Event
from app.models.participation import Participation, ParticipationState, ParticipationStatus
from app.models.tier_progression_rule import TierProgressionRule

from app.core.constants import TIER_ORDER, TIER_TOP


def _next_tier(current: str) -> str | None:
    """Next tier after current (E0->E1, ..., E4->E5). None if current is E5."""
    t = (current or "E0").strip()
    if t == TIER_TOP:
        return None
    try:
        i = TIER_ORDER.index(t)
        if i + 1 < len(TIER_ORDER):
            return TIER_ORDER[i + 1]
    except ValueError:
        pass
    return None


def compute_next_tier_progress(
    session: Session, user_id: str, driver_id: str | None = None
) -> tuple[int, dict[str, Any] | None]:
    """
    Progress (0–100) toward next driver tier for the given driver.
    If driver_id is provided and belongs to user_id, use that driver; else use first driver for user.
    """
    if driver_id:
        driver = session.query(Driver).filter(Driver.id == driver_id, Driver.user_id == user_id).first()
    else:
        driver = (
            session.query(Driver)
            .filter(Driver.user_id == user_id)
            .order_by(Driver.created_at.desc())
            .first()
        )
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

    # Count finished events (only completed races; registered/withdrawn do not count)
    count = (
        session.query(Participation.id)
        .join(Event, Participation.event_id == Event.id)
        .join(Classification, Classification.event_id == Event.id)
        .filter(
            Participation.driver_id == driver.id,
            Participation.participation_state == ParticipationState.completed,
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

    # Auto-promote when progress is 100% and all required licenses are earned
    if progress >= 100 and not missing_license_codes:
        next_t = _next_tier(driver.tier or "E0")
        if next_t:
            driver.tier = next_t
            session.commit()
            session.refresh(driver)

    return progress, next_tier_data

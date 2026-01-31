from __future__ import annotations

from collections import Counter
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.anti_gaming import AntiGamingReport
from app.models.classification import Classification
from app.models.participation import Participation


def _latest_classification(session: Session, event_id: str) -> Classification | None:
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )


def evaluate_anti_gaming(session: Session, driver_id: str, discipline: str) -> AntiGamingReport:
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver_id, Participation.discipline == discipline)
        .order_by(Participation.created_at.desc())
        .limit(30)
        .all()
    )

    flags: List[str] = []
    details: Dict[str, object] = {}
    multiplier = 1.0

    if not participations:
        report = AntiGamingReport(
            driver_id=driver_id,
            discipline=discipline,
            flags=["no_participations"],
            multiplier=1.0,
            details={"reason": "no_participations"},
        )
        session.add(report)
        session.commit()
        session.refresh(report)
        return report

    event_ids = [p.event_id for p in participations]
    total = len(event_ids)
    unique_events = len(set(event_ids))
    diversity_ratio = unique_events / total if total else 0

    counts = Counter(event_ids)
    most_common = counts.most_common(1)[0][1] if counts else 0

    tiers = []
    for participation in participations:
        classification = _latest_classification(session, participation.event_id)
        tiers.append(classification.event_tier if classification else "E2")

    low_tier_count = sum(1 for tier in tiers if tier in {"E1", "E2"})
    low_tier_ratio = low_tier_count / total if total else 0

    if most_common >= 4:
        flags.append("repeat_event_farming")
        multiplier *= 0.85
        details["most_common_event_repeats"] = most_common

    if diversity_ratio < 0.5 and total >= 6:
        flags.append("low_event_diversity")
        multiplier *= 0.9
        details["diversity_ratio"] = round(diversity_ratio, 2)

    if low_tier_ratio > 0.6 and total >= 6:
        flags.append("low_tier_farming")
        multiplier *= 0.85
        details["low_tier_ratio"] = round(low_tier_ratio, 2)

    multiplier = max(0.5, round(multiplier, 2))

    report = AntiGamingReport(
        driver_id=driver_id,
        discipline=discipline,
        flags=flags,
        multiplier=multiplier,
        details=details,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report
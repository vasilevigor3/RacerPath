from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.anti_gaming import AntiGamingReport
from app.models.crs_history import CRSHistory
from app.models.participation import Participation
from app.core.settings import settings

TIER_WEIGHTS = {
    "E0": 0.6,
    "E1": 0.8,
    "E2": 1.0,
    "E3": 1.2,
    "E4": 1.4,
    "E5": 1.6,
}


@dataclass
class CRSResult:
    score: float
    inputs: dict


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _latest_classification(session: Session, event_id: str) -> Classification | None:
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )


def _participation_score(participation: Participation) -> float:
    score = 100.0
    score -= participation.incidents_count * 4.0
    score -= participation.penalties_count * 6.0

    if participation.status == "dnf":
        score -= 25.0
    if participation.status == "dsq":
        score -= 35.0
    if participation.status == "dns":
        score -= 40.0

    if participation.consistency_score is not None:
        score += (participation.consistency_score - 5.0) * 4.0

    if participation.pace_delta is not None and participation.pace_delta > 0:
        score -= min(10.0, participation.pace_delta * 2.0)

    return clamp_score(score)


def compute_crs(session: Session, driver_id: str, discipline: str) -> CRSResult:
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver_id, Participation.discipline == discipline)
        .order_by(Participation.created_at.desc())
        .limit(30)
        .all()
    )

    if not participations:
        return CRSResult(score=0.0, inputs={"reason": "no_participations"})

    weighted_scores = []
    weights = []

    for participation in participations:
        base_score = _participation_score(participation)
        classification = _latest_classification(session, participation.event_id)
        tier = classification.event_tier if classification else "E2"
        weight = TIER_WEIGHTS.get(tier, 1.0)
        weighted_scores.append(base_score * weight)
        weights.append(weight)

    total_weight = sum(weights) or 1.0
    score = sum(weighted_scores) / total_weight

    report = (
        session.query(AntiGamingReport)
        .filter(AntiGamingReport.driver_id == driver_id, AntiGamingReport.discipline == discipline)
        .order_by(AntiGamingReport.created_at.desc())
        .first()
    )
    multiplier = report.multiplier if report else 1.0
    multiplier = max(settings.anti_gaming_min_multiplier, min(settings.anti_gaming_max_multiplier, multiplier))
    score *= multiplier

    inputs = {
        "participations": len(participations),
        "avg_incidents": sum(p.incidents_count for p in participations) / len(participations),
        "avg_penalties": sum(p.penalties_count for p in participations) / len(participations),
        "dnf_rate": sum(1 for p in participations if p.status in {"dnf", "dsq"}) / len(participations),
        "weighted_tier_average": sum(weights) / len(weights),
        "anti_gaming_multiplier": multiplier,
    }

    return CRSResult(score=round(clamp_score(score), 2), inputs=inputs)


def record_crs(session: Session, driver_id: str, discipline: str) -> CRSHistory:
    result = compute_crs(session, driver_id, discipline)
    history = CRSHistory(driver_id=driver_id, discipline=discipline, score=result.score, inputs=result.inputs)
    session.add(history)
    session.commit()
    session.refresh(history)
    return history

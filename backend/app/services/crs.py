from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.anti_gaming import AntiGamingReport
from app.models.crs_history import CRSHistory
from app.models.participation import Participation
from app.models.task_completion import TaskCompletion
from app.core.settings import settings

CRS_ALGO_VERSION = "crs_v1"
PARTICIPATIONS_INPUT_LIMIT = 20

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


def _classification_for_participation(
    session: Session, participation: Participation
) -> Classification | None:
    """Classification for this participation: by classification_id if set, else by event_id."""
    if participation.classification_id:
        return (
            session.query(Classification)
            .filter(Classification.id == participation.classification_id)
            .first()
        )
    return _latest_classification(session, participation.event_id)


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
        classification = _classification_for_participation(session, participation)
        if not classification:
            raise ValueError(
                f"Event {participation.event_id} has no classification; "
                "CRS requires a classification for every participation."
            )
        tier = classification.event_tier
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


def compute_inputs(session: Session, driver_id: str, discipline: str) -> dict:
    """Minimal input snapshot for CRS: participation ids, counts, aggregates."""
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver_id, Participation.discipline == discipline)
        .order_by(Participation.created_at.desc())
        .limit(PARTICIPATIONS_INPUT_LIMIT)
        .all()
    )
    participation_ids = [p.id for p in participations]
    if not participations:
        return {
            "participation_ids": [],
            "reason": "no_participations",
            "participations_count": 0,
            "incidents_count": 0,
            "finished_count": 0,
            "task_completions_count": 0,
        }
    incidents_count = sum(p.incidents_count for p in participations)
    finished_count = sum(1 for p in participations if p.status == "finished")
    task_completions_count = (
        session.query(TaskCompletion)
        .filter(TaskCompletion.driver_id == driver_id, TaskCompletion.status == "completed")
        .count()
    )
    return {
        "participation_ids": participation_ids,
        "participations_count": len(participations),
        "incidents_count": incidents_count,
        "finished_count": finished_count,
        "task_completions_count": task_completions_count,
        "avg_incidents": incidents_count / len(participations),
    }


def compute_inputs_hash(inputs: dict) -> str:
    """SHA256 of canonical JSON (sorted keys) for inputs snapshot."""
    payload = json.dumps(inputs, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def record_crs(
    session: Session,
    driver_id: str,
    discipline: str,
    trigger_participation_id: str | None = None,
) -> CRSHistory:
    """Legacy entry point: same as recompute_crs (writes inputs_hash, algo_version)."""
    return recompute_crs(session, driver_id, discipline, trigger_participation_id)


def recompute_crs(
    session: Session,
    driver_id: str,
    discipline: str,
    trigger_participation_id: str | None = None,
) -> CRSHistory:
    """Compute CRS and save with inputs_hash, algo_version, computed_from_participation_id."""
    result = compute_crs(session, driver_id, discipline)
    inputs_snapshot = compute_inputs(session, driver_id, discipline)
    inputs_hash = compute_inputs_hash(inputs_snapshot)
    history = CRSHistory(
        driver_id=driver_id,
        discipline=discipline,
        score=result.score,
        inputs=result.inputs,
        computed_from_participation_id=trigger_participation_id,
        inputs_hash=inputs_hash,
        algo_version=CRS_ALGO_VERSION,
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    return history

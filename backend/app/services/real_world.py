from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.driver_license import DriverLicense
from app.models.participation import Participation
from app.models.real_world_format import RealWorldFormat
from app.models.real_world_readiness import RealWorldReadiness
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition

TIER_ORDER = ["E0", "E1", "E2", "E3", "E4", "E5"]


def _latest_crs(session: Session, driver_id: str, discipline: str) -> CRSHistory | None:
    return (
        session.query(CRSHistory)
        .filter(CRSHistory.driver_id == driver_id, CRSHistory.discipline == discipline)
        .order_by(CRSHistory.computed_at.desc())
        .first()
    )


def _latest_classification(session: Session, event_id: str) -> Classification | None:
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )


def _completed_task_codes(session: Session, driver_id: str) -> set[str]:
    task_ids = {
        completion.task_id
        for completion in session.query(TaskCompletion)
        .filter(TaskCompletion.driver_id == driver_id, TaskCompletion.status == "completed")
        .all()
    }
    if not task_ids:
        return set()
    tasks = session.query(TaskDefinition).filter(TaskDefinition.id.in_(task_ids)).all()
    return {task.code for task in tasks}


def _earned_licenses(session: Session, driver_id: str, discipline: str) -> set[str]:
    return {
        license.level_code
        for license in session.query(DriverLicense)
        .filter(DriverLicense.driver_id == driver_id, DriverLicense.discipline == discipline)
        .all()
    }


def _tiers_completed(session: Session, driver_id: str, discipline: str) -> set[str]:
    tiers = set()
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver_id, Participation.discipline == discipline)
        .all()
    )
    for participation in participations:
        classification = _latest_classification(session, participation.event_id)
        if classification:
            tiers.add(classification.event_tier)
    return tiers


def _tier_index(tier: str) -> int:
    try:
        return TIER_ORDER.index(tier)
    except ValueError:
        return 0


def compute_real_world_readiness(session: Session, driver_id: str, discipline: str) -> RealWorldReadiness:
    formats = (
        session.query(RealWorldFormat)
        .filter(RealWorldFormat.discipline == discipline, RealWorldFormat.active.is_(True))
        .order_by(RealWorldFormat.min_crs.asc())
        .all()
    )

    crs = _latest_crs(session, driver_id, discipline)
    crs_score = crs.score if crs else 0.0
    completed_tasks = _completed_task_codes(session, driver_id)
    earned_licenses = _earned_licenses(session, driver_id, discipline)
    tiers_completed = _tiers_completed(session, driver_id, discipline)

    format_outputs: List[Dict] = []
    best_status_rank = 2
    status_rank = {"ready": 0, "almost_ready": 1, "not_ready": 2}

    for fmt in formats:
        missing: List[str] = []

        if crs_score < fmt.min_crs:
            missing.append(f"CRS >= {fmt.min_crs}")

        if fmt.required_license_code and fmt.required_license_code not in earned_licenses:
            missing.append(f"License {fmt.required_license_code}")

        missing_tasks = [code for code in fmt.required_task_codes if code not in completed_tasks]
        for code in missing_tasks:
            missing.append(f"Task {code}")

        for tier in fmt.required_event_tiers:
            if tier not in tiers_completed:
                missing.append(f"Event tier {tier}")

        if not missing:
            status = "ready"
        else:
            near_crs = crs_score >= max(0, fmt.min_crs - 10)
            status = "almost_ready" if near_crs and len(missing) <= 2 else "not_ready"

        best_status_rank = min(best_status_rank, status_rank[status])
        format_outputs.append(
            {
                "code": fmt.code,
                "name": fmt.name,
                "status": status,
                "missing": missing,
            }
        )

    overall = "not_ready"
    for key, rank in status_rank.items():
        if rank == best_status_rank:
            overall = key
            break

    summary = f"CRS {crs_score:.1f}. Real-world readiness: {overall.replace('_', ' ')}."

    readiness = RealWorldReadiness(
        driver_id=driver_id,
        discipline=discipline,
        status=overall,
        summary=summary,
        formats=format_outputs,
    )
    session.add(readiness)
    session.commit()
    session.refresh(readiness)
    return readiness
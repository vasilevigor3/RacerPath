from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlalchemy.orm import Session

from app.models.crs_history import CRSHistory
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition


@dataclass
class EligibilityResult:
    eligible: bool
    next_level_code: str | None
    reasons: List[str]
    current_crs: float | None
    completed_task_codes: List[str]
    required_task_codes: List[str]


def _latest_crs(session: Session, driver_id: str, discipline: str) -> CRSHistory | None:
    return (
        session.query(CRSHistory)
        .filter(CRSHistory.driver_id == driver_id, CRSHistory.discipline == discipline)
        .order_by(CRSHistory.computed_at.desc())
        .first()
    )


def _completed_task_codes(session: Session, driver_id: str) -> set[str]:
    """Only completions tied to an event participation count toward license award."""
    task_ids = {
        completion.task_id
        for completion in session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.status == "completed",
            TaskCompletion.participation_id.isnot(None),
        )
        .all()
    }
    if not task_ids:
        return set()
    tasks = session.query(TaskDefinition).filter(TaskDefinition.id.in_(task_ids)).all()
    return {task.code for task in tasks}


def check_eligibility(session: Session, driver_id: str, discipline: str) -> EligibilityResult:
    """Return eligibility for next license: eligible, next_level_code, reasons, crs, task codes."""
    crs = _latest_crs(session, driver_id, discipline)
    completed_codes = _completed_task_codes(session, driver_id)

    levels = (
        session.query(LicenseLevel)
        .filter(LicenseLevel.discipline == discipline, LicenseLevel.active.is_(True))
        .order_by(LicenseLevel.min_crs.asc())
        .all()
    )

    earned = {
        lic.level_code
        for lic in session.query(DriverLicense)
        .filter(DriverLicense.driver_id == driver_id, DriverLicense.discipline == discipline)
        .all()
    }

    if not levels:
        return EligibilityResult(
            eligible=False,
            next_level_code=None,
            reasons=["No license levels defined for this discipline"],
            current_crs=crs.score if crs else None,
            completed_task_codes=sorted(completed_codes),
            required_task_codes=[],
        )

    if not crs:
        next_code = next((lev.code for lev in levels if lev.code not in earned), None)
        req = next((lev.required_task_codes for lev in levels if lev.code == next_code), []) if next_code else []
        return EligibilityResult(
            eligible=False,
            next_level_code=next_code,
            reasons=["No CRS score for this driver/discipline yet (need classified events)"],
            current_crs=None,
            completed_task_codes=sorted(completed_codes),
            required_task_codes=req or [],
        )

    eligible_level = None
    reasons: List[str] = []
    for level in levels:
        if level.code in earned:
            continue
        req_codes = level.required_task_codes if isinstance(level.required_task_codes, list) else []
        missing_tasks = set(req_codes) - completed_codes
        if crs.score < level.min_crs:
            reasons.append(f"CRS {crs.score} < min_crs {level.min_crs} for {level.code}")
            continue
        if missing_tasks:
            reasons.append(f"Missing tasks for {level.code}: {', '.join(sorted(missing_tasks))}")
            continue
        eligible_level = level
        break

    if eligible_level:
        return EligibilityResult(
            eligible=True,
            next_level_code=eligible_level.code,
            reasons=[],
            current_crs=crs.score,
            completed_task_codes=sorted(completed_codes),
            required_task_codes=eligible_level.required_task_codes or [],
        )

    next_code = next((lev.code for lev in levels if lev.code not in earned), None)
    req = next((lev.required_task_codes for lev in levels if lev.code == next_code), []) if next_code else []
    return EligibilityResult(
        eligible=False,
        next_level_code=next_code,
        reasons=reasons if reasons else ["No next level or requirements not met"],
        current_crs=crs.score,
        completed_task_codes=sorted(completed_codes),
        required_task_codes=req or [],
    )


def award_license(session: Session, driver_id: str, discipline: str) -> DriverLicense | None:
    crs = _latest_crs(session, driver_id, discipline)
    if not crs:
        return None

    completed_codes = _completed_task_codes(session, driver_id)

    levels = (
        session.query(LicenseLevel)
        .filter(LicenseLevel.discipline == discipline, LicenseLevel.active.is_(True))
        .order_by(LicenseLevel.min_crs.asc())
        .all()
    )

    if not levels:
        return None

    earned = {
        license.level_code
        for license in session.query(DriverLicense)
        .filter(DriverLicense.driver_id == driver_id, DriverLicense.discipline == discipline)
        .all()
    }

    eligible = None
    for level in levels:
        if level.code in earned:
            continue
        if crs.score < level.min_crs:
            continue
        # Require ALL required_task_codes to be in completed_codes (no partial pass)
        req_codes = level.required_task_codes if isinstance(level.required_task_codes, list) else []
        if req_codes and not all(rc in completed_codes for rc in req_codes):
            continue
        eligible = level

    if not eligible:
        return None

    driver_license = DriverLicense(
        driver_id=driver_id,
        discipline=discipline,
        level_code=eligible.code,
        status="earned",
    )
    session.add(driver_license)
    session.commit()
    session.refresh(driver_license)
    return driver_license
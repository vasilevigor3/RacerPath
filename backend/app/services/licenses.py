from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.crs_history import CRSHistory
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition


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
        if not set(level.required_task_codes).issubset(completed_codes):
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
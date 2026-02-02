"""Run task evaluation, license award, and tier recalc when a participation becomes completed."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.participation import Participation
from app.services.licenses import award_license, check_eligibility
from app.services.next_tier import compute_next_tier_progress
from app.services.tasks import assign_participation_id_for_completed_participation, evaluate_tasks


@dataclass
class ParticipationCompletedResult:
    task_completions_count: int
    license_awarded: bool
    license_level_code: str | None


def on_participation_completed(
    session: Session, driver_id: str, participation_id: str
) -> ParticipationCompletedResult:
    """Evaluate tasks, backfill participation_id, check eligibility, award license if eligible, recalc tier."""
    completions = evaluate_tasks(session, driver_id, participation_id)
    assign_participation_id_for_completed_participation(session, driver_id, participation_id)

    part = session.query(Participation).filter(Participation.id == participation_id).first()
    discipline = (
        part.discipline.value if hasattr(part.discipline, "value") else str(part.discipline or "gt")
    )

    result = check_eligibility(session, driver_id, discipline)
    license_awarded = False
    license_level_code = None
    if result.eligible and result.next_level_code:
        awarded = award_license(session, driver_id, discipline)
        if awarded:
            license_awarded = True
            license_level_code = awarded.level_code

    # Recalc tier (and auto-promote if progress 100% and required licenses earned)
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if driver and driver.user_id:
        compute_next_tier_progress(session, driver.user_id)

    return ParticipationCompletedResult(
        task_completions_count=len(completions),
        license_awarded=license_awarded,
        license_level_code=license_level_code,
    )

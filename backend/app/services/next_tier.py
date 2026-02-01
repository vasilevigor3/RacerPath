"""Progress toward next tier: computed from finished races, completed tasks, earned licenses."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.participation import Participation, ParticipationStatus
from app.models.task_completion import TaskCompletion

# Weights for next_tier_progress_percent (0–100). Tune as product rules evolve.
WEIGHT_RACES = 4
WEIGHT_TASKS = 6
WEIGHT_LICENSES = 25
MAX_POINTS = 100  # cap progress at 100%


def compute_next_tier_progress(session: Session, user_id: str) -> int:
    """
    Compute progress (0–100) toward next tier from:
    - finished races (Participation.status == finished),
    - completed tasks (TaskCompletion.status == completed),
    - earned licenses (DriverLicense.status == earned).
    """
    driver = session.query(Driver).filter(Driver.user_id == user_id).first()
    if not driver:
        return 0

    races_count = (
        session.query(Participation.id)
        .filter(
            Participation.driver_id == driver.id,
            Participation.status == ParticipationStatus.finished,
        )
        .count()
    )
    tasks_count = (
        session.query(TaskCompletion.id)
        .filter(
            TaskCompletion.driver_id == driver.id,
            TaskCompletion.status == "completed",
        )
        .count()
    )
    licenses_count = (
        session.query(DriverLicense.id)
        .filter(
            DriverLicense.driver_id == driver.id,
            DriverLicense.status == "earned",
        )
        .count()
    )

    points = races_count * WEIGHT_RACES + tasks_count * WEIGHT_TASKS + licenses_count * WEIGHT_LICENSES
    return min(MAX_POINTS, points)

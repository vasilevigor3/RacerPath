"""Clear all user data: licenses, task completions, participations, incidents. Used by admin API and scripts."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.user import User


def clear_user_data(session: Session, email: str) -> dict:
    """Delete all licenses, task completions, participations (and incidents) for user by email. Returns counts."""
    user = session.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError(f"User not found: {email}")

    drivers = session.query(Driver).filter(Driver.user_id == user.id).all()
    if not drivers:
        return {"licenses": 0, "task_completions": 0, "participations": 0}

    driver_ids = [d.id for d in drivers]

    licenses_deleted = session.query(DriverLicense).filter(
        DriverLicense.driver_id.in_(driver_ids)
    ).delete(synchronize_session=False)

    task_completions_deleted = session.query(TaskCompletion).filter(
        TaskCompletion.driver_id.in_(driver_ids)
    ).delete(synchronize_session=False)

    participation_ids = [
        row[0]
        for row in session.query(Participation.id).filter(
            Participation.driver_id.in_(driver_ids)
        ).all()
    ]
    participations_deleted = 0
    if participation_ids:
        session.query(CRSHistory).filter(
            CRSHistory.computed_from_participation_id.in_(participation_ids)
        ).update(
            {CRSHistory.computed_from_participation_id: None},
            synchronize_session=False,
        )
        session.query(Recommendation).filter(
            Recommendation.computed_from_participation_id.in_(participation_ids)
        ).update(
            {Recommendation.computed_from_participation_id: None},
            synchronize_session=False,
        )
        session.query(Incident).filter(
            Incident.participation_id.in_(participation_ids)
        ).delete(synchronize_session=False)
        participations_deleted = session.query(Participation).filter(
            Participation.id.in_(participation_ids)
        ).delete(synchronize_session=False)

    return {
        "licenses": licenses_deleted,
        "task_completions": task_completions_deleted,
        "participations": participations_deleted,
    }

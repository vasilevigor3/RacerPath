"""Delete ALL task definitions, license levels, driver licenses, events, participations,
task completions, and related records. Use before creating a fresh test set.

Run from repo root:
  docker compose exec app python backend/scripts/reset_all_tasks_licenses_events.py

Then create test set:
  docker compose exec app python backend/scripts/create_test_task_and_event.py
"""
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.driver_license import DriverLicense
from app.models.event import Event
from app.models.incident import Incident
from app.models.license_level import LicenseLevel
from app.models.participation import Participation
from app.models.penalty import Penalty
from app.models.raw_event import RawEvent
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition


def reset_all(session: Session) -> dict:
    """Delete all tasks, licenses, events and related. Returns counts."""
    # 1. Participations-related: nullify refs, delete dependents
    participation_ids = [row[0] for row in session.query(Participation.id).all()]
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
        incident_ids = [r[0] for r in session.query(Incident.id).filter(
            Incident.participation_id.in_(participation_ids)
        ).all()]
        if incident_ids:
            session.query(Penalty).filter(
                Penalty.incident_id.in_(incident_ids)
            ).delete(synchronize_session=False)
        session.query(Incident).filter(
            Incident.participation_id.in_(participation_ids)
        ).delete(synchronize_session=False)

    # 2. Task completions (all)
    task_completions_deleted = session.query(TaskCompletion).delete(
        synchronize_session=False
    )

    # 3. Participations
    participations_deleted = session.query(Participation).delete(
        synchronize_session=False
    )

    # 4. Event-related
    session.query(RawEvent).delete(synchronize_session=False)
    session.query(Classification).delete(synchronize_session=False)
    events_deleted = session.query(Event).delete(synchronize_session=False)

    # 5. Driver licenses (all users)
    licenses_deleted = session.query(DriverLicense).delete(
        synchronize_session=False
    )

    # 6. Task definitions
    task_definitions_deleted = session.query(TaskDefinition).delete(
        synchronize_session=False
    )

    # 7. License levels (definitions)
    license_levels_deleted = session.query(LicenseLevel).delete(
        synchronize_session=False
    )

    return {
        "task_completions": task_completions_deleted,
        "participations": participations_deleted,
        "events": events_deleted,
        "driver_licenses": licenses_deleted,
        "task_definitions": task_definitions_deleted,
        "license_levels": license_levels_deleted,
    }


def main() -> None:
    session = SessionLocal()
    try:
        counts = reset_all(session)
        session.commit()
        print("Reset complete. Deleted:")
        for key, value in counts.items():
            print(f"  {key}: {value}")
        print("\nRun: docker compose exec app python backend/scripts/create_test_task_and_event.py")
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Delete all script-created events (source='script') and related records.

Run from repo root:
  docker compose exec app python backend/scripts/clear_script_events.py
"""
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.raw_event import RawEvent
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion


def clear_script_events(session: Session) -> int:
    """Delete all events where source='script'. Returns count."""
    events = session.query(Event).filter(Event.source == "script").all()
    event_ids = [e.id for e in events]
    if not event_ids:
        return 0

    participation_ids = [
        row[0]
        for row in session.query(Participation.id).filter(
            Participation.event_id.in_(event_ids)
        ).all()
    ]
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
        session.query(TaskCompletion).filter(
            TaskCompletion.participation_id.in_(participation_ids)
        ).delete(synchronize_session=False)
        session.query(Participation).filter(
            Participation.event_id.in_(event_ids)
        ).delete(synchronize_session=False)
    session.query(RawEvent).filter(RawEvent.event_id.in_(event_ids)).delete(
        synchronize_session=False
    )
    session.query(Classification).filter(
        Classification.event_id.in_(event_ids)
    ).delete(synchronize_session=False)
    count = session.query(Event).filter(Event.id.in_(event_ids)).delete(
        synchronize_session=False
    )
    return count


def main() -> None:
    session = SessionLocal()
    try:
        count = clear_script_events(session)
        session.commit()
        print(f"Deleted {count} script event(s).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

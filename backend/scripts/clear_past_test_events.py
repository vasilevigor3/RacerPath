"""Delete all past test events (source=script or title like 'Test Flow%') and related records.

Run from repo root:
  docker compose exec app python backend/scripts/clear_past_test_events.py
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.penalty import Penalty
from app.models.raw_event import RawEvent
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion


def clear_past_test_events(session: Session) -> int:
    """Delete events where start_time_utc < now and (source='script' or title like 'Test Flow%'). Returns count."""
    now = datetime.now(timezone.utc)
    query = session.query(Event).filter(Event.start_time_utc.isnot(None))
    query = query.filter(Event.start_time_utc < now)
    query = query.filter(
        (Event.source == "script") | (Event.title.like("Test Flow%"))
    )
    events = query.all()
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
        count = clear_past_test_events(session)
        session.commit()
        print(f"Deleted {count} past test event(s).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

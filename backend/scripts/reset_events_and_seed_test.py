"""Delete all events and related records, then create 3 test events: 2 with tier E0, 1 with tier E1.
Run from repo root:
  docker compose exec app python backend/scripts/reset_events_and_seed_test.py
"""
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.raw_event import RawEvent
from app.models.task_completion import TaskCompletion
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event


def main() -> None:
    session = SessionLocal()
    try:
        event_ids = [row[0] for row in session.query(Event.id).all()]
        if not event_ids:
            print("No events to delete.")
        else:
            participation_ids = [
                row[0]
                for row in session.query(Participation.id).filter(Participation.event_id.in_(event_ids)).all()
            ]
            session.query(Incident).filter(Incident.participation_id.in_(participation_ids)).delete(
                synchronize_session=False
            )
            session.query(TaskCompletion).filter(TaskCompletion.participation_id.in_(participation_ids)).delete(
                synchronize_session=False
            )
            session.query(Participation).filter(Participation.event_id.in_(event_ids)).delete(
                synchronize_session=False
            )
            session.query(RawEvent).filter(RawEvent.event_id.in_(event_ids)).delete(synchronize_session=False)
            session.query(Classification).filter(Classification.event_id.in_(event_ids)).delete(
                synchronize_session=False
            )
            session.query(Event).filter(Event.id.in_(event_ids)).delete(synchronize_session=False)
            session.commit()
            print(f"Deleted {len(event_ids)} events and related records.")

        now = datetime.now(timezone.utc)
        test_events = [
            ("Test Event E0 #1", "E0"),
            ("Test Event E0 #2", "E0"),
            ("Test Event E1", "E1"),
        ]
        for title, tier in test_events:
            event = Event(
                title=title,
                source="seed",
                game="ACC",  # so drivers with ACC/Assetto Corsa Competizione in sim_games see these events
                start_time_utc=now,
                session_type="race",
                schedule_type="weekly",
                event_type="circuit",
                format_type="sprint",
                duration_minutes=30,
                grid_size_expected=20,
            )
            session.add(event)
            session.flush()
            payload = build_event_payload(event, "gt")
            classification_data = classify_event(payload)
            classification_data["event_tier"] = tier
            classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
            classification = Classification(event_id=event.id, **classification_data)
            session.add(classification)
        session.commit()
        print("Created 3 test events: 2 x E0, 1 x E1.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

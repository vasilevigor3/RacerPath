"""Create one "Race of the day" event for tier E0 (suitable for Next actions for E0 drivers).
Run from repo root:
  docker compose exec app python backend/scripts/create_race_of_day_e0.py
"""
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event


def main() -> None:
    # Start in ~2 hours from now so it's "upcoming" and appears in Race of the day
    start_utc = datetime.now(timezone.utc) + timedelta(hours=2)
    start_utc = start_utc.replace(minute=0, second=0, microsecond=0)

    session = SessionLocal()
    try:
        event = Event(
            title="Race of the day (E0)",
            source="script",
            game="ACC",
            start_time_utc=start_utc,
            special_event="race_of_day",
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="sprint",
            duration_minutes=30,
            grid_size_expected=20,
        )
        session.add(event)
        session.flush()

        tier = "E0"
        payload = build_event_payload(event, "gt")
        classification_data = classify_event(payload)
        classification_data["event_tier"] = tier
        classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)

        session.commit()
        print(
            f"Created event: {event.title} (id={event.id}, tier={tier}, special_event=race_of_day, start={start_utc.isoformat()})"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()

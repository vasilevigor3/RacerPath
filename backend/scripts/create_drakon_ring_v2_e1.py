"""Create event Drakon Ring v2 (tier E1), same as Drakon Ring v1 but tier E1.
Race · sprint / ACC · 2/2/2026, 8:47:00 PM · Waiting to start
Run from repo root:
  docker compose exec app python backend/scripts/create_drakon_ring_v2_e1.py
"""
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event


def main() -> None:
    # 2/2/2026, 8:47:00 PM UTC
    start_utc = datetime(2026, 2, 2, 19, 47, 0, tzinfo=timezone.utc)

    session = SessionLocal()
    try:
        event = Event(
            title="Drakon Ring v2",
            source="script",
            game="ACC",
            start_time_utc=start_utc,
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="sprint",
            duration_minutes=30,
            grid_size_expected=20,
        )
        session.add(event)
        session.flush()

        tier = "E1"
        payload = build_event_payload(event, "gt")
        classification_data = classify_event(payload)
        classification_data["event_tier"] = tier
        classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)

        session.commit()
        print(f"Created event: {event.title} (id={event.id}, tier={tier}, start={start_utc.isoformat()})")
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Create one event tier E0 with rig: pedals premium, wheel force feedback.
Run from repo root:
  docker compose exec app python backend/scripts/create_event_e0_premium_ffb.py
"""
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event

RIG_OPTIONS = {
    "wheel_type": "force_feedback_nm",
    "pedals_class": "premium",
    "manual_with_clutch": False,
}


def main() -> None:
    start_utc = datetime(2026, 2, 10, 20, 0, 0, tzinfo=timezone.utc)
    session = SessionLocal()
    try:
        event = Event(
            title="E0 Premium Rig · ACC Sprint",
            source="script",
            game="ACC",
            start_time_utc=start_utc,
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="sprint",
            duration_minutes=30,
            grid_size_expected=20,
            rig_options=RIG_OPTIONS,
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
            f"Created: {event.title} (id={event.id}, tier={tier}, "
            f"rig: wheel={RIG_OPTIONS['wheel_type']}, pedals={RIG_OPTIONS['pedals_class']})"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Set start_time_utc of test events (Drakon Ring, E0 Premium Rig, Test Old/Super) to future dates.
Run from repo root:
  docker compose exec app python backend/scripts/set_test_events_future_dates.py
"""
from datetime import datetime, timezone, timedelta

from app.db.session import SessionLocal
from app.models.event import Event


def main() -> None:
    session = SessionLocal()
    try:
        # Test events: Drakon Ring v1/v2, E0 Premium Rig, Test · Old wheel / Super pedals
        events = (
            session.query(Event)
            .filter(
                Event.game == "ACC",
                (
                    (Event.source == "script")
                    | (Event.title.like("%Drakon Ring%"))
                    | (Event.title.like("%E0 Premium Rig%"))
                    | (Event.title.like("%Test · Old%"))
                ),
            )
            .all()
        )
        now = datetime.now(timezone.utc)
        # Spread starts: 7, 14, 21, 28 days from now
        for i, event in enumerate(events):
            days_ahead = 7 + (i % 4) * 7
            new_start = now + timedelta(days=days_ahead)
            new_start = new_start.replace(hour=19, minute=0, second=0, microsecond=0)
            event.start_time_utc = new_start
            print(f"Updated: {event.title} (id={event.id}) -> start={new_start.isoformat()}")
        session.commit()
        print(f"Done: {len(events)} event(s) updated.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

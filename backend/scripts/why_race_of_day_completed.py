"""Show why "Race of the day: completed" for a user (by email). Run from repo root:
  docker compose exec app python backend/scripts/why_race_of_day_completed.py YOUR_EMAIL
"""
import sys
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.event import Event
from app.models.participation import Participation
from app.models.user import User
from app.utils.special_events import get_period_bounds


def main() -> None:
    email = (sys.argv[1] or "").strip()
    if not email:
        print("Usage: python backend/scripts/why_race_of_day_completed.py YOUR_EMAIL")
        sys.exit(1)

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)
        driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            print(f"User {email} has no driver.")
            sys.exit(1)

        now_utc = datetime.now(timezone.utc)
        period_start, period_end = get_period_bounds("race_of_day", now_utc)

        participations = (
            session.query(Participation, Event)
            .join(Event, Participation.event_id == Event.id)
            .filter(
                Participation.driver_id == driver.id,
                Event.special_event == "race_of_day",
                Event.start_time_utc.isnot(None),
                Event.start_time_utc >= period_start,
                Event.start_time_utc <= period_end,
            )
            .all()
        )

        print(f"User: {user.email}  Driver: {driver.name} (id={driver.id})")
        print(f"Period (race_of_day): {period_start.isoformat()} .. {period_end.isoformat()}")
        print(f"Participations in this period: {len(participations)}")
        for p, e in participations:
            print(f"  participation_id={p.id}  event={e.title}  participation_state={p.participation_state}  event_start={e.start_time_utc}")
        if not participations:
            print("  (none — 'Race of the day: completed' should not show; check period or other slot)")
    finally:
        session.close()


if __name__ == "__main__":
    main()

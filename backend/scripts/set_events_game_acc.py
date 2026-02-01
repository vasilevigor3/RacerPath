"""Set game='ACC' for events that have game='Test Game'. Optional: --all to set ACC for every event.
Run from repo root:
  docker compose exec app python backend/scripts/set_events_game_acc.py
  docker compose exec app python backend/scripts/set_events_game_acc.py --all
"""
import sys

from app.db.session import SessionLocal
from app.models.event import Event


def main() -> None:
    update_all = "--all" in sys.argv
    session = SessionLocal()
    try:
        if update_all:
            updated = session.query(Event).update({"game": "ACC"}, synchronize_session=False)
        else:
            updated = (
                session.query(Event)
                .filter(Event.game == "Test Game")
                .update({"game": "ACC"}, synchronize_session=False)
            )
        session.commit()
        print(f"OK: set game='ACC' for {updated} event(s).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

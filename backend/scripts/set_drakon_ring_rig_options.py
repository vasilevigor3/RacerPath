"""Set rig_options on Drakon Ring v1 and v2 events (ACC).
Run from repo root:
  docker compose exec app python backend/scripts/set_drakon_ring_rig_options.py
"""
from app.db.session import SessionLocal
from app.models.event import Event


# Default rig: legacy wheel, spring pedals, no clutch required (typical ACC sprint)
RIG_OPTIONS = {
    "wheel_type": "legacy",
    "pedals_class": "spring",
    "manual_with_clutch": False,
}


def main() -> None:
    session = SessionLocal()
    try:
        events = (
            session.query(Event)
            .filter(
                Event.game == "ACC",
                Event.title.like("%Drakon Ring v%"),
            )
            .all()
        )
        for event in events:
            event.rig_options = RIG_OPTIONS
            print(f"Updated rig_options: {event.title} (id={event.id})")
        session.commit()
        print(f"Done: {len(events)} event(s) updated.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

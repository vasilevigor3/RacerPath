"""Make E0 Premium Rig and Test · Old wheel visible to driver with tier E1 and rig legacy+spring.
- E0 Premium Rig: set tier to E1, rig to legacy+spring.
- Test · Old wheel: set rig to legacy+spring (pedals_class=spring).
Run from repo root:
  docker compose exec app python backend/scripts/fix_test_events_visible.py
"""
from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import TIER_LABELS

RIG_LEGACY_SPRING = {
    "wheel_type": "legacy",
    "pedals_class": "spring",
    "manual_with_clutch": False,
}


def main() -> None:
    session = SessionLocal()
    try:
        # E0 Premium Rig -> tier E1, rig legacy+spring
        e0 = (
            session.query(Event)
            .filter(Event.game == "ACC", Event.title == "E0 Premium Rig · ACC Sprint")
            .first()
        )
        if e0:
            e0.rig_options = RIG_LEGACY_SPRING
            cls = (
                session.query(Classification)
                .filter(Classification.event_id == e0.id)
                .order_by(Classification.created_at.desc())
                .first()
            )
            if cls:
                cls.event_tier = "E1"
                cls.tier_label = TIER_LABELS.get("E1", "E1")
            print(f"Updated: {e0.title} -> tier E1, rig legacy+spring")
        else:
            print("E0 Premium Rig · ACC Sprint not found")

        # Test · Old wheel -> rig legacy+spring
        test_ev = (
            session.query(Event)
            .filter(Event.game == "ACC", Event.title.like("%Test · Old%"))
            .first()
        )
        if test_ev:
            test_ev.rig_options = RIG_LEGACY_SPRING
            print(f"Updated: {test_ev.title} -> rig legacy+spring")
        else:
            print("Test · Old wheel event not found")

        session.commit()
        print("Done.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Revert E0 Premium Rig and Test · Old wheel to original tier/rig.
- E0 Premium Rig: tier E0, rig force_feedback_nm + premium.
- Test · Old wheel: rig legacy + premium.
Run from repo root:
  docker compose exec app python backend/scripts/revert_test_events_visible.py
"""
from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import TIER_LABELS

RIG_E0_PREMIUM_FFB = {
    "wheel_type": "force_feedback_nm",
    "pedals_class": "premium",
    "manual_with_clutch": False,
}
RIG_LEGACY_PREMIUM = {
    "wheel_type": "legacy",
    "pedals_class": "premium",
    "manual_with_clutch": False,
}


def main() -> None:
    session = SessionLocal()
    try:
        e0 = (
            session.query(Event)
            .filter(Event.game == "ACC", Event.title == "E0 Premium Rig · ACC Sprint")
            .first()
        )
        if e0:
            e0.rig_options = RIG_E0_PREMIUM_FFB
            cls = (
                session.query(Classification)
                .filter(Classification.event_id == e0.id)
                .order_by(Classification.created_at.desc())
                .first()
            )
            if cls:
                cls.event_tier = "E0"
                cls.tier_label = TIER_LABELS.get("E0", "E0")
            print(f"Reverted: {e0.title} -> tier E0, rig force_feedback_nm+premium")
        else:
            print("E0 Premium Rig · ACC Sprint not found")

        test_ev = (
            session.query(Event)
            .filter(Event.game == "ACC", Event.title.like("%Test · Old%"))
            .first()
        )
        if test_ev:
            test_ev.rig_options = RIG_LEGACY_PREMIUM
            print(f"Reverted: {test_ev.title} -> rig legacy+premium")
        else:
            print("Test · Old wheel event not found")

        session.commit()
        print("Done.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

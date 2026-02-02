"""Run events diagnostic for a driver_id (why GET /api/events?driver_id=... returns []).
Usage: docker compose exec app python backend/scripts/events_diagnostic.py <driver_id>
"""
import json
import sys

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.utils.game_aliases import expand_driver_games_for_event_match

TIER_ORDER = ["E0", "E1", "E2", "E3", "E4", "E5"]


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/events_diagnostic.py <driver_id>", file=sys.stderr)
        sys.exit(1)
    driver_id = sys.argv[1].strip()
    session = SessionLocal()
    try:
        driver = session.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            out = {"reason": "driver_not_found", "driver_found": False}
            print(json.dumps(out, indent=2))
            return
        total_in_db = session.query(Event).count()
        driver_games = list(expand_driver_games_for_event_match(driver.sim_games or []))
        query = session.query(Event)
        if driver.sim_games:
            query = query.filter(Event.game.in_(driver_games))
        after_game = query.count()
        driver_tier = getattr(driver, "tier", "E0") or "E0"
        event_ids_after_game = [r[0] for r in query.with_entities(Event.id).all()]
        tier_by_event = {}
        if event_ids_after_game:
            classifications = (
                session.query(Classification)
                .filter(Classification.event_id.in_(event_ids_after_game))
                .order_by(Classification.created_at.desc())
                .all()
            )
            for c in classifications:
                if c.event_id not in tier_by_event:
                    tier_by_event[c.event_id] = c.event_tier or "E2"
        driver_idx = TIER_ORDER.index(driver_tier) if driver_tier in TIER_ORDER else 0
        after_tier = sum(
            1
            for eid in event_ids_after_game
            if TIER_ORDER.index(tier_by_event.get(eid, "E2")) >= driver_idx
        )
        if total_in_db == 0:
            reason = "no_events_in_db"
        elif after_game == 0 and driver.sim_games:
            reason = "no_events_match_sim_games"
        elif after_tier == 0:
            reason = "no_events_match_tier"
        else:
            reason = "ok"
        hint = None
        if reason == "no_events_match_sim_games":
            hint = "Add ACC or Assetto Corsa Competizione to Profile → Sim games to see test events."
        elif reason == "no_events_in_db":
            hint = "Run create_test_task_and_event.py to create test events."
        elif reason == "no_events_match_tier":
            hint = "Events have lower tier than driver. Uncheck 'Show only my lvl events' or create events with tier >= driver tier."
        out = {
            "reason": reason,
            "driver_found": True,
            "driver_sim_games": driver.sim_games,
            "driver_tier": driver_tier,
            "events_total_in_db": total_in_db,
            "events_after_game_filter": after_game,
            "events_after_tier_filter": after_tier,
            "hint": hint,
        }
        print(json.dumps(out, indent=2))
    finally:
        session.close()


if __name__ == "__main__":
    main()

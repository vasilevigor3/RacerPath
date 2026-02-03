"""Diagnose why past events don't show for a user.
Checks: past events in DB (last 30 days), tier match, sim_games match, rig filter.
Usage:
  python backend/scripts/past_events_diagnostic.py <email|user_id|driver_id>
  docker compose exec app python backend/scripts/past_events_diagnostic.py user@example.com
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.event import Event
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.user import UserRepository
from app.utils.game_aliases import expand_driver_games_for_event_match
from app.utils.rig_compat import driver_rig_satisfies_event


RECENT_DAYS = 30


def resolve_driver(session, arg: str) -> Driver | None:
    """Resolve email / user_id / driver_id to Driver."""
    arg = arg.strip()
    user_repo = UserRepository(session)
    driver_repo = DriverRepository(session)

    if "@" in arg:
        user = user_repo.get_by_email(arg)
        if not user:
            return None
        return driver_repo.get_by_user_id(user.id)

    # Try as user_id
    user = user_repo.get_by_id(arg)
    if user:
        return driver_repo.get_by_user_id(user.id)

    # Try as driver_id
    return driver_repo.get_by_id(arg)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: past_events_diagnostic.py <email|user_id|driver_id>", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    try:
        driver = resolve_driver(session, sys.argv[1])
        if not driver:
            print("User/Driver not found.")
            sys.exit(1)

        now = datetime.now(timezone.utc)
        since = now - timedelta(days=RECENT_DAYS)
        driver_tier = getattr(driver, "tier", "E0") or "E0"
        driver_games = list(expand_driver_games_for_event_match(driver.sim_games or []))

        # 1) All events in DB with start in [since, now) (past window)
        past_in_window = (
            session.query(Event)
            .filter(
                Event.start_time_utc.isnot(None),
                Event.start_time_utc < now,
                Event.start_time_utc >= since,
            )
            .order_by(Event.start_time_utc.desc())
            .all()
        )

        # 2) For each past event: tier from classification
        event_repo = EventRepository(session)
        from app.repositories.classification import ClassificationRepository
        class_repo = ClassificationRepository(session)
        tier_by_event = {}
        if past_in_window:
            for e in past_in_window:
                c = class_repo.get_latest_for_event(e.id)
                tier_by_event[e.id] = (c.event_tier or "E2") if c else "E2"

        # 3) Count by tier match (exact: event_tier == driver_tier)
        with_tier = [e for e in past_in_window if tier_by_event.get(e.id) == driver_tier]

        # 4) Count by game match (event.game in driver_games; if driver_games empty, no filter in repo)
        if driver_games:
            with_game = [e for e in with_tier if e.game in driver_games]
        else:
            with_game = with_tier

        # 5) What list_past_ids returns (tier + game)
        past_ids = event_repo.list_past_ids(
            driver_tier=driver_tier,
            driver_games=driver_games if driver_games else None,
            limit=500,
            offset=0,
            recent_days=RECENT_DAYS,
        )
        count_past = event_repo.count_past_ids(
            driver_tier=driver_tier,
            driver_games=driver_games if driver_games else None,
            recent_days=RECENT_DAYS,
        )

        # 6) After rig filter (what API actually returns)
        events_after_rig = []
        if past_ids:
            events_by_id = {e.id: e for e in event_repo.list_by_ids(past_ids, order_by_start=False)}
            for eid in past_ids:
                e = events_by_id.get(eid)
                if not e:
                    continue
                if driver_rig_satisfies_event(driver.rig_options, e.rig_options):
                    events_after_rig.append(e)

        # Report
        print("=== Past events diagnostic ===")
        print(f"Driver: {driver.id} ({getattr(driver, 'name', '—')})")
        print(f"Driver tier: {driver_tier}")
        print(f"Driver sim_games: {driver.sim_games}")
        print(f"Driver games (expanded for match): {driver_games}")
        print(f"Driver rig_options: {driver.rig_options}")
        print(f"Window: last {RECENT_DAYS} days (since {since.isoformat()} until now {now.isoformat()})")
        print()
        print("Counts:")
        print(f"  Past events in DB (in window):     {len(past_in_window)}")
        print(f"  After tier match (== {driver_tier}):     {len(with_tier)}")
        print(f"  After game filter (sim_games):   {len(with_game)}")
        print(f"  list_past_ids (tier+game):        {len(past_ids)} (count_past_ids={count_past})")
        print(f"  After rig filter (API result):    {len(events_after_rig)}")
        print()

        if not past_in_window:
            print("Reason: No past events in DB in the last 30 days.")
            print("  Create events with start_time_utc in the past or run test data scripts.")
            return
        if not with_tier:
            print("Reason: No past events match driver tier (exact match required).")
            print(f"  Driver tier is {driver_tier}. Event tiers in window: {sorted(set(tier_by_event.get(e.id, '?') for e in past_in_window))}")
            return
        if driver_games and not with_game:
            print("Reason: No past events match driver sim_games.")
            print(f"  Driver games (expanded): {driver_games}. Event games in window: {sorted(set(e.game for e in past_in_window if e.game))}")
            return
        if not past_ids:
            print("Reason: list_past_ids returned 0 (tier+game filter in DB). Check repo logic.")
            return
        if not events_after_rig:
            print("Reason: All candidate events filtered out by rig (driver rig does not satisfy event.rig_options).")
            print("  Check driver.rig_options and event.rig_options (wheel_type, pedals_class, manual_with_clutch).")
            return

        print("Past events should be visible. First 3 returned by API (after rig):")
        for e in events_after_rig[:3]:
            c_tier = tier_by_event.get(e.id, "?")
            print(f"  - {e.id} | {e.title} | start={e.start_time_utc} | tier={c_tier} | game={e.game}")
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Background runner for mock event service: creates random E2 ACC events every N minutes."""

from __future__ import annotations

import logging
import threading
import time

from app.core.settings import settings
from app.db.session import SessionLocal
from app.services.mock_event_service import tick_mock_events

logger = logging.getLogger("racerpath")


def _run_tick() -> None:
    session = SessionLocal()
    try:
        interval_min = max(1, getattr(settings, "mock_event_interval_minutes", 5))
        minutes_until_start = max(0, getattr(settings, "mock_event_minutes_until_start", 5))
        result = tick_mock_events(
            session,
            tier="E2",
            game="ACC",
            minutes_until_start=minutes_until_start,
            count=1,
        )
        session.commit()
        created = result.get("events_created") or []
        if created:
            logger.info("mock_event: created %s event(s)", len(created))
    except Exception as e:
        logger.exception("mock_event tick failed: %s", e)
        session.rollback()
    finally:
        session.close()


def start_mock_event_background() -> None:
    if not getattr(settings, "mock_event_enabled", False):
        return
    interval_min = max(1, getattr(settings, "mock_event_interval_minutes", 5))

    def _loop() -> None:
        time.sleep(60)  # first tick after 1 min so app is up
        while True:
            _run_tick()
            time.sleep(interval_min * 60)

    thread = threading.Thread(target=_loop, daemon=True, name="mock_event")
    thread.start()
    logger.info(
        "mock_event: background thread started (interval=%s min, start_in=%s min)",
        interval_min,
        getattr(settings, "mock_event_minutes_until_start", 5),
    )

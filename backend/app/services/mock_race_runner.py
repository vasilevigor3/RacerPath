"""Background runner for mock race service: runs tick_mock_races periodically when MOCK_RACE_ENABLED."""

from __future__ import annotations

import logging
import threading
import time

from app.core.settings import settings
from app.db.session import SessionLocal
from app.events.participation_events import dispatch_participation_completed
from app.services.mock_incident_service import tick_mock_incidents
from app.services.mock_race_service import tick_mock_races
from app.services.crs import recompute_crs

logger = logging.getLogger("racerpath")


def _run_tick() -> None:
    session = SessionLocal()
    interval = max(1, getattr(settings, "mock_race_interval_seconds", 60))
    try:
        result = tick_mock_races(session, interval_seconds=interval)
        if getattr(settings, "mock_incident_enabled", True):
            inc_result = tick_mock_incidents(
                session,
                probability=getattr(settings, "mock_incident_probability", 0.15),
            )
            for driver_id, discipline in inc_result.get("driver_discipline_pairs") or []:
                try:
                    recompute_crs(session, driver_id, discipline, trigger_participation_id=None)
                except Exception:
                    pass
        session.commit()
        for driver_id, participation_id in result.get("finished_driver_participation_pairs") or []:
            dispatch_session = SessionLocal()
            try:
                dispatch_participation_completed(dispatch_session, driver_id, participation_id)
                dispatch_session.commit()
            except Exception as e:
                logger.warning("mock_race: dispatch_participation_completed failed: %s", e)
                dispatch_session.rollback()
            finally:
                dispatch_session.close()
        if result.get("participations_updated") or result.get("participations_finished"):
            logger.info(
                "mock_race: events=%s updated=%s finished=%s",
                result.get("events_processed"),
                result.get("participations_updated"),
                result.get("participations_finished"),
            )
    except Exception as e:
        logger.exception("mock_race tick failed: %s", e)
        session.rollback()
    finally:
        session.close()


def _loop() -> None:
    interval = max(1, getattr(settings, "mock_race_interval_seconds", 60))
    # First tick after 10s so app is up
    time.sleep(10)
    while True:
        if getattr(settings, "mock_race_enabled", False):
            _run_tick()
        time.sleep(interval)


def start_mock_race_background() -> None:
    if not getattr(settings, "mock_race_enabled", False):
        return
    thread = threading.Thread(target=_loop, daemon=True, name="mock_race")
    thread.start()
    logger.info("mock_race: background thread started (interval=%ss)", settings.mock_race_interval_seconds)

"""
Mock race service: simulates a real race server.

- Race fills in at most 1 minute of real time: total_laps = 60 / MOCK_RACE_INTERVAL_SECONDS.
- Each tick (every MOCK_RACE_INTERVAL_SECONDS) = one lap event: append one new lap with
  realistic random data; no full regenerate.

For events that have started (start_time_utc <= now) and not yet finished,
generates: started_at / finished_at, lap_times, laps_completed, consistency_score,
pace_delta, position_overall, position_class.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.participation import Participation, ParticipationState, ParticipationStatus


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _lap_times_to_consistency_score(lap_times: List[float]) -> float:
    """Convert lap times (seconds) to a 0–10 consistency score. Lower stddev = higher score."""
    if len(lap_times) < 2:
        return 5.0
    n = len(lap_times)
    mean = sum(lap_times) / n
    variance = sum((x - mean) ** 2 for x in lap_times) / (n - 1)
    stddev = math.sqrt(variance)
    # stddev ~0 -> 10, stddev ~2 -> 5, stddev 5+ -> 0
    score = 10.0 - min(10.0, stddev * 2.5)
    return round(max(0.0, min(10.0, score)), 1)


def _lap_times_to_pace_delta(lap_times: List[float], best_lap_in_session: float | None) -> float:
    """Average lap time minus best lap in session (seconds per lap)."""
    if not lap_times or best_lap_in_session is None:
        return 0.0
    avg = sum(lap_times) / len(lap_times)
    return round(max(0.0, avg - best_lap_in_session), 2)


def _events_in_progress(session: Session, now: datetime) -> List[Event]:
    """Events that have started and not yet finished."""
    return (
        session.query(Event)
        .filter(
            Event.start_time_utc.isnot(None),
            Event.start_time_utc <= now,
        )
        .filter(
            (Event.finished_time_utc.is_(None)) | (Event.finished_time_utc > now)
        )
        .all()
    )


def _participations_to_simulate(session: Session, event: Event) -> List[Participation]:
    """Participations for this event that are registered or started (not completed/withdrawn)."""
    return (
        session.query(Participation)
        .filter(
            Participation.event_id == event.id,
            Participation.participation_state.in_([
                ParticipationState.registered,
                ParticipationState.started,
            ]),
        )
        .all()
    )


def _one_lap_time(
    base_seconds: float = 90.0,
    driver_speed_factor: float = 1.0,
    consistency: float = 0.7,
) -> float:
    """Generate one realistic lap time (seconds)."""
    sigma = 0.8 * (1.1 - consistency)
    lap = base_seconds / driver_speed_factor + random.gauss(0, sigma)
    return round(max(60.0, lap), 2)


def tick_mock_races(session: Session, interval_seconds: int = 15) -> dict:
    """
    One tick of the mock race service. Each tick = one lap event (one new lap per participation).
    Race fills in at most 1 minute: total_laps = 60 / interval_seconds.
    Returns summary: events_processed, participations_updated, participations_finished.
    """
    now = _ensure_utc(datetime.now(timezone.utc)) or datetime.now(timezone.utc)
    events = _events_in_progress(session, now)
    participations_updated = 0
    participations_finished = 0
    finished_pairs: List[tuple[str, str]] = []

    interval_sec = max(1, interval_seconds)
    total_laps = max(1, 60 // interval_sec)  # race completes in 1 minute of real time

    for event in events:
        start_utc = _ensure_utc(event.start_time_utc)
        finished_utc = _ensure_utc(event.finished_time_utc)
        if not start_utc:
            continue

        elapsed_seconds = (now - start_utc).total_seconds()
        tick_index = int(elapsed_seconds / interval_sec)  # 0, 1, 2, ...
        laps_done = min(tick_index + 1, total_laps)
        race_finished = (tick_index + 1) >= total_laps
        finish_at = start_utc + timedelta(seconds=total_laps * interval_sec) if race_finished else None
        if race_finished and finish_at:
            event.finished_time_utc = finish_at

        participations = _participations_to_simulate(session, event)
        if not participations:
            continue

        # When race just started: set started_at for all registered
        for p in participations:
            if p.participation_state == ParticipationState.registered and p.started_at is None:
                p.started_at = start_utc
                p.participation_state = ParticipationState.started
                participations_updated += 1

        # One lap per tick: append new lap(s) so we have laps_done total (usually +1 this tick)
        rng = random.Random(f"{event.id}-{now.isoformat()}")
        base_lap = 88.0 + rng.uniform(0, 6)
        best_lap_session = base_lap - 1.5

        for part in participations:
            existing = list((part.raw_metrics or {}).get("lap_times") or [])
            driver_seed = hash((part.driver_id, event.id)) % 1000
            speed = 0.92 + (driver_seed % 15) / 100.0
            consistency_val = 0.5 + (driver_seed % 50) / 100.0
            to_add = laps_done - len(existing)
            for _ in range(max(0, to_add)):
                existing.append(
                    _one_lap_time(
                        base_seconds=base_lap,
                        driver_speed_factor=speed,
                        consistency=consistency_val,
                    )
                )
            lap_times = existing
            best_lap_session = min(best_lap_session, min(lap_times) if lap_times else base_lap)

            part.laps_completed = len(lap_times)
            part.raw_metrics = {**(part.raw_metrics or {}), "lap_times": lap_times}
            part.consistency_score = _lap_times_to_consistency_score(lap_times)

            if race_finished:
                part.finished_at = finish_at
                part.participation_state = ParticipationState.completed
                part.status = ParticipationStatus.finished
                participations_finished += 1
                finished_pairs.append((part.driver_id, part.id))

            participations_updated += 1

        # Assign positions by average lap time
        avg_laps = []
        for part in participations:
            lt = (part.raw_metrics or {}).get("lap_times") or []
            avg_laps.append((part.id, sum(lt) / len(lt) if lt else 999.0))
        avg_laps.sort(key=lambda x: x[1])
        for rank, (pid, _) in enumerate(avg_laps, start=1):
            for p in participations:
                if p.id == pid:
                    p.position_overall = rank
                    p.position_class = rank
                    break

        for part in participations:
            lt = (part.raw_metrics or {}).get("lap_times") or []
            part.pace_delta = _lap_times_to_pace_delta(lt, best_lap_session)

    return {
        "events_processed": len(events),
        "participations_updated": participations_updated,
        "participations_finished": participations_finished,
        "finished_driver_participation_pairs": finished_pairs,
    }

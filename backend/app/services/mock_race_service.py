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

import logging
import math
import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.participation import Participation, ParticipationState, ParticipationStatus

logger = logging.getLogger("racerpath.mock_race")


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


# ACC GT3 typical lap times (seconds) — realistic base per track
ACC_GT3_BASE_LAP_SECONDS = {
    "monza": 106.0,
    "spa": 138.0,
    "nürburgring": 115.0,
    "nurburgring": 115.0,
    "silverstone": 118.0,
    "barcelona": 106.0,
    "paul ricard": 108.0,
    "paul_ricard": 108.0,
    "hungaroring": 112.0,
    "zandvoort": 107.0,
    "imola": 106.0,
    "kyalami": 108.0,
    "suzuka": 127.0,
    "laguna seca": 79.0,
    "laguna_seca": 79.0,
    "misano": 106.0,
    "brands_hatch": 88.0,
    "brands hatch": 88.0,
    "mount panorama": 132.0,
    "bathurst": 132.0,
    "cota": 133.0,
    "watkins glen": 106.0,
    "valencia": 97.0,
    "donington": 72.0,
    "oulton park": 72.0,
}
DEFAULT_BASE_LAP_SECONDS = 106.0  # fallback (e.g. Monza-like)


def _base_lap_from_event(event: Event) -> float:
    """Infer ACC-style base lap time (seconds) from event title/track."""
    title = (getattr(event, "title", None) or "").lower()
    for key, base in ACC_GT3_BASE_LAP_SECONDS.items():
        if key in title:
            return base + random.uniform(-1.5, 2.0)
    return DEFAULT_BASE_LAP_SECONDS + random.uniform(-2.0, 2.0)


def _one_lap_time(
    base_seconds: float = 106.0,
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

    if events:
        logger.info(
            "tick: now=%s interval=%ss total_laps=%s events_count=%s",
            now.isoformat(), interval_sec, total_laps, len(events),
        )

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

        event_title = getattr(event, "title", None) or event.id[:8]
        logger.info(
            "event: event_id=%s title=%s tick=%s laps_done=%s/%s finished=%s",
            event.id[:8], event_title, tick_index, laps_done, total_laps, race_finished,
        )

        participations = _participations_to_simulate(session, event)
        if not participations:
            continue

        # When race just started: set started_at for all registered
        for p in participations:
            if p.participation_state == ParticipationState.registered and p.started_at is None:
                p.started_at = start_utc
                p.participation_state = ParticipationState.started
                participations_updated += 1

        # One lap per tick: base lap from event (ACC track‑aware), then append new lap(s)
        rng = random.Random(f"{event.id}-{now.isoformat()}")
        base_lap = _base_lap_from_event(event)
        best_lap_session = base_lap - 1.5

        for part in participations:
            existing = list((part.raw_metrics or {}).get("lap_times") or [])
            driver_seed = hash((part.driver_id, event.id)) % 1000
            speed = 0.92 + (driver_seed % 15) / 100.0
            consistency_val = 0.5 + (driver_seed % 50) / 100.0
            to_add = laps_done - len(existing)
            new_laps: List[float] = []
            for _ in range(max(0, to_add)):
                lap_s = _one_lap_time(
                    base_seconds=base_lap,
                    driver_speed_factor=speed,
                    consistency=consistency_val,
                )
                existing.append(lap_s)
                new_laps.append(lap_s)
            lap_times = existing
            best_lap_session = min(best_lap_session, min(lap_times) if lap_times else base_lap)

            part.laps_completed = len(lap_times)
            # ACC-like: sector_times as list of [s1, s2, s3] per lap (approx 40%/35%/25% + noise)
            existing_sectors = list((part.raw_metrics or {}).get("sector_times") or [])
            for i in range(len(existing_sectors), len(lap_times)):
                lt = lap_times[i]
                r = random.Random(f"{part.id}-{i}")
                s1 = round(lt * (0.38 + r.uniform(0, 0.04)) + r.gauss(0, 0.2), 2)
                s2 = round(lt * (0.34 + r.uniform(0, 0.04)) + r.gauss(0, 0.2), 2)
                s3 = round(lt - s1 - s2, 2)
                existing_sectors.append([max(0.1, s1), max(0.1, s2), max(0.1, s3)])
            part.raw_metrics = {
                **(part.raw_metrics or {}),
                "lap_times": lap_times,
                "sector_times": existing_sectors,
            }
            part.consistency_score = _lap_times_to_consistency_score(lap_times)

            if race_finished:
                part.finished_at = finish_at
                part.participation_state = ParticipationState.completed
                part.status = ParticipationStatus.finished
                participations_finished += 1
                finished_pairs.append((part.driver_id, part.id))
                logger.info(
                    "part_finished: event_id=%s part_id=%s driver_id=%s laps=%s",
                    event.id[:8], part.id[:8], part.driver_id[:8], len(lap_times),
                )
            elif new_laps:
                logger.info(
                    "lap: event_id=%s part_id=%s driver_id=%s lap_s=%.2f laps=%s consistency=%.1f",
                    event.id[:8], part.id[:8], part.driver_id[:8],
                    new_laps[-1], len(lap_times), part.consistency_score,
                )

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

        logger.info(
            "positions: event_id=%s %s",
            event.id[:8],
            ", ".join(f"P{p.position_overall}({p.driver_id[:8]})" for p in participations),
        )

        for part in participations:
            lt = (part.raw_metrics or {}).get("lap_times") or []
            part.pace_delta = _lap_times_to_pace_delta(lt, best_lap_session)

    return {
        "events_processed": len(events),
        "participations_updated": participations_updated,
        "participations_finished": participations_finished,
        "finished_driver_participation_pairs": finished_pairs,
    }

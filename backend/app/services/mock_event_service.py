"""
Mock event service: creates random E2 ACC events every N minutes, with start in M minutes.

Configurable: interval (e.g. 5 min), minutes_until_start (e.g. 5), tier (E2), game (ACC).
Each tick creates one event with random title/track/duration, start_time_utc = now + minutes_until_start.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.event import Event
from app.services.classifier import build_event_payload, classify_event
from app.services.timeline_validation import validate_event_timeline
from app.core.constants import TIER_LABELS

logger = logging.getLogger("racerpath.mock_event")

MOCK_TRACKS = [
    "Monza", "Spa", "Nürburgring", "Silverstone", "Barcelona", "Paul Ricard",
    "Hungaroring", "Zandvoort", "Imola", "Kyalami", "Suzuka", "Laguna Seca",
]
MOCK_TITLES = [
    "Sprint", "60 min", "Endurance", "GT3 Cup", "Mixed Class",
]


def _random_event_data(
    game: str = "ACC",
    tier: str = "E2",
    minutes_until_start: int = 5,
) -> dict:
    """Build minimal Event-compatible dict for one random E2 ACC event."""
    now = datetime.now(timezone.utc)
    start = now + timedelta(minutes=minutes_until_start)
    duration = random.choice([30, 45, 60, 90])
    finished = start + timedelta(minutes=duration)
    track = random.choice(MOCK_TRACKS)
    suffix = random.choice(MOCK_TITLES)
    title = f"Mock {game} {tier} · {track} {suffix}"
    return {
        "title": title[:200],
        "source": "mock",
        "game": game,
        "country": None,
        "city": None,
        "start_time_utc": start,
        "finished_time_utc": finished,
        "session_type": "race",
        "schedule_type": "weekly",
        "event_type": "circuit",
        "format_type": "sprint",
        "session_list": [],
        "team_size_min": 1,
        "team_size_max": 1,
        "rolling_start": False,
        "pit_rules": {},
        "duration_minutes": duration,
        "grid_size_expected": random.choice([20, 24, 28, 30]),
        "class_count": 1,
        "car_class_list": ["GT3"],
        "damage_model": "full",
        "penalties": "standard",
        "fuel_usage": "real",
        "tire_wear": "real",
        "weather": "fixed",
        "night": False,
        "time_acceleration": False,
        "surface_type": "asphalt",
        "track_type": "road",
        "stewarding": "standard",
        "team_event": False,
        "license_requirement": "none",
        "official_event": False,
        "assists_allowed": False,
        "rig_options": None,
        "task_codes": None,
    }


def tick_mock_events(
    session: Session,
    *,
    tier: str = "E2",
    game: str = "ACC",
    minutes_until_start: int = 5,
    count: int = 1,
) -> dict:
    """
    Create `count` random events (tier E2, game ACC), start_time_utc = now + minutes_until_start.
    Returns events_created list of (event_id, title).
    """
    created: List[tuple[str, str]] = []
    for _ in range(count):
        data = _random_event_data(game=game, tier=tier, minutes_until_start=minutes_until_start)
        event = Event(**data)
        session.add(event)
        session.flush()
        try:
            validate_event_timeline(event)
        except ValueError as e:
            logger.warning("mock_event: timeline validation failed, skipping: %s", e)
            session.delete(event)
            session.flush()
            continue
        classification_payload = build_event_payload(event, "gt")
        classification_data = classify_event(classification_payload)
        classification_data["event_tier"] = tier
        classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)
        created.append((event.id, event.title))
        logger.info(
            "event: id=%s title=%s start=%s duration=%s min",
            event.id[:8], event.title, event.start_time_utc.isoformat() if event.start_time_utc else None,
            event.duration_minutes,
        )
    return {"events_created": created}

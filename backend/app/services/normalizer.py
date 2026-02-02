from __future__ import annotations

from typing import Any, Dict, List, Tuple

from pydantic import ValidationError

from app.schemas.event import EventCreate

from app.core.constants import (
    ALLOWED_DAMAGE,
    ALLOWED_EVENT_TYPE,
    ALLOWED_FORMAT,
    ALLOWED_FUEL,
    ALLOWED_LICENSE,
    ALLOWED_PENALTIES,
    ALLOWED_SCHEDULE,
    ALLOWED_SESSION_TYPE,
    ALLOWED_STEWARDING,
    ALLOWED_SURFACE,
    ALLOWED_TIRE,
    ALLOWED_TRACK,
    ALLOWED_WEATHER,
)


def _normalize_enum(value: Any, allowed: set[str], default: str, errors: List[str], label: str) -> str:
    if value in allowed:
        return str(value)
    if value is None:
        return default
    errors.append(f"invalid_{label}")
    return default


def _normalize_int(value: Any, default: int, errors: List[str], label: str) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f"invalid_{label}")
        return default


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _normalize_session_list(value: Any) -> List[str]:
    sessions = _normalize_list(value)
    allowed = {"practice", "qualifying", "race"}
    return [item for item in sessions if item in allowed]


def normalize_raw_event(source: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any] | None, List[str]]:
    errors: List[str] = []
    base = payload.get("event") if isinstance(payload.get("event"), dict) else payload

    title = base.get("title") or base.get("name")
    if not title:
        errors.append("missing_title")

    event_type = _normalize_enum(
        base.get("event_type"),
        ALLOWED_EVENT_TYPE,
        "circuit",
        errors,
        "event_type",
    )
    if event_type == "offroad":
        event_type = "karting"

    normalized = {
        "title": title or "",
        "source": source,
        "game": base.get("game") or base.get("sim") or base.get("platform"),
        "start_time_utc": base.get("start_time_utc") or base.get("start_time"),
        "session_type": _normalize_enum(
            base.get("session_type"),
            ALLOWED_SESSION_TYPE,
            "race",
            errors,
            "session_type",
        ),
        "schedule_type": _normalize_enum(
            base.get("schedule_type") or base.get("schedule"),
            ALLOWED_SCHEDULE,
            "weekly",
            errors,
            "schedule_type",
        ),
        "event_type": event_type,
        "format_type": _normalize_enum(
            base.get("format_type") or base.get("format"),
            ALLOWED_FORMAT,
            "sprint",
            errors,
            "format_type",
        ),
        "session_list": _normalize_session_list(base.get("session_list") or base.get("sessions")),
        "team_size_min": _normalize_int(base.get("team_size_min"), 1, errors, "team_size_min"),
        "team_size_max": _normalize_int(base.get("team_size_max"), 1, errors, "team_size_max"),
        "rolling_start": _normalize_bool(base.get("rolling_start")),
        "pit_rules": base.get("pit_rules") if isinstance(base.get("pit_rules"), dict) else {},
        "duration_minutes": _normalize_int(base.get("duration_minutes") or base.get("duration"), 0, errors, "duration"),
        "grid_size_expected": _normalize_int(base.get("grid_size_expected") or base.get("grid"), 0, errors, "grid"),
        "class_count": _normalize_int(base.get("class_count") or base.get("classes"), 1, errors, "class_count"),
        "car_class_list": _normalize_list(base.get("car_class_list") or base.get("car_classes")),
        "damage_model": _normalize_enum(base.get("damage_model") or base.get("damage"), ALLOWED_DAMAGE, "off", errors, "damage_model"),
        "penalties": _normalize_enum(base.get("penalties"), ALLOWED_PENALTIES, "off", errors, "penalties"),
        "fuel_usage": _normalize_enum(base.get("fuel_usage") or base.get("fuel"), ALLOWED_FUEL, "off", errors, "fuel_usage"),
        "tire_wear": _normalize_enum(base.get("tire_wear") or base.get("tire"), ALLOWED_TIRE, "off", errors, "tire_wear"),
        "weather": _normalize_enum(base.get("weather"), ALLOWED_WEATHER, "fixed", errors, "weather"),
        "night": _normalize_bool(base.get("night")),
        "time_acceleration": _normalize_bool(base.get("time_acceleration")),
        "surface_type": _normalize_enum(base.get("surface_type"), ALLOWED_SURFACE, None, errors, "surface_type"),
        "track_type": _normalize_enum(base.get("track_type"), ALLOWED_TRACK, None, errors, "track_type"),
        "stewarding": _normalize_enum(base.get("stewarding"), ALLOWED_STEWARDING, "none", errors, "stewarding"),
        "team_event": _normalize_bool(base.get("team_event") or base.get("team")),
        "license_requirement": _normalize_enum(
            base.get("license_requirement") or base.get("license"),
            ALLOWED_LICENSE,
            "none",
            errors,
            "license_requirement",
        ),
        "official_event": _normalize_bool(base.get("official_event") or base.get("official")),
        "assists_allowed": _normalize_bool(base.get("assists_allowed") or base.get("assists")),
    }

    try:
        validated = EventCreate.model_validate(normalized)
    except ValidationError as exc:
        errors.extend(["validation_error"])
        return None, errors

    return validated.model_dump(), errors

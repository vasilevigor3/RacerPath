from __future__ import annotations

import hashlib
import json
from typing import Dict, List

from app.core.settings import settings
from app.core.constants import TIER_LABELS, TIER_RANK


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def duration_factor(minutes: int) -> float:
    if minutes < 10:
        return 0.1
    if minutes < 30:
        return 0.3
    if minutes < 60:
        return 0.5
    if minutes < 180:
        return 0.8
    return 1.0


def format_factor(fmt: str) -> float:
    return {
        "sprint": 0.3,
        "endurance": 0.8,
        "series": 0.7,
        "time_trial": 0.0,
    }.get(fmt, 0.3)


def realism_factor(damage: str, penalties: str, fuel: str, tire: str) -> float:
    if damage == "full" and penalties in {"standard", "strict"} and fuel == "real" and tire == "real":
        return 1.0
    if damage == "off" or penalties == "off":
        return 0.2
    if damage in {"limited", "full"} and penalties in {"low", "standard", "strict"}:
        return 0.6
    return 0.4


def schedule_factor(schedule: str) -> float:
    return {
        "daily": 0.2,
        "weekly": 0.5,
        "seasonal": 0.8,
        "special": 1.0,
    }.get(schedule, 0.4)


def license_factor(level: str) -> float:
    return {
        "none": 0.1,
        "entry": 0.3,
        "intermediate": 0.5,
        "advanced": 0.7,
        "pro_sim": 0.9,
    }.get(level, 0.2)


def stewarding_factor(level: str) -> float:
    return {
        "none": 0.1,
        "automated": 0.5,
        "human": 1.0,
        "human_review": 1.0,
    }.get(level, 0.3)


def environment_factor(weather: str, night: bool) -> float:
    if weather == "dynamic" and night:
        return 1.0
    if weather == "dynamic" or night:
        return 0.6
    return 0.2


def traffic_factor(grid: int, classes: int) -> float:
    if grid < 8:
        base = 0.2
    elif grid < 16:
        base = 0.4
    elif grid < 24:
        base = 0.6
    elif grid < 32:
        base = 0.8
    else:
        base = 1.0

    if classes <= 1:
        multi = 0.0
    elif classes == 2:
        multi = 0.2
    elif classes == 3:
        multi = 0.3
    else:
        multi = 0.4

    return clamp(base + multi)


def team_factor(team_size_max: int, pit_rules: dict, fmt: str, team_flag: bool) -> float:
    if team_size_max <= 1 and not team_flag:
        return 0.0
    base = 0.8 if fmt == "endurance" else 0.6
    if isinstance(pit_rules, dict) and pit_rules.get("driver_swap"):
        base += 0.2
    return clamp(base)


def tier_from_scores(difficulty: float, seriousness: float) -> str:
    min_score = min(difficulty, seriousness)
    if min_score < 35:
        return "E1"
    if min_score < 55:
        return "E2"
    if min_score < 70:
        return "E3"
    if min_score < 85:
        return "E4"
    return "E5"


def infer_primary_discipline(event_type: str | None, car_class_list: List[str], fallback: str) -> str:
    if event_type == "rally_stage":
        return "rally"
    if event_type in {"rallycross", "offroad", "karting"}:
        return "karting"
    if event_type == "historic":
        return "historic"

    for car_class in car_class_list:
        value = car_class.lower()
        if "formula" in value or value.startswith("f"):
            return "formula"
        if "gt" in value or "tcr" in value or "dtm" in value:
            return "gt"
    return fallback


def compatibility_scores(
    event_type: str | None,
    car_class_list: List[str],
    track_type: str | None,
    surface_type: str | None,
    assists: bool,
    discipline_hint: str,
) -> Dict[str, int]:
    base = {"formula": 30, "gt": 30, "rally": 30, "karting": 30, "historic": 30}
    primary = infer_primary_discipline(event_type, car_class_list, discipline_hint)
    if primary in base:
        base[primary] = 70

    if track_type in {"road", "street"}:
        base["formula"] = clamp_score(base["formula"] + 10)
        base["gt"] = clamp_score(base["gt"] + 10)
    if track_type == "stage":
        base["rally"] = clamp_score(base["rally"] + 10)
    if surface_type in {"gravel", "dirt"}:
        base["rally"] = clamp_score(base["rally"] + 10)
        base["karting"] = clamp_score(base["karting"] + 5)
    if surface_type == "mixed":
        base["karting"] = clamp_score(base["karting"] + 5)

    if assists and primary in base:
        base[primary] = clamp_score(base[primary] - 20)

    return base


def _snapshot(payload: dict) -> dict:
    return {
        "format": str(payload.get("format", "sprint")),
        "duration": int(payload.get("duration", 0) or 0),
        "grid": int(payload.get("grid", 0) or 0),
        "classes": int(payload.get("classes", 1) or 1),
        "schedule": str(payload.get("schedule", "daily")),
        "damage": str(payload.get("damage", "off")),
        "penalties": str(payload.get("penalties", "off")),
        "fuel": str(payload.get("fuel", "off")),
        "tire": str(payload.get("tire", "off")),
        "weather": str(payload.get("weather", "fixed")),
        "night": bool(payload.get("night", False)),
        "stewarding": str(payload.get("stewarding", "none")),
        "license": str(payload.get("license", "none")),
        "official": bool(payload.get("official", False)),
        "assists": bool(payload.get("assists", False)),
        "event_type": payload.get("event_type"),
        "car_class_list": payload.get("car_class_list") or [],
        "track_type": payload.get("track_type"),
        "surface_type": payload.get("surface_type"),
        "team_size_max": int(payload.get("team_size_max", 1) or 1),
        "pit_rules": payload.get("pit_rules") if isinstance(payload.get("pit_rules"), dict) else {},
        "team": bool(payload.get("team", False)),
        "rolling_start": bool(payload.get("rolling_start", False)),
        "time_acceleration": bool(payload.get("time_acceleration", False)),
        "session_list": payload.get("session_list") or [],
        "discipline_hint": str(payload.get("discipline", "gt")),
    }


def _hash_snapshot(snapshot: dict) -> str:
    payload_bytes = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def classify_event(payload: dict) -> dict:
    snapshot = _snapshot(payload)

    fmt = snapshot["format"]
    duration = snapshot["duration"]
    grid = snapshot["grid"]
    classes = snapshot["classes"]
    damage = snapshot["damage"]
    penalties = snapshot["penalties"]
    fuel = snapshot["fuel"]
    tire = snapshot["tire"]
    schedule = snapshot["schedule"]
    license_level = snapshot["license"]
    stewarding = snapshot["stewarding"]
    weather = snapshot["weather"]
    night = snapshot["night"]
    official = snapshot["official"]
    assists = snapshot["assists"]
    event_type = snapshot["event_type"]
    car_class_list = snapshot["car_class_list"]
    track_type = snapshot["track_type"]
    surface_type = snapshot["surface_type"]
    team_size_max = snapshot["team_size_max"]
    pit_rules = snapshot["pit_rules"]
    team_flag = snapshot["team"]
    discipline_hint = snapshot["discipline_hint"]

    duration_f = duration_factor(duration)
    format_f = format_factor(fmt)
    realism_f = realism_factor(damage, penalties, fuel, tire)
    environment_f = environment_factor(weather, night)
    traffic_f = traffic_factor(grid, classes)
    team_f = team_factor(team_size_max, pit_rules, fmt, team_flag)
    schedule_f = schedule_factor(schedule)
    license_f = license_factor(license_level)
    steward_f = stewarding_factor(stewarding)
    regulation_f = clamp(license_f * 0.6 + steward_f * 0.4)

    difficulty_score = (
        duration_f * 0.25
        + format_f * 0.15
        + environment_f * 0.15
        + traffic_f * 0.15
        + realism_f * 0.20
        + team_f * 0.10
    ) * 100

    seriousness_score = (
        schedule_f * 0.20
        + regulation_f * 0.25
        + steward_f * 0.15
        + (1.0 if official else 0.0) * 0.15
        + license_f * 0.15
        + realism_f * 0.10
    ) * 100

    caps_applied = []
    max_tier = None

    if fmt == "time_trial":
        caps_applied.append("time_trial_excluded")
        tier = "E0"
    else:
        tier = tier_from_scores(difficulty_score, seriousness_score)

    if penalties == "off" or damage == "off":
        caps_applied.append("penalties_or_damage_off")
        seriousness_score = min(seriousness_score, 40)
        max_tier = "E1"

    if duration < 10 and classes == 1:
        caps_applied.append("short_single_class")
        max_tier = "E1"

    if grid < 8:
        caps_applied.append("low_grid")
        max_tier = "E1"

    if max_tier and TIER_RANK.get(tier, 0) > TIER_RANK[max_tier]:
        tier = max_tier

    return {
        "event_tier": tier,
        "tier_label": TIER_LABELS.get(tier, "Unknown"),
        "difficulty_score": round(difficulty_score, 1),
        "seriousness_score": round(seriousness_score, 1),
        "realism_score": round(realism_f * 100, 1),
        "discipline_compatibility": compatibility_scores(
            event_type,
            car_class_list,
            track_type,
            surface_type,
            assists,
            discipline_hint,
        ),
        "caps_applied": caps_applied,
        "classification_version": settings.classification_version,
        "inputs_hash": _hash_snapshot(snapshot),
        "inputs_snapshot": snapshot,
    }


def build_event_payload(event, discipline_hint: str = "gt") -> dict:
    return {
        "format": event.format_type,
        "duration": event.duration_minutes,
        "grid": event.grid_size_expected,
        "classes": event.class_count,
        "schedule": event.schedule_type,
        "damage": event.damage_model,
        "penalties": event.penalties,
        "fuel": event.fuel_usage,
        "tire": event.tire_wear,
        "weather": event.weather,
        "night": event.night,
        "stewarding": event.stewarding,
        "team": event.team_event,
        "license": event.license_requirement,
        "official": event.official_event,
        "discipline": discipline_hint,
        "assists": event.assists_allowed,
        "event_type": event.event_type,
        "car_class_list": event.car_class_list,
        "track_type": event.track_type,
        "surface_type": event.surface_type,
        "team_size_max": event.team_size_max,
        "pit_rules": event.pit_rules,
        "rolling_start": event.rolling_start,
        "time_acceleration": event.time_acceleration,
        "session_list": event.session_list,
    }

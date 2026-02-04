"""
Platform-specific incident config: code → score, incident_type, penalty.

Code format: {platform}_{incident_slug}_{penalty_slug}, e.g. acc_off_track_time_penalty,
iracing_blocking_no_penalty. Code must match Event.game (platform) so we validate prefix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path(__file__).resolve().parent
_SUPPORTED_PLATFORMS = ("acc", "iracing")

# Event.game (various spellings) → config key
GAME_TO_PLATFORM: dict[str, str] = {
    "acc": "acc",
    "assetto corsa competizione": "acc",
    "ac": "acc",
    "assetto corsa": "acc",
    "iracing": "iracing",
}

# Valid code prefixes (must match platform)
CODE_PREFIXES = _SUPPORTED_PLATFORMS

_CACHE: dict[str, dict[str, Any]] = {}


def _load_platform_config(platform: str) -> dict[str, Any]:
    if platform in _CACHE:
        return _CACHE[platform]
    path = _CONFIG_DIR / f"{platform}.json"
    if not path.exists():
        _CACHE[platform] = {}
        return _CACHE[platform]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _CACHE[platform] = data.get("codes", {})
    return _CACHE[platform]


def normalize_game_to_platform(game: str | None) -> str | None:
    """Map Event.game to platform key (acc, iracing) for config lookup. None if unknown."""
    if not game or not isinstance(game, str):
        return None
    key = game.strip().lower()
    return GAME_TO_PLATFORM.get(key)


def _normalize_code(code: str) -> str:
    """Lowercase, strip; for lookup in config."""
    return (code or "").strip().lower().replace(" ", "_")


def code_platform_prefix(code: str) -> str | None:
    """
    Extract platform prefix from code. Code must be like acc_... or iracing_...
    Returns 'acc' or 'iracing' or None if prefix not recognized.
    """
    normalized = _normalize_code(code)
    if not normalized or "_" not in normalized:
        return None
    prefix = normalized.split("_", 1)[0]
    return prefix if prefix in CODE_PREFIXES else None


def validate_code_for_platform(platform: str | None, code: str) -> tuple[bool, str]:
    """
    Check that code is valid for the event's platform.
    Returns (True, "") if valid, (False, "error message") otherwise.
    """
    if not platform or platform not in _SUPPORTED_PLATFORMS:
        return False, "Event game is not set or not supported (use ACC or iRacing)"
    prefix = code_platform_prefix(code)
    if not prefix:
        return False, f"Code must start with a platform prefix (acc_ or iracing_), e.g. acc_off_track_time_penalty"
    if prefix != platform:
        return False, f"Code prefix '{prefix}_' does not match event platform '{platform}' (event game must match code)"
    config = _load_platform_config(platform)
    key = _normalize_code(code)
    if key not in config:
        return False, f"Unknown incident code '{code}' for platform '{platform}'"
    return True, ""


def get_incident_by_code(platform: str | None, code: str) -> dict[str, Any] | None:
    """
    Return config entry for platform + code: score, incident_type, penalty, time_seconds (optional).
    Code must start with platform prefix and exist in platform config; otherwise returns None.
    """
    if not platform or platform not in _SUPPORTED_PLATFORMS:
        return None
    prefix = code_platform_prefix(code)
    if prefix != platform:
        return None
    config = _load_platform_config(platform)
    key = _normalize_code(code)
    entry = config.get(key)
    if not entry or not isinstance(entry, dict):
        return None
    penalty = entry.get("penalty", "no_penalty")
    return {
        "score": float(entry.get("score", 0.0)),
        "incident_type": str(entry.get("incident_type", "Other")),
        "penalty": penalty if penalty in ("no_penalty", "time_penalty", "drive_through", "stop_and_go", "dsq") else "no_penalty",
        "time_seconds": int(entry["time_seconds"]) if entry.get("time_seconds") is not None else (5 if penalty == "time_penalty" else None),
    }


def get_platform_codes(platform: str | None) -> list[str]:
    """Return list of incident codes for the platform (for mocks). Empty if unknown platform."""
    if not platform or platform not in _SUPPORTED_PLATFORMS:
        return []
    config = _load_platform_config(platform)
    return list(config.keys())

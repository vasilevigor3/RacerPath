"""Task-related constants: disciplines, scope/period, requirement keys."""

DISCIPLINES = ["gt", "formula", "rally", "karting", "historic"]

DISCIPLINE_ALIASES = {"offroad": "karting"}

REQUIREMENT_COLUMN_KEYS = (
    "min_duration_minutes",
    "max_incidents",
    "max_penalties",
    "require_night",
    "require_dynamic_weather",
    "require_team_event",
    "require_clean_finish",
    "allow_non_finish",
    "max_position_overall",
    "min_position_overall",
    "min_laps_completed",
    "repeatable",
    "max_completions",
    "cooldown_hours",
    "diversity_window_days",
    "max_same_event_count",
    "require_event_diversity",
    "max_same_signature_count",
    "signature_cooldown_hours",
    "diminishing_returns",
    "diminishing_step",
    "diminishing_floor",
    "manual",
)

DEFAULT_ROLLING_WINDOW_SIZE = 5
DEFAULT_ROLLING_WINDOW_UNIT = "participations"

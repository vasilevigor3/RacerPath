"""Platform-specific incident code → score, incident_type, penalty. Codes: acc_*, iracing_*."""

from app.core.incident_config.loader import (
    code_platform_prefix,
    get_incident_by_code,
    get_platform_codes,
    normalize_game_to_platform,
    validate_code_for_platform,
)

__all__ = [
    "code_platform_prefix",
    "get_incident_by_code",
    "get_platform_codes",
    "normalize_game_to_platform",
    "validate_code_for_platform",
]

"""Event domain: tier order, discipline inference, tier-for-readiness (pure, no DB)."""

from app.core.constants import TIER_ORDER


def infer_discipline(event_type: str, car_class_list: list | None = None) -> str:
    """Infer discipline from event_type and optional car_class_list."""
    if event_type == "rally_stage":
        return "rally"
    if event_type in {"rallycross", "offroad", "karting"}:
        return "karting"
    if event_type == "historic":
        return "historic"
    for car_class in car_class_list or []:
        if "formula" in (car_class or "").lower():
            return "formula"
    return "gt"


def tier_range_for_readiness(crs_score: float) -> tuple[str, str]:
    """Return (min_tier, max_tier) for a given CRS readiness score."""
    if crs_score >= 85:
        return "E3", "E4"
    if crs_score >= 70:
        return "E2", "E3"
    return "E1", "E2"

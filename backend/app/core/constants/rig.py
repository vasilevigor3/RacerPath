"""Rig/hardware constants for driver profile compatibility."""

WHEEL_ORDER = {"legacy": 0, "force_feedback_nm": 1}
PEDALS_ORDER = {"basic": 0, "spring": 1, "premium": 2}
DEFAULT_DRIVER_RIG = {
    "wheel_type": "legacy",
    "pedals_class": "basic",
    "manual_with_clutch": False,
}

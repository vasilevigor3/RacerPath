"""Rig compatibility: event.rig_options = minimum required; driver must meet or exceed."""

WHEEL_ORDER = {"legacy": 0, "force_feedback_nm": 1}
PEDALS_ORDER = {"basic": 0, "spring": 1, "premium": 2}

# Driver with no rig_options is treated as minimal rig (legacy, basic, no clutch)
DEFAULT_DRIVER_RIG = {"wheel_type": "legacy", "pedals_class": "basic", "manual_with_clutch": False}


def driver_rig_satisfies_event(driver_rig: dict | None, event_rig: dict | None) -> bool:
    """True if driver's rig meets or exceeds event's required rig. If event has no rig_options, True."""
    if not event_rig or (not event_rig.get("wheel_type") and not event_rig.get("pedals_class") and event_rig.get("manual_with_clutch") is None):
        return True
    driver = driver_rig if driver_rig else DEFAULT_DRIVER_RIG
    # Wheel: event requires at least X; driver must have >= X
    req_wheel = event_rig.get("wheel_type")
    if req_wheel and req_wheel in WHEEL_ORDER:
        driver_wheel = driver.get("wheel_type")
        if driver_wheel not in WHEEL_ORDER:
            return False
        if WHEEL_ORDER[driver_wheel] < WHEEL_ORDER[req_wheel]:
            return False
    # Pedals: event requires at least X; driver must have >= X
    req_pedals = event_rig.get("pedals_class")
    if req_pedals and req_pedals in PEDALS_ORDER:
        driver_pedals = driver.get("pedals_class")
        if driver_pedals not in PEDALS_ORDER:
            return False
        if PEDALS_ORDER[driver_pedals] < PEDALS_ORDER[req_pedals]:
            return False
    # Manual with clutch: if event requires True, driver must have True
    if event_rig.get("manual_with_clutch") is True and not driver.get("manual_with_clutch"):
        return False
    return True

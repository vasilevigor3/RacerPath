"""Period bounds and uniqueness for special slots (race_of_day/week/month/year)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

SPECIAL_SLOT_VALUES = ("race_of_day", "race_of_week", "race_of_month", "race_of_year")


def get_period_bounds(special_value: str, dt: datetime) -> tuple[datetime, datetime]:
    """Return (period_start, period_end) in UTC for the day/week/month/year containing dt."""
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    if special_value == "race_of_day":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end = start + timedelta(days=1) - timedelta(microseconds=1)
        return start, end
    if special_value == "race_of_week":
        weekday = dt.isoweekday()
        monday_offset = timedelta(days=weekday - 1)
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc) - monday_offset
        end = start + timedelta(days=7) - timedelta(microseconds=1)
        return start, end
    if special_value == "race_of_month":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        if dt.month == 12:
            end = start.replace(month=12, day=31) + timedelta(
                hours=23, minutes=59, seconds=59, microseconds=999999
            )
        else:
            end = start.replace(month=dt.month + 1) - timedelta(microseconds=1)
        return start, end
    if special_value == "race_of_year":
        start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        end = start.replace(month=12, day=31) + timedelta(
            hours=23, minutes=59, seconds=59, microseconds=999999
        )
        return start, end
    return dt, dt


def special_slot_tier_conflict(
    session: "Session",
    special_value: str,
    start_time_utc: datetime | None,
    tier: str,
    exclude_event_id: str | None = None,
) -> bool:
    """
    True if another event already exists for this (special_event, period, tier).
    One unique event per tier per period (day/week/month/year).
    """
    if special_value not in SPECIAL_SLOT_VALUES or not start_time_utc or not tier:
        return False
    from app.models.classification import Classification
    from app.models.event import Event

    period_start, period_end = get_period_bounds(special_value, start_time_utc)
    q = (
        session.query(Event.id)
        .join(Classification, Event.id == Classification.event_id)
        .filter(
            Event.special_event == special_value,
            Event.start_time_utc >= period_start,
            Event.start_time_utc <= period_end,
            Classification.event_tier == tier,
        )
    )
    if exclude_event_id:
        q = q.filter(Event.id != exclude_event_id)
    return q.limit(1).first() is not None

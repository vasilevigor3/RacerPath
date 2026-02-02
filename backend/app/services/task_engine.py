"""
Task Engine: formalized task scopes (global, per_participation, rolling_window, periodic),
period_key, cooldown, and completion rules.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.models.participation import Participation
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition

from app.core.constants import (
    DEFAULT_ROLLING_WINDOW_SIZE,
    DEFAULT_ROLLING_WINDOW_UNIT,
)

PeriodKind = Literal["daily", "weekly", "monthly"]
ScopeKind = Literal["global", "per_participation", "rolling_window", "periodic"]


def build_period_key(dt: datetime | None, period: PeriodKind) -> str:
    """Build period_key: YYYY-MM-DD (daily), YYYY-Www (weekly ISO), YYYY-MM (monthly)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if period == "daily":
        return dt.strftime("%Y-%m-%d")
    if period == "weekly":
        iso = dt.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if period == "monthly":
        return dt.strftime("%Y-%m")
    raise ValueError(f"Unknown period: {period}")


def _task_by_code(session: Session, task_code: str) -> TaskDefinition | None:
    return session.query(TaskDefinition).filter(TaskDefinition.code == task_code).first()


def _latest_completion(
    session: Session, driver_id: str, task_id: str
) -> TaskCompletion | None:
    return (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.status == "completed",
        )
        .order_by(TaskCompletion.created_at.desc())
        .first()
    )


def _completion_time(completion: TaskCompletion) -> datetime:
    value = completion.completed_at or completion.created_at
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def can_complete_task(
    session: Session,
    driver_id: str,
    task_id: str,
    participation_id: str | None,
    now: datetime | None = None,
    period_key: str | None = None,
) -> tuple[bool, str]:
    """
    Check if the driver can complete the task (scope, uniqueness, cooldown).
    Returns (allowed, reason).
    """
    task = session.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task or not task.active:
        return False, "task_not_found_or_inactive"
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    scope = (task.scope or "per_participation").lower()

    if scope == "per_participation":
        if not participation_id:
            return False, "per_participation_requires_participation_id"
        existing = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.participation_id == participation_id,
                TaskCompletion.status == "completed",
            )
            .first()
        )
        if existing:
            return False, "already_completed_for_this_participation"
        return True, "ok"

    if scope == "global":
        if participation_id is not None:
            return False, "global_must_not_have_participation_id"
        existing = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.participation_id.is_(None),
                TaskCompletion.period_key.is_(None),
                TaskCompletion.status == "completed",
            )
            .first()
        )
        if existing:
            return False, "global_already_completed"
        if task.cooldown_days:
            latest = _latest_completion(session, driver_id, task_id)
            if latest:
                t = _completion_time(latest)
                if now - t < timedelta(days=task.cooldown_days):
                    return False, "cooldown_not_elapsed"
        return True, "ok"

    if scope == "periodic":
        if not task.period or task.period not in ("daily", "weekly", "monthly"):
            return False, "periodic_requires_period_on_definition"
        pk = period_key or build_period_key(now, task.period)
        existing = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.period_key == pk,
                TaskCompletion.status == "completed",
            )
            .first()
        )
        if existing:
            return False, "periodic_already_completed_for_period"
        if task.cooldown_days:
            latest = _latest_completion(session, driver_id, task_id)
            if latest:
                t = _completion_time(latest)
                if now - t < timedelta(days=task.cooldown_days):
                    return False, "cooldown_not_elapsed"
        return True, "ok"

    if scope == "rolling_window":
        # One-time "achievement" per driver/task when window condition is met; we don't check here,
        # we only allow one global-like completion (or we use achieved_by to store window source).
        # For now: allow creating one completion per driver/task for rolling_window (like global).
        existing = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.status == "completed",
            )
            .first()
        )
        if existing:
            return False, "rolling_window_already_achieved"
        return True, "ok"

    return False, "unknown_scope"


def complete_task(
    session: Session,
    driver_id: str,
    task_code: str,
    participation_id: str | None = None,
    period_key: str | None = None,
    achieved_by: list[str] | None = None,
    notes: str | None = None,
) -> TaskCompletion | None:
    """
    Create a task completion via Task Engine (by task_code).
    Validates scope/participation_id/period/cooldown; returns new TaskCompletion or None.
    """
    task = _task_by_code(session, task_code)
    if not task:
        return None
    now = datetime.now(timezone.utc)
    pk = period_key
    if (task.scope or "").lower() == "periodic" and task.period and task.period in ("daily", "weekly", "monthly") and not pk:
        pk = build_period_key(now, task.period)
    allowed, reason = can_complete_task(
        session, driver_id, task.id, participation_id, now=now, period_key=pk
    )
    if not allowed:
        return None
    completion = TaskCompletion(
        driver_id=driver_id,
        task_id=task.id,
        participation_id=participation_id,
        status="completed",
        notes=notes,
        completed_at=now,
        period_key=pk,
        achieved_by=achieved_by,
    )
    session.add(completion)
    session.flush()
    session.refresh(completion)
    return completion


def check_rolling_window_and_complete(
    session: Session,
    driver_id: str,
    task_id: str,
    participation_ids: list[str],
    window_size: int | None = None,
    window_unit: str | None = None,
) -> TaskCompletion | None:
    """
    If rolling_window condition is met (e.g. N participations in window), create one
    TaskCompletion with achieved_by = participation_ids. Uses task.window_size/window_unit
    or defaults.
    """
    task = session.query(TaskDefinition).filter(TaskDefinition.id == task_id).first()
    if not task or (task.scope or "").lower() != "rolling_window":
        return None
    size = task.window_size if task.window_size is not None else DEFAULT_ROLLING_WINDOW_SIZE
    unit = task.window_unit or DEFAULT_ROLLING_WINDOW_UNIT
    if window_size is not None:
        size = window_size
    if window_unit is not None:
        unit = window_unit
    if len(participation_ids) < size:
        return None
    # Already achieved?
    existing = (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.status == "completed",
        )
        .first()
    )
    if existing:
        return None
    completion = TaskCompletion(
        driver_id=driver_id,
        task_id=task.id,
        participation_id=None,
        status="completed",
        completed_at=datetime.now(timezone.utc),
        achieved_by=participation_ids[:size],
    )
    session.add(completion)
    session.flush()
    session.refresh(completion)
    return completion

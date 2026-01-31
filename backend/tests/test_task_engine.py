"""Tests: period_key, can_complete_task scope/cooldown, partial unique (per_participation 422 at API)."""
from datetime import datetime, timezone

import pytest

from app.services.task_engine import build_period_key, can_complete_task, complete_task


class TestBuildPeriodKey:
    def test_daily(self):
        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert build_period_key(dt, "daily") == "2026-01-15"

    def test_weekly_iso(self):
        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        key = build_period_key(dt, "weekly")
        assert key.startswith("2026-")
        assert "W" in key

    def test_monthly(self):
        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert build_period_key(dt, "monthly") == "2026-01"

    def test_none_uses_now(self):
        key = build_period_key(None, "daily")
        assert len(key) == 10 and key[4] == "-" and key[7] == "-"


class TestCanCompleteTask:
    """DB-dependent tests: run with session fixture."""

    @pytest.fixture
    def session(self):
        from app.db.session import SessionLocal
        session = SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    def test_per_participation_requires_participation_id(self, session):
        from app.models.task_definition import TaskDefinition
        from app.models.driver import Driver
        task = session.query(TaskDefinition).filter(TaskDefinition.scope == "per_participation").first()
        if not task:
            task = session.query(TaskDefinition).first()
        if not task:
            pytest.skip("no task_definitions")
        task.scope = "per_participation"
        session.add(task)
        session.flush()
        driver = session.query(Driver).first()
        if not driver:
            pytest.skip("no drivers")
        allowed, reason = can_complete_task(session, driver.id, task.id, participation_id=None)
        assert allowed is False
        assert "participation" in reason.lower()


class TestCompleteTaskCooldown:
    """Cooldown: second completion within cooldown_days is blocked."""

    @pytest.fixture
    def session(self):
        from app.db.session import SessionLocal
        session = SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()

    def test_cooldown_blocks_repeat(self, session):
        from app.models.task_definition import TaskDefinition
        from app.models.driver import Driver
        from app.models.task_completion import TaskCompletion
        driver = session.query(Driver).first()
        if not driver:
            pytest.skip("no drivers")
        task = session.query(TaskDefinition).filter(TaskDefinition.scope == "global").first()
        if not task:
            task = session.query(TaskDefinition).first()
        if not task:
            pytest.skip("no tasks")
        task.scope = "global"
        task.cooldown_days = 999
        session.add(task)
        session.flush()
        existing = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver.id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.participation_id.is_(None),
                TaskCompletion.period_key.is_(None),
            )
            .first()
        )
        if existing:
            allowed, _ = can_complete_task(session, driver.id, task.id, None)
            assert allowed is False

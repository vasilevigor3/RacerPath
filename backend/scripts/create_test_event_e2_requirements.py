"""Create a test task and event matching the given requirements:

  Min event tier: E2
  Min session duration: 60 min
  Max incidents: 2
  Max penalties: 1
  Cooldown between completions: 72 h
  Diversity window: 45 days
  Max completions from same event: 1
  Event diversity required: yes

Run from repo root:
  docker compose exec app python backend/scripts/create_test_event_e2_requirements.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.models.task_definition import TaskDefinition
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event

TASK_CODE = "GT_E2_60MIN"
TASK_NAME = "GT E2 · 60 min (max 2 incidents, 1 penalty)"
EVENT_TITLE = "Test E2 · 60 min"
EVENT_TIER = "E2"
DURATION_MINUTES = 60


def main() -> None:
    session = SessionLocal()
    try:
        task = session.query(TaskDefinition).filter(TaskDefinition.code == TASK_CODE).first()
        if not task:
            task = TaskDefinition(
                code=TASK_CODE,
                name=TASK_NAME,
                discipline="gt",
                description="E2 event, 60+ min, max 2 incidents, max 1 penalty. Cooldown 72h, diversity 45d, max 1 from same event.",
                requirements={
                    "min_event_tier": "E2",
                    "min_duration_minutes": 60,
                    "max_incidents": 2,
                    "max_penalties": 1,
                    "cooldown_hours": 72,
                    "diversity_window_days": 45,
                    "max_same_event_count": 1,
                    "require_event_diversity": True,
                },
                min_event_tier="E2",
                min_duration_minutes=60.0,
                max_incidents=2,
                max_penalties=1,
                cooldown_hours=72.0,
                diversity_window_days=45,
                max_same_event_count=1,
                require_event_diversity=True,
                repeatable=True,
                active=True,
                event_related=True,
                scope="per_participation",
            )
            session.add(task)
            session.flush()
            print(f"Created task: {task.code} (id={task.id})")
        else:
            print(f"Task already exists: {task.code} (id={task.id})")

        base_start = datetime.now(timezone.utc) + timedelta(hours=1)
        base_start = base_start.replace(minute=0, second=0, microsecond=0)
        event = Event(
            title=EVENT_TITLE,
            source="script",
            game="ACC",
            start_time_utc=base_start,
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="endurance",
            duration_minutes=DURATION_MINUTES,
            grid_size_expected=20,
            task_codes=[TASK_CODE],
        )
        session.add(event)
        session.flush()
        payload = build_event_payload(event, "gt")
        classification_data = classify_event(payload)
        classification_data["event_tier"] = EVENT_TIER
        classification_data["tier_label"] = TIER_LABELS.get(EVENT_TIER, EVENT_TIER)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)

        session.commit()
        print(f"Created event: {event.title} (id={event.id}, tier={EVENT_TIER}, duration={DURATION_MINUTES} min, task_codes={event.task_codes}, start={base_start.isoformat()})")
    finally:
        session.close()


if __name__ == "__main__":
    main()

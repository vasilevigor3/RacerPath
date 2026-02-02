"""Create a test task (GT_TEST_FLOW) and a test event with task_codes for flow testing.

Run from repo root:
  docker compose exec app python backend/scripts/create_test_task_and_event.py

Flow to test for vasilevigor3@gmail.com (E0 driver):
  1. Log in, open Events, find "Test Flow · E0 Sprint", register.
  2. Task GT_TEST_FLOW should appear In progress (assign_tasks_on_registration).
  3. Admin: mock-join then mock-finish (status=finished) for the participation.
  4. Backend must call evaluate_tasks on participation completed to mark task completed.
  5. If GT_TEST_FLOW is in a license level's required_task_codes, eligibility may allow receiving license.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.models.task_definition import TaskDefinition
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event

TASK_CODE = "GT_TEST_FLOW"
EVENT_TITLE = "Test Flow · E0 Sprint"


def main() -> None:
    session = SessionLocal()
    try:
        # 1. Create or get task
        task = session.query(TaskDefinition).filter(TaskDefinition.code == TASK_CODE).first()
        if not task:
            task = TaskDefinition(
                code=TASK_CODE,
                name="Test flow: clean sprint (E0)",
                discipline="gt",
                description="Finish a sprint race with zero incidents and penalties. For flow testing.",
                requirements={
                    "require_clean_finish": True,
                    "min_duration_minutes": 15,
                },
                min_event_tier="E0",
                active=True,
                event_related=True,
                scope="per_participation",
            )
            session.add(task)
            session.flush()
            print(f"Created task: {task.code} (id={task.id})")
        else:
            print(f"Task already exists: {task.code} (id={task.id})")

        # 2. Create event with task_codes and classification E0
        start_utc = datetime.now(timezone.utc) + timedelta(hours=1)
        start_utc = start_utc.replace(minute=0, second=0, microsecond=0)

        event = Event(
            title=EVENT_TITLE,
            source="script",
            game="ACC",
            start_time_utc=start_utc,
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="sprint",
            duration_minutes=30,
            grid_size_expected=20,
            task_codes=[TASK_CODE],
        )
        session.add(event)
        session.flush()

        tier = "E0"
        payload = build_event_payload(event, "gt")
        classification_data = classify_event(payload)
        classification_data["event_tier"] = tier
        classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)

        session.commit()
        print(
            f"Created event: {event.title} (id={event.id}, tier={tier}, "
            f"task_codes={event.task_codes}, start={start_utc.isoformat()})"
        )
        print("Next: register for this event as driver, then mock-join / mock-finish (admin or dev).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Create test tasks (GT_TEST_FLOW, GT_TEST_FLOW_2), two events (task 1 on event 1, task 2 on event 2), license requires both.

Run from repo root:
  docker compose exec app python backend/scripts/create_test_task_and_event.py

Flow to test:
  1. Register for Event 1 (race) -> GT_TEST_FLOW In progress. Finish participation (>=15 min, clean) -> task 1 completed.
  2. Register for Event 2 (race) -> GT_TEST_FLOW_2 In progress. Finish participation -> task 2 completed -> license GT_E0_TEST awarded.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.event import Event
from app.models.license_level import LicenseLevel
from app.models.task_definition import TaskDefinition
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event

TASK_CODES = ["GT_TEST_FLOW", "GT_TEST_FLOW_2"]
EVENT_TITLE = "Test Flow · E2 Sprint"
EVENT_TIER = "E2"  # Driver tier must be >= event tier to see events (E0..E5)
LICENSE_CODE = "GT_E0_TEST"
LICENSE_NAME = "GT E0 Test"
LICENSE_DESC = "Test license: complete both GT_TEST_FLOW and GT_TEST_FLOW_2 (Test Flow events) to become eligible."


TASK_SPECS = [
    ("GT_TEST_FLOW", "Test flow 1: clean sprint", "Finish a sprint race with zero incidents and penalties (task 1)."),
    ("GT_TEST_FLOW_2", "Test flow 2: clean sprint", "Finish a sprint race with zero incidents and penalties (task 2)."),
]


def main() -> None:
    session = SessionLocal()
    try:
        # 1. Create or get both tasks
        for code, name, desc in TASK_SPECS:
            task = session.query(TaskDefinition).filter(TaskDefinition.code == code).first()
            if not task:
                task = TaskDefinition(
                    code=code,
                    name=name,
                    discipline="gt",
                    description=desc,
                    requirements={"require_clean_finish": True, "min_duration_minutes": 15},
                    min_event_tier="E0",
                    min_duration_minutes=15.0,
                    require_clean_finish=True,
                    active=True,
                    event_related=True,
                    scope="per_participation",
                )
                session.add(task)
                session.flush()
                print(f"Created task: {task.code} (id={task.id})")
            else:
                print(f"Task already exists: {task.code} (id={task.id})")

        # 2. Create two events: event 1 = task 1 only, event 2 = task 2 only (2 races to complete both tasks)
        base_start = datetime.now(timezone.utc) + timedelta(hours=1)
        base_start = base_start.replace(minute=0, second=0, microsecond=0)
        created_events = []
        for i, hour_offset in enumerate([0, 1], start=1):
            start_utc = base_start + timedelta(hours=hour_offset)
            task_codes_for_event = [TASK_CODES[i - 1]]  # Event 1 -> [GT_TEST_FLOW], Event 2 -> [GT_TEST_FLOW_2]
            event = Event(
                title=f"{EVENT_TITLE} #{i}",
                source="script",
                game="ACC",
                start_time_utc=start_utc,
                session_type="race",
                schedule_type="weekly",
                event_type="circuit",
                format_type="sprint",
                duration_minutes=30,
                grid_size_expected=20,
                task_codes=task_codes_for_event,
            )
            session.add(event)
            session.flush()
            tier = EVENT_TIER
            payload = build_event_payload(event, "gt")
            classification_data = classify_event(payload)
            classification_data["event_tier"] = tier
            classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
            classification = Classification(event_id=event.id, **classification_data)
            session.add(classification)
            created_events.append((event, start_utc, task_codes_for_event))

        # 3. Create or get license level that requires both tasks
        level = session.query(LicenseLevel).filter(LicenseLevel.code == LICENSE_CODE).first()
        required = list(TASK_CODES)
        if not level:
            level = LicenseLevel(
                discipline="gt",
                code=LICENSE_CODE,
                name=LICENSE_NAME,
                description=LICENSE_DESC,
                min_crs=0.0,
                required_task_codes=required,
                active=True,
            )
            session.add(level)
            session.flush()
            print(f"Created license level: {level.code} (id={level.id}, required_task_codes={level.required_task_codes})")
        else:
            level.required_task_codes = required
            session.flush()
            print(f"Updated license level: {level.code}, required_task_codes={level.required_task_codes}")

        session.commit()
        for ev, st, tc in created_events:
            print(f"Created event: {ev.title} (id={ev.id}, task_codes={tc}, start={st.isoformat()})")
        print("Test flow: finish Event 1 (race) -> task 1 completed; finish Event 2 (race) -> task 2 completed -> license awarded.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

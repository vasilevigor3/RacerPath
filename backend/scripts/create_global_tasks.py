"""Create two non-event tasks (event_related=False, scope=global) for testing.

Run from repo root:
  docker compose exec app python backend/scripts/create_global_tasks.py

Tasks created:
  - GT_GLOBAL_PROFILE   — "Complete profile" (e.g. fill name, avatar)
  - GT_GLOBAL_SIM_GAMES — "Add sim games" (e.g. select at least one sim in Profile)

How to check readiness / mark completed:
  1. List completions: GET /api/tasks/completions?driver_id=<driver_id>
     — pending/in_progress tasks won't have a completed row; completed tasks will.
  2. Mark complete when your app decides "ready": POST /api/dev/tasks/complete
     Body: { "driver_id": "<driver_id>", "task_code": "GT_GLOBAL_PROFILE" }
     (or "GT_GLOBAL_SIM_GAMES"). No participation_id for global tasks.
  3. From CLI: curl -X POST .../api/dev/tasks/complete -H "Authorization: Bearer <token>" \\
       -H "Content-Type: application/json" -d '{"driver_id":"...","task_code":"GT_GLOBAL_PROFILE"}'
"""
from __future__ import annotations

from app.db.session import SessionLocal
from app.models.task_definition import TaskDefinition

GLOBAL_TASK_SPECS = [
    (
        "GT_GLOBAL_PROFILE",
        "Complete profile",
        "Fill in your driver profile (name, avatar, etc.). Not tied to any event.",
    ),
    (
        "GT_GLOBAL_SIM_GAMES",
        "Add sim games",
        "Select at least one sim in Profile → Sim games. Not tied to any event.",
    ),
]


def main() -> None:
    session = SessionLocal()
    try:
        for code, name, desc in GLOBAL_TASK_SPECS:
            task = session.query(TaskDefinition).filter(TaskDefinition.code == code).first()
            if not task:
                task = TaskDefinition(
                    code=code,
                    name=name,
                    discipline="gt",
                    description=desc,
                    requirements={},
                    active=True,
                    event_related=False,
                    scope="global",
                )
                session.add(task)
                session.flush()
                print(f"Created global task: {task.code} (id={task.id}, scope={task.scope})")
            else:
                print(f"Global task already exists: {task.code} (id={task.id})")
        session.commit()
        print("\nTo mark complete: POST /api/dev/tasks/complete with driver_id and task_code (no participation_id).")
    finally:
        session.close()


if __name__ == "__main__":
    main()

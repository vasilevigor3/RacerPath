"""Inspect driver participations and task completions; diagnose why task stayed in progress.

Run from repo root:
  docker compose exec app python backend/scripts/inspect_driver_tasks.py <user_id_or_driver_id>

Prints: driver, participations (state, status, started_at, finished_at, incidents, penalties),
  task completions, and for each completed participation whether GT_TEST_FLOW would meet requirements.
"""
from __future__ import annotations

import sys

from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition
from app.models.user import User
from app.services.tasks import (
    _latest_classification,
    _meets_requirements,
    _participation_duration_minutes,
    assign_participation_id_for_completed_participation,
    evaluate_tasks,
)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: inspect_driver_tasks.py <user_id_or_driver_id>", file=sys.stderr)
        sys.exit(1)
    uid = sys.argv[1].strip()
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        driver = session.query(Driver).filter(Driver.id == uid).first()
        if not driver and user:
            driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            print(f"No driver found for id={uid}")
            sys.exit(1)
        driver_id = driver.id
        user = session.query(User).filter(User.id == driver.user_id).first() if driver.user_id else None
        print(f"Driver: id={driver_id}, user_id={driver.user_id}, email={user.email if user else '—'}")
        print()

        participations = (
            session.query(Participation)
            .options(
                selectinload(Participation.incidents).selectinload(Incident.penalties),
            )
            .filter(Participation.driver_id == driver_id)
            .order_by(Participation.created_at.desc())
            .all()
        )
        print(f"Participations: {len(participations)}")
        for p in participations:
            state = getattr(p.participation_state, "value", str(p.participation_state))
            status = getattr(p.status, "value", str(p.status))
            dur = _participation_duration_minutes(p)
            print(
                f"  id={p.id} event_id={p.event_id} state={state} status={status} "
                f"started_at={p.started_at} finished_at={p.finished_at} "
                f"incidents={p.incidents_count} penalties={p.penalties_count} duration_min={dur}"
            )
        print()

        completions = (
            session.query(TaskCompletion, TaskDefinition)
            .join(TaskDefinition, TaskCompletion.task_id == TaskDefinition.id)
            .filter(TaskCompletion.driver_id == driver_id)
            .all()
        )
        print(f"Task completions: {len(completions)}")
        for tc, td in completions:
            print(f"  task={td.code} status={tc.status} participation_id={tc.participation_id} completed_at={tc.completed_at}")
        print()

        task_gt = session.query(TaskDefinition).filter(TaskDefinition.code == "GT_TEST_FLOW").first()
        if not task_gt:
            print("GT_TEST_FLOW task not found.")
        else:
            print("GT_TEST_FLOW requirements:", task_gt.requirements)
            print("  Need: participation.status='finished', require_clean_finish => incidents=0 penalties=0, min_duration_minutes=15")
            print()

        for p in participations:
            if getattr(p.participation_state, "value", str(p.participation_state)) != "completed":
                continue
            event = session.query(Event).filter(Event.id == p.event_id).first()
            classification = _latest_classification(session, p.event_id) if event else None
            if not event:
                print(f"Participation {p.id}: event not found, skip.")
                continue
            if not task_gt:
                continue
            meets = _meets_requirements(task_gt, p, event, classification)
            status_val = getattr(p.status, "value", str(p.status))
            dur = _participation_duration_minutes(p)
            print(f"Participation {p.id} (event {event.title}): _meets_requirements(GT_TEST_FLOW) = {meets}")
            print(
                f"  status={status_val} (must be 'finished') incidents={p.incidents_count} penalties={p.penalties_count} "
                f"duration_min={dur} event.duration_minutes={event.duration_minutes}"
            )
            if not meets:
                if status_val != "finished":
                    print("  => Set participation.status = 'finished' in admin PATCH.")
                if p.incidents_count > 0 or p.penalties_count > 0:
                    print("  => require_clean_finish: incidents and penalties must be 0.")
                if dur is not None and dur < 15:
                    print("  => min_duration_minutes=15: participation duration or event duration must be >= 15.")
            else:
                print("  => Would pass. Re-running evaluate_tasks for this participation.")
                before = session.query(TaskCompletion).filter(
                    TaskCompletion.driver_id == driver_id,
                    TaskCompletion.task_id == task_gt.id,
                    TaskCompletion.status == "pending",
                ).count()
                evaluate_tasks(session, driver_id, p.id)
                assign_participation_id_for_completed_participation(session, driver_id, p.id)
                session.commit()
                after = session.query(TaskCompletion).filter(
                    TaskCompletion.driver_id == driver_id,
                    TaskCompletion.task_id == task_gt.id,
                    TaskCompletion.status == "completed",
                ).count()
                print(f"  evaluate_tasks done. Pending before: {before}, completed after: {after}")
        print("Done.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

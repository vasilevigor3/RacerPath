from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.task_completion import TaskCompletionRepository
from app.repositories.task_definition import TaskDefinitionRepository
from app.schemas.task import (
    TaskCompletionCreate,
    TaskCompletionRead,
    TaskDefinitionCreate,
    TaskDefinitionRead,
)
from app.services.tasks import evaluate_tasks
from app.services.task_templates import list_templates, seed_templates
from app.services.auth import require_roles, require_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/definitions", response_model=TaskDefinitionRead)
def create_task_definition(
    payload: TaskDefinitionCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    task = TaskDefinition(**payload.model_dump())
    TaskDefinitionRepository(session).add(task)
    session.commit()
    session.refresh(task)
    return task


@router.get("/definitions", response_model=List[TaskDefinitionRead])
def list_task_definitions(
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    return TaskDefinitionRepository(session).list_all()


@router.get("/definitions/{task_id}", response_model=TaskDefinitionRead)
def get_task_definition(
    task_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    task = TaskDefinitionRepository(session).get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/completions", response_model=TaskCompletionRead)
def create_task_completion(
    payload: TaskCompletionCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(payload.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")

    task = TaskDefinitionRepository(session).get_by_id(payload.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Driver can take tasks only at their tier or below (admin can bypass)
    if user.role not in {"admin"} and payload.status == "pending":
        _TIER_ORDER = ("E0", "E1", "E2", "E3", "E4", "E5")
        driver_tier = (driver.tier or "E0").strip()
        task_min_tier = (task.min_event_tier or "E0").strip()
        driver_idx = _TIER_ORDER.index(driver_tier) if driver_tier in _TIER_ORDER else 0
        task_idx = _TIER_ORDER.index(task_min_tier) if task_min_tier in _TIER_ORDER else 0
        if driver_idx < task_idx:
            raise HTTPException(
                status_code=400,
                detail=f"Task requires tier {task_min_tier} or higher; your tier is {driver_tier}. You can only take tasks at your tier or below.",
            )
        # Event-related tasks can only be taken by registering for an event (with participation_id)
        if getattr(task, "event_related", True) and not payload.participation_id:
            raise HTTPException(
                status_code=400,
                detail="This task is event-related. You can only take it by registering for an event that has this task.",
            )

    if payload.participation_id:
        participation = ParticipationRepository(session).get_by_id(payload.participation_id)
        if not participation:
            raise HTTPException(status_code=404, detail="Participation not found")
        if participation.driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Participation mismatch")

    task_completion_repo = TaskCompletionRepository(session)
    # Global scope: at most one completion per (driver_id, task_id). Update existing instead of duplicate.
    if payload.participation_id is None and payload.period_key is None:
        existing = task_completion_repo.find_global_completion(payload.driver_id, payload.task_id)
        if existing:
            existing.status = payload.status
            if payload.status == "completed":
                existing.completed_at = payload.completed_at or existing.completed_at or datetime.now(timezone.utc)
            session.commit()
            session.refresh(existing)
            return existing

    completion = TaskCompletion(**payload.model_dump())
    task_completion_repo.add(completion)
    session.commit()
    session.refresh(completion)
    return completion


@router.get("/completions", response_model=List[TaskCompletionRead])
def list_task_completions(
    driver_id: str | None = None,
    task_id: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_user_id(user.id)
        if not driver:
            return []
        if driver_id and driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
        driver_id = driver.id
    if not driver_id:
        return []
    return TaskCompletionRepository(session).list_by_driver(driver_id, task_id)


@router.post("/evaluate", response_model=List[TaskCompletionRead])
def evaluate_task_completion(
    driver_id: str,
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if participation.driver_id != driver.id:
        raise HTTPException(status_code=403, detail="Participation mismatch")
    completions = evaluate_tasks(session, driver_id, participation_id)
    return completions


@router.get("/templates")
def get_task_templates(_: User = Depends(require_user())):
    return list_templates()


@router.post("/templates/seed", response_model=List[TaskDefinitionRead])
def seed_task_templates(
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    return seed_templates(session)

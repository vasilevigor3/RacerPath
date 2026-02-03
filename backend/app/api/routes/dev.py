"""Dev/admin endpoints: task complete by code, driver recompute CRS+recommendations, mock session/finish."""
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.participation import ParticipationState, ParticipationStatus
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.task_definition import TaskDefinitionRepository
from app.schemas.crs import CRSHistoryRead
from app.schemas.participation import ParticipationRead
from app.schemas.recommendation import RecommendationRead
from app.schemas.task import TaskCompletionRead, TaskCompleteRequest
from app.services.auth import require_roles, require_user
from app.services.crs import recompute_crs
from app.services.recommendations import recompute_recommendations
from app.events.participation_events import dispatch_participation_completed
from app.services.task_engine import can_complete_task, complete_task

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/tasks/complete", response_model=TaskCompletionRead)
def dev_complete_task(
    payload: TaskCompleteRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Complete a task by task_code (Task Engine). Admin or own driver."""
    driver = DriverRepository(session).get_by_id(payload.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in ("admin",) and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    task = TaskDefinitionRepository(session).get_by_code(payload.task_code)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    allowed, reason = can_complete_task(
        session, payload.driver_id, task.id, payload.participation_id, period_key=payload.period_key
    )
    if not allowed:
        raise HTTPException(status_code=422, detail=reason)
    completion = complete_task(
        session,
        driver_id=payload.driver_id,
        task_code=payload.task_code,
        participation_id=payload.participation_id,
        period_key=payload.period_key,
        achieved_by=payload.achieved_by,
    )
    if not completion:
        raise HTTPException(status_code=422, detail="Cannot complete task")
    session.commit()
    session.refresh(completion)
    return completion


@router.post("/drivers/{driver_id}/recompute")
def dev_recompute_driver(
    driver_id: str,
    trigger_participation_id: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
) -> dict[str, Any]:
    """Recompute CRS and recommendations for a driver (with snapshot: inputs_hash, algo_version, computed_from)."""
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in ("admin",) and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    disciplines = [driver.primary_discipline] if driver.primary_discipline else []
    if not disciplines:
        return {"crs": [], "recommendations": []}
    crs_list: List[CRSHistoryRead] = []
    rec_list: List[RecommendationRead] = []
    for disc in disciplines:
        try:
            crs = recompute_crs(session, driver_id, disc, trigger_participation_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        crs_list.append(crs)
        rec, special_events = recompute_recommendations(session, driver_id, disc, trigger_participation_id)
        rec_list.append(RecommendationRead.model_validate(rec).model_copy(update={"special_events": special_events}))
    return {"crs": crs_list, "recommendations": rec_list}


# ---- Mock external integration: driver joined session / finished race ----

@router.post("/participations/{participation_id}/mock-join", response_model=ParticipationRead)
def mock_participation_join(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_roles("admin")),
):
    """Mock: simulate external integration — driver joined server/session. Sets participation_state=started, started_at=now."""
    part = ParticipationRepository(session).get_by_id(participation_id)
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    if part.participation_state != ParticipationState.registered:
        raise HTTPException(
            status_code=400,
            detail=f"Participation state must be 'registered' to mock join (current: {part.participation_state}).",
        )
    now = datetime.now(timezone.utc)
    part.participation_state = ParticipationState.started
    part.started_at = now
    session.commit()
    session.refresh(part)
    return part


@router.post("/participations/{participation_id}/mock-finish", response_model=ParticipationRead)
def mock_participation_finish(
    participation_id: str,
    status: str = "finished",
    session: Session = Depends(get_session),
    user: User = Depends(require_roles("admin")),
):
    """Mock: simulate external integration — driver finished race. Sets participation_state=completed, finished_at=now, status (finished/dnf/dsq)."""
    part = ParticipationRepository(session).get_by_id(participation_id)
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    if part.participation_state != ParticipationState.started:
        raise HTTPException(
            status_code=400,
            detail=f"Participation state must be 'started' to mock finish (current: {part.participation_state}).",
        )
    if part.started_at is None:
        raise HTTPException(status_code=400, detail="started_at must be set before mock finish.")
    valid_statuses = {"finished", "dnf", "dsq"}
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {valid_statuses}.",
        )
    now = datetime.now(timezone.utc)
    if now < part.started_at:
        raise HTTPException(status_code=400, detail="finished_at cannot be before started_at.")
    part.participation_state = ParticipationState.completed
    part.finished_at = now
    part.status = ParticipationStatus(status)
    session.commit()
    session.refresh(part)
    dispatch_participation_completed(session, part.driver_id, part.id)
    return part


@router.post("/mock-race/tick")
def dev_mock_race_tick(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    """Run one tick of the mock race service. Updates participations for events in progress."""
    from app.core.settings import settings
    from app.db.session import SessionLocal
    from app.services.mock_race_service import tick_mock_races
    interval = max(1, getattr(settings, "mock_race_interval_seconds", 60))
    result = tick_mock_races(session, interval_seconds=interval)
    session.commit()
    for driver_id, participation_id in result.get("finished_driver_participation_pairs") or []:
        disp_session = SessionLocal()
        try:
            dispatch_participation_completed(disp_session, driver_id, participation_id)
            disp_session.commit()
        finally:
            disp_session.close()
    return {
        "events_processed": result["events_processed"],
        "participations_updated": result["participations_updated"],
        "participations_finished": result["participations_finished"],
    }


@router.post("/mock-incident/tick")
def dev_mock_incident_tick(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    """Run one tick of the mock incident service. Adds incidents for participations with state started."""
    from app.core.settings import settings
    from app.services.crs import recompute_crs
    from app.services.mock_incident_service import tick_mock_incidents
    result = tick_mock_incidents(
        session,
        probability=getattr(settings, "mock_incident_probability", 0.15),
    )
    for driver_id, discipline in result.get("driver_discipline_pairs") or []:
        try:
            recompute_crs(session, driver_id, discipline, trigger_participation_id=None)
        except Exception:
            pass
    session.commit()
    return {
        "incidents_created": result["incidents_created"],
        "driver_discipline_pairs": result["driver_discipline_pairs"],
    }


@router.post("/mock-event/tick")
def dev_mock_event_tick(
    session: Session = Depends(get_session),
    _: User = Depends(require_roles("admin")),
) -> dict[str, Any]:
    """Create one random E2 ACC event (start in 5 min)."""
    from app.core.settings import settings
    from app.services.mock_event_service import tick_mock_events
    minutes_until_start = max(0, getattr(settings, "mock_event_minutes_until_start", 5))
    result = tick_mock_events(
        session,
        tier="E2",
        game="ACC",
        minutes_until_start=minutes_until_start,
        count=1,
    )
    session.commit()
    return {
        "events_created": result["events_created"],
    }

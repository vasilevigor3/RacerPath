from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState, ParticipationStatus
from app.models.penalty import Penalty
from app.models.user import User
from app.repositories.classification import ClassificationRepository
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.penalty import PenaltyRepository
from app.repositories.task_completion import TaskCompletionRepository
from app.schemas.incident import IncidentCreate, IncidentRead
from app.schemas.participation import (
    ActiveParticipationRead,
    ParticipationCreate,
    ParticipationRead,
    ParticipationWithEventRead,
    ParticipationWithdrawUpdate,
)
from app.penalties.scores import get_score_for_penalty_type
from app.schemas.penalty import PenaltyCreate, PenaltyRead, PenaltyTypeEnum
from app.services.tasks import assign_tasks_on_registration, evaluate_tasks
from app.services.crs import recompute_crs
from app.services.auth import require_user
from app.utils.rig_compat import driver_rig_satisfies_event

router = APIRouter(prefix="/participations", tags=["participations"])


@router.post("", response_model=ParticipationRead)
def create_participation(
    payload: ParticipationCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(payload.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    event = EventRepository(session).get_by_id(payload.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    start_utc = event.start_time_utc
    if start_utc is not None and start_utc.tzinfo is None:
        start_utc = start_utc.replace(tzinfo=timezone.utc)
    if start_utc is not None and start_utc <= now_utc:
        raise HTTPException(
            status_code=400,
            detail="Cannot register for a past event. Registration is closed.",
        )
    classification = ClassificationRepository(session).get_latest_for_event(payload.event_id)
    if not classification:
        raise HTTPException(
            status_code=400,
            detail="Event has no classification; participation requires the event to be classified first.",
        )
    if not driver_rig_satisfies_event(driver.rig_options, event.rig_options):
        raise HTTPException(
            status_code=400,
            detail="Your rig does not meet the event's required rig (wheel/pedals). You cannot register.",
        )
    MAX_WITHDRAWALS = 3
    part_repo = ParticipationRepository(session)
    existing = part_repo.get_by_driver_and_event(payload.driver_id, payload.event_id)
    if existing:
        if existing.participation_state == ParticipationState.withdrawn:
            if existing.withdraw_count >= MAX_WITHDRAWALS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Max withdrawals reached ({MAX_WITHDRAWALS}). You cannot register again for this event.",
                )
            existing.participation_state = ParticipationState.registered
            existing.status = ParticipationStatus.dns
            session.commit()
            session.refresh(existing)
            assign_tasks_on_registration(session, driver.id, existing.id)
            return existing
        raise HTTPException(status_code=400, detail="Participation already exists")

    participation = Participation(**payload.model_dump())
    participation.classification_id = classification.id
    part_repo.add(participation)
    session.commit()
    session.refresh(participation)
    assign_tasks_on_registration(session, driver.id, participation.id)
    try:
        recompute_crs(
            session,
            driver.id,
            participation.discipline.value if hasattr(participation.discipline, "value") else participation.discipline,
            trigger_participation_id=participation.id,
        )
    except ValueError:
        pass
    return participation


@router.get("", response_model=List[ParticipationWithEventRead])
def list_participations(
    driver_id: str | None = None,
    event_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    part_repo = ParticipationRepository(session)
    driver_repo = DriverRepository(session)
    event_repo = EventRepository(session)
    if user.role not in {"admin"}:
        if driver_id:
            driver = driver_repo.get_by_id(driver_id)
            if not driver or driver.user_id != user.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
        else:
            driver = driver_repo.get_by_user_id(user.id)
            if not driver:
                return []
            driver_id = driver.id
    limit = max(1, min(limit, 200))
    participations = part_repo.list_filtered(
        driver_id=driver_id, event_id=event_id, offset=offset, limit=limit
    )
    if not participations:
        return []
    result = []
    for p in participations:
        event = event_repo.get_by_id(p.event_id)
        result.append(
            ParticipationWithEventRead(
                **ParticipationRead.model_validate(p).model_dump(),
                event_title=event.title if event else "",
                event_start_time_utc=event.start_time_utc if event else None,
            )
        )
    return result


@router.get("/active", response_model=ActiveParticipationRead | None)
def get_active_participation(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Return the driver's current race (participation_state=started, finished_at is null), if any."""
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        return None
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    participation = ParticipationRepository(session).get_active_by_driver(driver_id)
    if not participation:
        return None
    event = EventRepository(session).get_by_id(participation.event_id)
    event_title = event.title if event else None
    return ActiveParticipationRead(
        **ParticipationRead.model_validate(participation).model_dump(),
        event_title=event_title,
    )


@router.get("/{participation_id}", response_model=ParticipationRead)
def get_participation(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return participation


@router.patch("/{participation_id}", response_model=ParticipationRead)
def update_participation_withdraw(
    participation_id: str,
    payload: ParticipationWithdrawUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Driver withdraws from event: set participation_state to withdrawn (only when currently registered)."""
    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    if participation.participation_state != ParticipationState.registered:
        raise HTTPException(
            status_code=400,
            detail="Can only withdraw when participation state is registered.",
        )
    participation.participation_state = ParticipationState.withdrawn
    participation.withdraw_count = (participation.withdraw_count or 0) + 1
    TaskCompletionRepository(session).delete_by_participation_and_status(
        participation.id, ["pending", "in_progress"]
    )
    session.commit()
    session.refresh(participation)
    return participation


@router.post("/{participation_id}/incidents", response_model=IncidentRead)
def create_incident(
    participation_id: str,
    payload: IncidentCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if participation_id != payload.participation_id:
        raise HTTPException(status_code=400, detail="Participation mismatch")

    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")

    incident = Incident(**payload.model_dump())
    IncidentRepository(session).add(incident)
    participation.incidents_count += 1
    session.commit()
    session.refresh(incident)
    return incident


@router.get("/{participation_id}/incidents", response_model=List[IncidentRead])
def list_incidents(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return IncidentRepository(session).list_by_participation_id(participation_id)


@router.post("/{participation_id}/penalties", response_model=PenaltyRead)
def create_penalty(
    participation_id: str,
    payload: PenaltyCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if participation_id != payload.participation_id:
        raise HTTPException(status_code=400, detail="Participation mismatch")

    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")

    score = payload.score if payload.score is not None else get_score_for_penalty_type(payload.penalty_type.value)
    penalty = Penalty(
        participation_id=payload.participation_id,
        penalty_type=payload.penalty_type.value,
        score=score,
        time_seconds=payload.time_seconds,
        lap=payload.lap,
        description=payload.description,
    )
    PenaltyRepository(session).add(penalty)
    participation.penalties_count += 1
    if payload.penalty_type == PenaltyTypeEnum.dsq:
        participation.status = ParticipationStatus.dsq
    session.commit()
    session.refresh(penalty)
    return penalty


@router.get("/{participation_id}/penalties", response_model=List[PenaltyRead])
def list_penalties(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    participation = ParticipationRepository(session).get_by_id(participation_id)
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return PenaltyRepository(session).list_by_participation_id(participation_id)

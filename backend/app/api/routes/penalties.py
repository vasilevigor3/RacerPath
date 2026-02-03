"""Penalties API: list/count by driver, get by id."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.penalty import PenaltyRepository
from app.schemas.penalty import PenaltyRead, PenaltyWithEventRead
from app.services.auth import require_user

router = APIRouter(prefix="/penalties", tags=["penalties"])


@router.get("/count")
def get_penalties_count(
    driver_id: str | None = None,
    participation_id: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Return total count of penalties for the current driver (or filtered)."""
    if user.role not in {"admin"}:
        if driver_id:
            driver = DriverRepository(session).get_by_id(driver_id)
            if not driver or driver.user_id != user.id:
                return {"total": 0}
        else:
            driver = DriverRepository(session).get_by_user_id(user.id)
            if not driver:
                return {"total": 0}
            driver_id = driver.id
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return {"total": 0}
            if not driver or participation.driver_id != driver.id:
                return {"total": 0}
    total = PenaltyRepository(session).count_filtered(
        driver_id=driver_id, participation_id=participation_id
    )
    return {"total": total}


@router.get("", response_model=List[PenaltyWithEventRead])
def list_all_penalties(
    driver_id: str | None = None,
    participation_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if user.role not in {"admin"}:
        if driver_id:
            driver = DriverRepository(session).get_by_id(driver_id)
            if not driver or driver.user_id != user.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
        else:
            driver = DriverRepository(session).get_by_user_id(user.id)
            if not driver:
                return []
            driver_id = driver.id
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return []
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 200))
    penalties = PenaltyRepository(session).list_filtered(
        driver_id=driver_id, participation_id=participation_id, offset=offset, limit=limit
    )
    if not penalties:
        return []
    part_repo = ParticipationRepository(session)
    event_repo = EventRepository(session)
    result = []
    for p in penalties:
        inc = getattr(p, "incident", None)  # loaded via selectinload
        part = part_repo.get_by_id(inc.participation_id) if inc else None
        event = event_repo.get_by_id(part.event_id) if part else None
        result.append(
            PenaltyWithEventRead(
                id=p.id,
                participation_id=inc.participation_id if inc else None,
                penalty_type=p.penalty_type,
                score=p.score,
                time_seconds=p.time_seconds,
                lap=p.lap,
                description=p.description,
                created_at=p.created_at,
                event_id=part.event_id if part else None,
                event_title=event.title if event else "",
                event_start_time_utc=event.start_time_utc if event else None,
            )
        )
    return result


@router.get("/{penalty_id}", response_model=PenaltyRead)
def get_penalty(
    penalty_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    penalty = PenaltyRepository(session).get_by_id(penalty_id, load_incident=True)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")
    if user.role not in {"admin"}:
        incident = IncidentRepository(session).get_by_id(penalty.incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        participation = ParticipationRepository(session).get_by_id(incident.participation_id)
        driver = DriverRepository(session).get_by_id(participation.driver_id) if participation else None
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return penalty

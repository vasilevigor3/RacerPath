"""Penalties API: list/count by driver, get by id."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.penalty import PenaltyRepository
from app.schemas.penalty import PenaltyRead
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
        driver = DriverRepository(session).get_by_user_id(user.id)
        if not driver:
            return {"total": 0}
        if driver_id and driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
        driver_id = driver.id
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return {"total": 0}
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    total = PenaltyRepository(session).count_filtered(
        driver_id=driver_id, participation_id=participation_id
    )
    return {"total": total}


@router.get("", response_model=List[PenaltyRead])
def list_all_penalties(
    driver_id: str | None = None,
    participation_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
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
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return []
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 200))
    return PenaltyRepository(session).list_filtered(
        driver_id=driver_id, participation_id=participation_id, offset=offset, limit=limit
    )


@router.get("/{penalty_id}", response_model=PenaltyRead)
def get_penalty(
    penalty_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    penalty = PenaltyRepository(session).get_by_id(penalty_id)
    if not penalty:
        raise HTTPException(status_code=404, detail="Penalty not found")
    if user.role not in {"admin"}:
        participation = ParticipationRepository(session).get_by_id(penalty.participation_id)
        driver = DriverRepository(session).get_by_id(participation.driver_id) if participation else None
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return penalty

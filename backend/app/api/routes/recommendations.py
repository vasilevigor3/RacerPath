from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.user import User
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationRead
from app.services.recommendations import compute_recommendation
from app.services.auth import require_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/compute", response_model=RecommendationRead)
def compute(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    rec, special_events = compute_recommendation(session, driver_id, discipline)
    return RecommendationRead.model_validate(rec).model_copy(update={"special_events": special_events})


@router.get("", response_model=List[RecommendationRead])
def list_recommendations(
    driver_id: str,
    discipline: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    query = session.query(Recommendation).filter(Recommendation.driver_id == driver_id)
    if discipline:
        query = query.filter(Recommendation.discipline == discipline)
    return query.order_by(Recommendation.created_at.desc()).all()


@router.get("/latest", response_model=Optional[RecommendationRead])
def latest(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    # Always recompute so "Race next" uses same driver.tier filter as /events/upcoming
    rec, special_events = compute_recommendation(session, driver_id, discipline)
    return RecommendationRead.model_validate(rec).model_copy(update={"special_events": special_events})
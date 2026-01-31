"""Dev/admin endpoints: task complete by code, driver recompute CRS+recommendations."""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.task_definition import TaskDefinition
from app.models.user import User
from app.schemas.crs import CRSHistoryRead
from app.schemas.recommendation import RecommendationRead
from app.schemas.task import TaskCompletionRead, TaskCompleteRequest
from app.services.auth import require_roles, require_user
from app.services.crs import recompute_crs
from app.services.recommendations import recompute_recommendations
from app.services.task_engine import can_complete_task, complete_task

router = APIRouter(prefix="/dev", tags=["dev"])


@router.post("/tasks/complete", response_model=TaskCompletionRead)
def dev_complete_task(
    payload: TaskCompleteRequest,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Complete a task by task_code (Task Engine). Admin or own driver."""
    driver = session.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in ("admin",) and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    task = session.query(TaskDefinition).filter(TaskDefinition.code == payload.task_code).first()
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
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
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
        crs = recompute_crs(session, driver_id, disc, trigger_participation_id)
        crs_list.append(crs)
        rec = recompute_recommendations(session, driver_id, disc, trigger_participation_id)
        rec_list.append(rec)
    return {"crs": crs_list, "recommendations": rec_list}

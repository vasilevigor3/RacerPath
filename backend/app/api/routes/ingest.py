import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.repositories.raw_event import RawEventRepository
from app.schemas.raw_event import RawEventIngest, RawEventRead
from app.services.ingestion import ingest_payload
from app.services.auth import require_roles, require_user
from app.core.settings import settings

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.get("/sources", response_model=List[str])
def list_sources(_: User = Depends(require_user())):
    return ["wss", "gridfinder", "iracing", "acc_league", "lfm", "sro_esports", "other"]


@router.post("/raw-events", response_model=RawEventRead)
def ingest_raw_event(
    payload: RawEventIngest,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    payload_bytes = json.dumps(payload.payload).encode("utf-8")
    if len(payload_bytes) > settings.ingest_payload_max_bytes:
        raise HTTPException(status_code=413, detail="Payload too large")
    return ingest_payload(
        session,
        payload.source,
        payload.payload,
        payload.create_event,
        payload.source_event_id,
    )


@router.get("/raw-events", response_model=List[RawEventRead])
def list_raw_events(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    limit = max(1, min(limit, 200))
    return RawEventRepository(session).list_paginated(offset=offset, limit=limit)


@router.get("/raw-events/{raw_event_id}", response_model=RawEventRead)
def get_raw_event(
    raw_event_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    raw_event = RawEventRepository(session).get_by_id(raw_event_id)
    if not raw_event:
        raise HTTPException(status_code=404, detail="Raw event not found")
    return raw_event

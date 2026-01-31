from __future__ import annotations

from urllib.error import HTTPError, URLError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_session
from app.services.connectors import extract_events, fetch_json
from app.services.ingestion import ingest_payload
from app.services.auth import require_roles, require_user
from app.models.user import User

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _sync_source(session: Session, source: str, url: str | None, api_key: str | None) -> dict:
    if not url:
        raise HTTPException(status_code=400, detail=f"{source} events URL is not configured")
    try:
        payload = fetch_json(url, api_key)
        events = extract_events(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except HTTPError as exc:
        raise HTTPException(status_code=exc.code or 502, detail=f"{source} fetch failed")
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"{source} fetch failed: {exc.reason}")
    except Exception:
        raise HTTPException(status_code=502, detail=f"{source} fetch failed")

    classified = 0
    failed = 0

    for event_payload in events:
        try:
            raw_event = ingest_payload(session, source, event_payload, create_event=True)
            if raw_event.status == "classified":
                classified += 1
            elif raw_event.status == "failed":
                failed += 1
        except Exception:
            session.rollback()
            failed += 1

    return {"source": source, "total": len(events), "classified": classified, "failed": failed}


@router.get("/status")
def connector_status(_: User = Depends(require_user())):
    return {
        "wss": {"configured": bool(settings.wss_events_url)},
        "gridfinder": {"configured": bool(settings.gridfinder_events_url)},
    }


@router.post("/wss/sync")
def sync_wss(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return _sync_source(session, "wss", settings.wss_events_url, settings.wss_api_key)


@router.post("/gridfinder/sync")
def sync_gridfinder(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return _sync_source(
        session,
        "gridfinder",
        settings.gridfinder_events_url,
        settings.gridfinder_api_key,
    )

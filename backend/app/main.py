from pathlib import Path
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
# TODO remove:
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.logging import configure_logging
from app.db.redis import create_redis_client
from app.db.session import SessionLocal, init_db
from app.services.auth import get_user_by_key, log_audit
from app.services.mock_event_runner import start_mock_event_background
from app.services.mock_race_runner import start_mock_race_background

app = FastAPI(title="RacerPath", version="0.1.0")
app.include_router(api_router)

logger = logging.getLogger("racerpath")


@app.on_event("startup")
def startup() -> None:
    configure_logging()
    init_db()
    try:
        app.state.redis = create_redis_client()
        app.state.redis.ping()
    except Exception:
        app.state.redis = None
    start_mock_race_background()
    start_mock_event_background()


@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api"):
        session = SessionLocal()
        try:
            api_key = request.headers.get("X-API-Key")
            user = get_user_by_key(session, api_key) if api_key else None
            log_audit(session, user, request.method, request.url.path, response.status_code)
        finally:
            session.close()
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def root():
    return {"service": "racerpath-api", "status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}

"""API router: routes grouped by semantic domain (auth → users → events → participations → tasks → licenses → crs/recs → ingest → tools → admin → dev)."""

from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.anti_gaming import router as anti_gaming_router
from app.api.routes.auth import router as auth_router
from app.api.routes.classify import router as classify_router
from app.api.routes.connectors import router as connectors_router
from app.api.routes.crs import router as crs_router
from app.api.routes.dev import router as dev_router
from app.api.routes.drivers import router as drivers_router
from app.api.routes.events import router as events_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.penalties import router as penalties_router
from app.api.routes.licenses import router as licenses_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.participations import router as participations_router
from app.api.routes.profile import router as profile_router
from app.api.routes.real_world import router as real_world_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.tasks import router as tasks_router

api_router = APIRouter(prefix="/api")

# Auth & identity
api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(drivers_router)

# Events & participations
api_router.include_router(events_router)
api_router.include_router(participations_router)

# Tasks & licenses
api_router.include_router(tasks_router)
api_router.include_router(licenses_router)

# CRS & recommendations
api_router.include_router(crs_router)
api_router.include_router(recommendations_router)

# Incidents & penalties
api_router.include_router(incidents_router)
api_router.include_router(penalties_router)

# Ingest & external
api_router.include_router(ingest_router)
api_router.include_router(real_world_router)
api_router.include_router(anti_gaming_router)

# Connectors & classification
api_router.include_router(connectors_router)
api_router.include_router(classify_router)

# Metrics
api_router.include_router(metrics_router)

# Admin & dev
api_router.include_router(admin_router)
api_router.include_router(dev_router)

# API Map

Base prefix: `/api` (FastAPI). All paths below include the `/api` prefix unless noted.

## Core/Health
- `GET /` - Service status.
- `GET /api/health` - Health check.
- `GET /api/metrics` - System metrics (counts of drivers, events, classifications, participations).

## Auth (`/api/auth`)
- `POST /auth/bootstrap` - Bootstrap initial admin user.
- `POST /auth/register` - Register new user.
- `POST /auth/login` - Login user and get API key.
- `GET /auth/me` - Get current authenticated user.
- `POST /auth/users` - Create user (admin only).
- `GET /auth/users` - List users (admin only).
- `GET /auth/audit` - List audit logs (admin/coach).

## Profile (`/api/profile`)
- `GET /profile/me` - Get current user's profile.
- `PUT /profile/me` - Update current user's profile.

## Drivers (`/api/drivers`)
- `POST /drivers` - Create driver profile.
- `GET /drivers` - List drivers.
- `GET /drivers/me` - Get current user's driver profile.
- `POST /drivers/me` - Create current user's driver profile.
- `GET /drivers/{driver_id}` - Get driver by ID.

## Events (`/api/events`)
- `POST /events` - Create event (admin only).
- `GET /events` - List events (filterable).
- `GET /events/{event_id}` - Get event by ID.
- `GET /events/{event_id}/classification` - Get event classification.
- `GET /events/{event_id}/classifications` - List classifications for event.
- `POST /events/{event_id}/classify` - Reclassify event.

## Classify (`/api/classify`)
- `POST /classify` - Classify event data (cached).

## Participations (`/api/participations`)
- `POST /participations` - Create participation record.
- `GET /participations` - List participations (filterable).
- `GET /participations/{participation_id}` - Get participation by ID.
- `POST /participations/{participation_id}/incidents` - Create incident for participation.
- `GET /participations/{participation_id}/incidents` - List incidents for participation.

## Incidents (`/api/incidents`)
- `GET /incidents` - List incidents (filterable).
- `GET /incidents/{incident_id}` - Get incident by ID.

## CRS (`/api/crs`)
- `POST /crs/compute` - Compute CRS for driver/discipline.
- `GET /crs/history` - List CRS history for driver.
- `GET /crs/latest` - Get latest CRS for driver/discipline.

## Recommendations (`/api/recommendations`)
- `POST /recommendations/compute` - Compute recommendations for driver/discipline.
- `GET /recommendations` - List recommendations (filterable).
- `GET /recommendations/latest` - Get latest recommendation for driver/discipline.

## Licenses (`/api/licenses`)
- `POST /licenses/levels` - Create license level (admin only).
- `GET /licenses/levels` - List license levels (filterable by discipline).
- `POST /licenses/award` - Award license to driver (admin/coach).
- `GET /licenses` - List driver licenses (filterable by discipline).

## Tasks (`/api/tasks`)
- `POST /tasks/definitions` - Create task definition (admin/coach).
- `GET /tasks/definitions` - List task definitions.
- `GET /tasks/definitions/{task_id}` - Get task definition by ID.
- `POST /tasks/completions` - Create task completion record.
- `GET /tasks/completions` - List task completions (filterable).
- `POST /tasks/evaluate` - Evaluate task completion for driver/participation.
- `GET /tasks/templates` - List task templates.
- `POST /tasks/templates/seed` - Seed task templates (admin/coach).

## Anti-gaming (`/api/anti-gaming`)
- `POST /anti-gaming/evaluate` - Evaluate anti-gaming metrics for driver.
- `GET /anti-gaming/reports` - List anti-gaming reports for driver.
- `GET /anti-gaming/reports/latest` - Get latest anti-gaming report.

## Real-world readiness (`/api/real-world`)
- `POST /real-world/formats` - Create real-world format (admin/coach).
- `GET /real-world/formats` - List real-world formats (filterable by discipline).
- `POST /real-world/assess` - Assess real-world readiness for driver.
- `GET /real-world/assessments` - List real-world assessments.
- `GET /real-world/assessments/latest` - Get latest assessment.

## Ingestion (`/api/ingest`)
- `GET /ingest/sources` - List available ingestion sources.
- `POST /ingest/raw-events` - Ingest raw event payload.
- `GET /ingest/raw-events` - List raw events.
- `GET /ingest/raw-events/{raw_event_id}` - Get raw event by ID.

## Connectors (`/api/connectors`)
- `GET /connectors/status` - Get connector configuration status.
- `POST /connectors/wss/sync` - Sync events from WSS source.
- `POST /connectors/gridfinder/sync` - Sync events from GridFinder source.

## Admin (`/api/admin`)
- `GET /admin/users` - List all users with completion stats (admin only).
- `GET /admin/users/{user_id}` - Get user details (admin only).
- `GET /admin/profiles/{user_id}` - Get user profile by ID (admin only).
- `PUT /admin/profiles/{user_id}` - Update user profile (admin only).
- `GET /admin/search/user` - Search user by email (admin only).
- `GET /admin/search/participations` - Search participations by driver/email (admin only).
- `GET /admin/driver/inspect` - Inspect driver details and participations (admin only).

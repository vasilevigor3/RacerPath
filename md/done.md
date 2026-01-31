# Done

2026-01-28 - Defined event classification schema (inputs, factors, scoring, tiers, and caps).
2026-01-28 - Built web app MVP (front-end UI + backend classification API).
2026-01-28 - Built working FastAPI app with Postgres + Redis, static frontend, and basic CRUD.
2026-01-28 - Added core DB schema + Alembic migrations for participation, incidents, tasks, CRS history, recommendations.
2026-01-28 - Implemented external event ingestion + normalization pipeline (raw_events, normalizer, API).
2026-01-28 - Implemented classification engine v1 (inputs snapshot/hash, versioned outputs, reclassify endpoints).
2026-01-28 - Added participation + incident tracking API for results and behavior.
2026-01-28 - Added CRS computation service + API (history, latest, compute).
2026-01-28 - Added tasks & challenges engine (definitions, completions, auto-evaluation).
2026-01-28 - Added recommendation engine v1 (compute + history endpoints).
2026-01-28 - Added license ladders + promotion rules (levels + awards API).
2026-01-28 - Added frontend dashboards for CRS, recommendations, and licenses.
2026-01-28 - Added auth + roles + audit logging (bootstrap + API key auth).
2026-01-28 - Added tests + observability (unit tests, metrics endpoint, error logging).
2026-01-28 - Added local ops polish (seed script + docs updates).
2026-01-28 - Implemented real-world mapping engine (formats + readiness assessment).
2026-01-28 - Added discipline task templates library (seedable templates per school).
2026-01-28 - Added anti-gaming enforcement (reports + CRS multiplier).
2026-01-28 - Added external connectors v1 (WSS/GridFinder sync endpoints + settings).
2026-01-28 - Added self-service accounts (register/login) and user-linked driver profiles.
2026-01-28 - Upgraded Tasks & Challenges Engine v2 (anti-farming rules, cooldowns, diversity, diminishing returns).
2026-01-29 - Added onboarding task templates (driver/profile/games), auto-completion hooks, and duration-aware task validation.
2026-01-29 - Auto-evaluate tasks on participation creation; added activity feed, license progress, and readiness index in the cabinet.
2026-01-29 - Expanded seed data with a 60-minute event, upcoming schedule dates, and accurate participation durations.
2026-01-29 - Drafted external event ingestion contract (`event-ingestion-contract.md`).
2026-01-29 - Fixed sticky header stacking and made stat tiles clickable with deep links to details.
2026-01-29 - Switched auth to email + password with mandatory onboarding for games + discipline path.
2026-01-29 - Consolidated duplicate profile CTAs and refocused the profile progress panel.
2026-01-29 - Replaced Off-road discipline with Karting across UI, schemas, and classification docs.
2026-01-29 - Updated profile CTA state to show "Edit profile" when completion is 100%.
2026-01-29 - Switched profile sim platforms and rig setup to selectable checkboxes; made goals system-owned and read-only.
2026-01-29 - Synced onboarding data into the user profile and prefilled the profile form from driver data.
2026-01-29 - Cleaned dashboard spacing/padding, removed residual "Waiting for input" cues, and added consistent form heights.
2026-01-29 - Rebuilt the Driver snapshot to reflect the logged-in driver, show real readiness data, and surface dynamic challenges/risks.
2026-01-29 - Hid operator tools from the racer cabinet and introduced an admin-only cabinet with user metrics, event lists, and gated navigation.
2026-01-29 - Split admin vs driver flows, added driver ID display, and gave admins targeted tools for player inspection plus profile adjustments and event creation rights.
2026-01-29 - Hardened role gating so driver nav/panels hide for admins and refreshed admin user/profile feeds to hit the proper `/api/*` endpoints, restoring the "load users" experience.
2026-01-29 - Prevented the profile-reset helper from hiding the admin console so that admins keep their dashboard visible after authentication.
2026-01-29 - Finished role-gating the UI: driver sections now hide for admins while admin nav/panels stay hidden for racers, verified by rebuilding assets/tests (ran `docker compose run --rm app bash -c "pip install pytest && pytest"` after the rebuild). 
2026-01-29 - Removed the admin-only event classification sandbox, consolidated the Operations/ Admin cabinet into one hybrid console (user metrics + driver/event forms), and simplified the admin nav to only Operations + Dashboards; rebuild/tests confirmed the new structure.
2026-01-29 - Normalized legacy `offroad` discipline values in task definitions so the models now treat them as `karting`, preventing FastAPI from rejecting `/api/tasks/definitions` responses (which was breaking login) and allowing fresh builds/tests to pass.
2026-01-29 - Moved the combined operations/admin console outside the onboarding-hidden wrapper so the admin landing page stays visible once the driver-only panels are hidden; rebuilt and re-tested the stack after the rearrangement.
2026-01-29 - Force-enabled auth visibility immediately after register/login success to keep the admin console from staying hidden while `loadProfile` finishes, then rebuilt and retested the bundle.

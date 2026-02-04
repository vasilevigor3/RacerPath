from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import _build_read, _compute_completion
from app.db.session import get_session
from app.models.driver import Driver
from app.models.user import User
from app.models.event import Event
from app.models.classification import Classification
from app.models.participation import Participation, ParticipationStatus, ParticipationState
from app.models.user_profile import UserProfile
from app.models.incident import Incident
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.models.task_definition import TaskDefinition
from app.models.crs_history import CRSHistory
from app.models.recommendation import Recommendation
from app.models.tier_progression_rule import TierProgressionRule
from app.repositories.classification import ClassificationRepository
from app.repositories.crs_history import CRSHistoryRepository
from app.repositories.driver import DriverRepository
from app.repositories.driver_license import DriverLicenseRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.license_level import LicenseLevelRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.task_definition import TaskDefinitionRepository
from app.repositories.tier_progression_rule import TierProgressionRuleRepository
from app.repositories.user import UserRepository
from app.repositories.user_profile import UserProfileRepository
from app.services.timeline_validation import validate_participation_timeline
from app.services.user_clear import clear_user_data
from app.schemas.admin import (
    AdminClearUserRequest,
    AdminClearUserResponse,
    AdminLookupRead,
    AdminDriverCrsDiagnostic,
    AdminLookupUser,
    AdminLookupDriver,
    AdminLookupParticipationItem,
    AdminLookupIncidentItem,
    AdminLookupLicenseItem,
    AdminLookupCrsItem,
    AdminLookupRecommendationItem,
    AdminParticipationSearchRead,
    AdminParticipationSummary,
    AdminPlayerInspectRead,
    AdminUserRead,
    AdminUserSearchRead,
    AdminEventDetailRead,
    AdminEventParticipationItem,
    AdminParticipationDetailRead,
    AdminParticipationDriverRef,
    AdminParticipationEventRef,
    AdminParticipationIncidentItem,
    AdminParticipationUpdate,
    AdminIncidentRead,
    AdminIncidentDetailRead,
    AdminIncidentParticipationRef,
    AdminIncidentEventRef,
    AdminIncidentDriverRef,
    TierProgressionRuleRead,
    TierProgressionRuleUpdate,
    AdminTaskDefinitionRead,
    AdminLicenseLevelRef,
)
from app.schemas.driver import DriverRead
from app.schemas.task import TaskDefinitionCreate, TaskDefinitionUpdate
from app.schemas.license import (
    LicenseLevelCreate,
    LicenseLevelRead,
    LicenseLevelUpdate,
    LicenseAwardCheckRead,
    LicenseAwardRequest,
    DriverLicenseRead,
)
from app.services.licenses import check_eligibility, award_license
from app.models.enums.event_enums import EventStatus
from app.schemas.event import EventRead
from app.schemas.classification import ClassificationRead, ClassificationCreate, ClassificationUpdate
from app.schemas.participation import ParticipationRead, ParticipationAdminRead
from app.schemas.profile import UserProfileRead, UserProfileUpsert
from app.services.auth import require_roles
from app.services.next_tier import compute_next_tier_progress
from app.events.participation_events import dispatch_participation_completed
from app.services.global_tasks import check_and_complete_global_tasks
from app.services.tasks import ensure_task_completion
from app.services.race_of_day import restart_race_of_day
from app.services.test_data import reset_all_tasks_licenses_events, create_test_task_and_event_set
from app.core.constants import VALID_TIERS

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/profiles/{user_id}", response_model=UserProfileRead)
def get_profile(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    profile = UserProfileRepository(session).get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    next_tier, next_tier_data = compute_next_tier_progress(session, user_id)
    return _build_read(profile, next_tier_progress_percent=next_tier, next_tier_data=next_tier_data)

@router.put("/profiles/{user_id}", response_model=UserProfileRead)
def update_profile(
    user_id: str,
    payload: UserProfileUpsert,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    profile_repo = UserProfileRepository(session)
    profile = profile_repo.get_by_user_id(user_id)
    if not profile:
        profile = UserProfile(user_id=user_id)
        profile_repo.add(profile)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "sim_platforms" and value is None:
            value = []
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    driver = DriverRepository(session).get_by_user_id(user_id)
    if profile.sim_platforms and driver:
        driver.sim_games = profile.sim_platforms
    session.commit()
    session.refresh(profile)
    profile_completion, missing, _ = _compute_completion(profile)
    if driver:
        suffix = (driver.primary_discipline or "gt").upper()
        if driver.sim_games:
            ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
        if profile_completion >= 100 or not missing:
            ensure_task_completion(session, driver.id, f"ONBOARD_PROFILE_{suffix}")
        ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
        check_and_complete_global_tasks(session, driver.id)
        session.commit()
    next_tier, next_tier_data = compute_next_tier_progress(session, user_id)
    return _build_read(profile, next_tier_progress_percent=next_tier, next_tier_data=next_tier_data)


@router.get("/users", response_model=List[AdminUserRead])
def list_users(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    limit = max(1, min(limit, 200))
    users = UserRepository(session).list_paginated(offset=offset, limit=limit)
    user_ids = [user.id for user in users]
    profiles = UserProfileRepository(session).get_by_user_ids(user_ids)
    drivers = [d for d in DriverRepository(session).list_all() if d.user_id in user_ids]
    profile_map = {profile.user_id: profile for profile in profiles}
    driver_map = {driver.user_id: driver for driver in drivers}
    response = []
    for user in users:
        profile = profile_map.get(user.id)
        profile_completion, _, level = _compute_completion(profile)
        driver = driver_map.get(user.id)
        response.append(
            AdminUserRead(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                active=user.active,
                created_at=user.created_at,
                profile_id=profile.id if profile else None,
                profile_completion_percent=profile_completion,
                level=level,
                driver_id=driver.id if driver else None,
            )
        )
    return sorted(response, key=lambda row: row.profile_completion_percent, reverse=True)


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user_detail(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user = UserRepository(session).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = UserProfileRepository(session).get_by_user_id(user.id)
    driver = DriverRepository(session).get_by_user_id(user.id)
    profile_completion, _, level = _compute_completion(profile)
    return AdminUserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        profile_id=profile.id if profile else None,
        profile_completion_percent=profile_completion,
        level=level,
        driver_id=driver.id if driver else None,
    )


def _find_user_and_driver(session: Session, query: str) -> tuple[User | None, Driver | None]:
    user_repo = UserRepository(session)
    driver_repo = DriverRepository(session)
    if "@" in query:
        user = user_repo.get_by_email(query)
        driver = driver_repo.get_by_user_id(user.id) if user else None
        return user, driver
    driver = driver_repo.get_by_id(query)
    user = user_repo.get_by_id(driver.user_id) if driver else None
    return user, driver


@router.get("/lookup", response_model=AdminLookupRead)
def admin_lookup(
    q: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Unified search by email or driver_id. Returns user, driver, participations, incidents, licenses, last CRS/recommendation."""
    user, driver = _find_user_and_driver(session, q.strip())
    if not driver:
        raise HTTPException(status_code=404, detail="User or driver not found")

    if not user:
        user = UserRepository(session).get_by_id(driver.user_id)

    user_out = (
        AdminLookupUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            active=user.active,
        )
        if user
        else None
    )
    driver_out = AdminLookupDriver(
        id=driver.id,
        name=driver.name,
        primary_discipline=driver.primary_discipline or "",
        tier=getattr(driver, "tier", "E0") or "E0",
        sim_games=driver.sim_games or [],
    )

    participations = ParticipationRepository(session).list_by_driver_id_with_events(
        driver.id, limit=50
    )
    part_items = []
    participation_ids = []
    for part, event in participations:
        participation_ids.append(part.id)
        incidents_count = (
            IncidentRepository(session).count_by_participation_id(part.id)
        )
        part_items.append(
            AdminLookupParticipationItem(
                id=part.id,
                event_id=part.event_id,
                event_title=event.title if event else None,
                event_game=event.game if event else None,
                started_at=part.started_at,
                finished_at=part.finished_at,
                status=part.status.value if hasattr(part.status, "value") else str(part.status),
                participation_state=part.participation_state.value if hasattr(part.participation_state, "value") else str(part.participation_state),
                incidents_count=incidents_count,
            )
        )

    incidents = IncidentRepository(session).list_by_participation_ids(
        participation_ids, limit=100
    )
    incident_items = [
        AdminLookupIncidentItem(
            id=i.id,
            participation_id=i.participation_id,
            incident_type=i.incident_type,
            severity=i.severity,
            lap=i.lap,
        )
        for i in incidents
    ]

    licenses = DriverLicenseRepository(session).list_by_driver_id(driver.id)
    license_items = [
        AdminLookupLicenseItem(id=l.id, discipline=l.discipline, level_code=l.level_code, status=l.status)
        for l in licenses
    ]

    last_crs = CRSHistoryRepository(session).latest_by_driver(driver.id)
    crs_out = (
        AdminLookupCrsItem(
            id=last_crs.id,
            discipline=last_crs.discipline,
            score=last_crs.score,
            computed_at=last_crs.computed_at,
        )
        if last_crs
        else None
    )

    last_rec = RecommendationRepository(session).latest_by_driver(driver.id)
    rec_out = (
        AdminLookupRecommendationItem(
            id=last_rec.id,
            discipline=last_rec.discipline,
            readiness_status=last_rec.readiness_status,
            summary=last_rec.summary,
            created_at=last_rec.created_at,
        )
        if last_rec
        else None
    )

    return AdminLookupRead(
        user=user_out,
        driver=driver_out,
        participations=part_items,
        incidents=incident_items,
        licenses=license_items,
        last_crs=crs_out,
        last_recommendation=rec_out,
    )


@router.get("/search/user", response_model=AdminUserSearchRead)
def search_user_by_email(
    email: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user = UserRepository(session).get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    driver = DriverRepository(session).get_by_user_id(user.id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return AdminUserSearchRead(
        driver_id=driver.id,
        email=user.email,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
    )


@router.get("/search/participations", response_model=AdminParticipationSearchRead)
def search_participations(
    q: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user, driver = _find_user_and_driver(session, q)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    participations = ParticipationRepository(session).list_by_driver_id_with_events(
        driver.id, limit=1000
    )
    items = []
    for participation, event in participations:
        item = participation.__dict__.copy()
        item["game"] = event.game if event else None
        item.pop("_sa_instance_state", None)
        items.append(item)
    return AdminParticipationSearchRead(
        driver_id=driver.id,
        driver_email=user.email if user else None,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
        participations=items,
    )


@router.get("/driver/inspect", response_model=AdminPlayerInspectRead)
def inspect_driver(
    q: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user, driver = _find_user_and_driver(session, q)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    participations = ParticipationRepository(session).list_by_driver_id(driver.id)
    # Re-sort by started_at desc for summary
    participations = sorted(
        participations,
        key=lambda p: (p.started_at or p.created_at or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )
    summary = [
        AdminParticipationSummary(id=item.id, started_at=item.started_at) for item in participations
    ]
    return AdminPlayerInspectRead(
        driver_id=driver.id,
        driver_email=user.email if user else None,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
        participations=summary,
    )


@router.post("/clear-user", response_model=AdminClearUserResponse)
def post_clear_user(
    payload: AdminClearUserRequest,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Clear all data for a user by email: licenses, task completions, participations, incidents. User and driver remain."""
    try:
        counts = clear_user_data(session, payload.email.strip())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    session.commit()
    return AdminClearUserResponse(**counts)


@router.post("/race-of-day/restart")
def post_race_of_day_restart(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Delete current Race of the day event(s) with all relations, create a new one (E0)."""
    return restart_race_of_day(session)


@router.post("/reset-and-seed-test-data")
def post_reset_and_seed_test_data(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Reset all tasks, licenses, events and related; then create test set (GT_TEST_FLOW, GT_TEST_FLOW_2, 2 events, GT_E0_TEST)."""
    reset_counts = reset_all_tasks_licenses_events(session)
    session.commit()
    created = create_test_task_and_event_set(session)
    session.commit()
    return {"reset": reset_counts, "created": created}


@router.get("/events/{event_id}", response_model=AdminEventDetailRead)
def get_event_detail(
    event_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Event details + classification + participations list."""
    event = EventRepository(session).get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification = ClassificationRepository(session).get_latest_for_event(event_id)
    participations = ParticipationRepository(session).list_by_event_id_with_drivers(
        event_id, limit=200
    )
    part_items = [
        AdminEventParticipationItem(
            id=p.id,
            driver_id=p.driver_id,
            driver_name=dr.name if dr else None,
            status=p.status.value if hasattr(p.status, "value") else str(p.status),
            position_overall=p.position_overall,
            laps_completed=p.laps_completed,
            incidents_count=p.incidents_count,
            started_at=p.started_at,
        )
        for p, dr in participations
    ]
    event_data = {k: getattr(event, k) for k in EventRead.model_fields if hasattr(event, k)}
    event_data.setdefault("event_status", EventStatus.scheduled)
    return AdminEventDetailRead(
        event=EventRead.model_validate(event_data),
        classification=ClassificationRead.model_validate(classification) if classification else None,
        participations=part_items,
    )


@router.get("/participations/{participation_id}", response_model=AdminParticipationDetailRead)
def get_participation_detail(
    participation_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Participation details + driver + event + incidents list."""
    part = ParticipationRepository(session).get_by_id(participation_id, with_counts=True)
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    driver = DriverRepository(session).get_by_id(part.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    event = EventRepository(session).get_by_id(part.event_id)
    incidents = IncidentRepository(session).list_by_participation_id(participation_id)
    part_data = {**ParticipationRead.model_validate(part).model_dump(), "game": event.game if event else None}
    return AdminParticipationDetailRead(
        participation=ParticipationAdminRead(**part_data),
        driver=AdminParticipationDriverRef(
            id=driver.id,
            name=driver.name,
            primary_discipline=driver.primary_discipline or "",
            sim_games=driver.sim_games or [],
        ),
        event=AdminParticipationEventRef(
            id=part.event_id,
            title=event.title if event else "",
            game=event.game if event else None,
        ),
        incidents=[
            AdminParticipationIncidentItem(
                id=i.id,
                code=getattr(i, "code", None),
                score=getattr(i, "score", 0.0),
                incident_type=i.incident_type,
                severity=i.severity,
                lap=i.lap,
                description=i.description,
                created_at=i.created_at,
            )
            for i in incidents
        ],
    )


@router.patch("/participations/{participation_id}", response_model=ParticipationRead)
def update_participation(
    participation_id: str,
    payload: AdminParticipationUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Update participation fields (status, participation_state, position, laps, started_at, finished_at). Dates are validated: finished_at >= started_at when both set; started requires started_at; completed requires started_at and finished_at."""
    part = ParticipationRepository(session).get_by_id(participation_id)
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = ParticipationStatus(data["status"])
    if "participation_state" in data and data["participation_state"] is not None:
        data["participation_state"] = ParticipationState(data["participation_state"])
    for key, value in data.items():
        setattr(part, key, value)

    # When setting completed without started_at, set started_at so validation passes and dispatch runs
    if part.participation_state == ParticipationState.completed and part.started_at is None:
        if part.finished_at is not None:
            part.started_at = part.finished_at - timedelta(minutes=30)
        else:
            now = datetime.now(timezone.utc)
            part.started_at = now - timedelta(minutes=30)
            if part.finished_at is None:
                part.finished_at = now

    # Date validation
    if part.started_at is not None and part.finished_at is not None:
        if part.finished_at < part.started_at:
            raise HTTPException(
                status_code=400,
                detail="finished_at must be greater than or equal to started_at.",
            )
    if part.participation_state == ParticipationState.started:
        if part.started_at is None:
            raise HTTPException(
                status_code=400,
                detail="participation_state=started requires started_at to be set.",
            )
    if part.participation_state == ParticipationState.completed:
        if part.started_at is None:
            raise HTTPException(
                status_code=400,
                detail="participation_state=completed requires started_at to be set.",
            )
        if part.finished_at is None:
            raise HTTPException(
                status_code=400,
                detail="participation_state=completed requires finished_at to be set.",
            )
        if part.finished_at < part.started_at:
            raise HTTPException(
                status_code=400,
                detail="finished_at must be greater than or equal to started_at.",
            )

    event = EventRepository(session).get_by_id(part.event_id)
    try:
        validate_participation_timeline(part, event)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    session.commit()
    session.refresh(part)
    if part.participation_state == ParticipationState.completed:
        dispatch_participation_completed(session, part.driver_id, part.id)
    return part


@router.get("/incidents/{incident_id}", response_model=AdminIncidentDetailRead)
def get_incident_detail(
    incident_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Incident details + participation + event + driver."""
    incident = IncidentRepository(session).get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    part = ParticipationRepository(session).get_by_id(incident.participation_id)
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    event = EventRepository(session).get_by_id(part.event_id)
    driver = DriverRepository(session).get_by_id(part.driver_id)
    return AdminIncidentDetailRead(
        incident=AdminIncidentRead(
            id=incident.id,
            participation_id=incident.participation_id,
            code=getattr(incident, "code", None),
            score=getattr(incident, "score", 0.0),
            incident_type=incident.incident_type,
            severity=incident.severity,
            lap=incident.lap,
            description=incident.description,
            created_at=incident.created_at,
        ),
        participation=AdminIncidentParticipationRef(
            id=part.id,
            driver_id=part.driver_id,
            event_id=part.event_id,
            status=part.status.value if hasattr(part.status, "value") else str(part.status),
            started_at=part.started_at,
        ),
        event=AdminIncidentEventRef(id=event.id, title=event.title, game=event.game) if event else None,
        driver=AdminIncidentDriverRef(id=driver.id, name=driver.name) if driver else None,
    )


# --- Tier progression rules (admin) ---


@router.get("/tier-rules", response_model=List[TierProgressionRuleRead])
def list_tier_rules(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """List all tier progression rules. Missing tiers are not returned (use PATCH to create)."""
    return TierProgressionRuleRepository(session).list_all()


@router.get("/tier-rules/{tier}", response_model=TierProgressionRuleRead)
def get_tier_rule(
    tier: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    tier = tier.strip().upper()
    if tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    rule = TierProgressionRuleRepository(session).get_by_tier(tier)
    if not rule:
        raise HTTPException(status_code=404, detail="Tier rule not found")
    return rule


@router.patch("/tier-rules/{tier}", response_model=TierProgressionRuleRead)
def update_tier_rule(
    tier: str,
    payload: TierProgressionRuleUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Create or update tier rule: min_events and difficulty_threshold for next_tier_progress_percent."""
    tier = tier.strip().upper()
    if tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    rule = TierProgressionRuleRepository(session).get_by_tier(tier)
    if not rule:
        rule = TierProgressionRule(tier=tier, min_events=5, difficulty_threshold=0.0, required_license_codes=[])
        session.add(rule)
    data = payload.model_dump(exclude_unset=True)
    if "min_events" in data:
        rule.min_events = max(0, data["min_events"])
    if "difficulty_threshold" in data:
        rule.difficulty_threshold = float(data["difficulty_threshold"])
    if "required_license_codes" in data:
        rule.required_license_codes = list(data["required_license_codes"]) if data["required_license_codes"] is not None else []
    session.commit()
    session.refresh(rule)
    return rule


# --- License levels (admin) ---


@router.get("/license-levels", response_model=List[LicenseLevelRead])
def list_license_levels(
    discipline: str | None = None,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """List license levels. Optional filter by discipline."""
    return LicenseLevelRepository(session).list_by_discipline(discipline=discipline)


@router.post("/license-levels", response_model=LicenseLevelRead)
def create_license_level(
    payload: LicenseLevelCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Create a license level."""
    level = LicenseLevel(**payload.model_dump())
    session.add(level)
    session.commit()
    session.refresh(level)
    return level


@router.get("/license-levels/{level_id}", response_model=LicenseLevelRead)
def get_license_level(
    level_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    level = LicenseLevelRepository(session).get_by_id(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="License level not found")
    return level


@router.patch("/license-levels/{level_id}", response_model=LicenseLevelRead)
def update_license_level(
    level_id: str,
    payload: LicenseLevelUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    level = LicenseLevelRepository(session).get_by_id(level_id)
    if not level:
        raise HTTPException(status_code=404, detail="License level not found")
    data = payload.model_dump(exclude_unset=True)
    if "required_task_codes" in data and data["required_task_codes"] is not None:
        level.required_task_codes = list(data["required_task_codes"])
    for key, value in data.items():
        if key != "required_task_codes" and value is not None:
            setattr(level, key, value)
    session.commit()
    session.refresh(level)
    return level


def _resolve_driver_id(session: Session, driver_id: str | None, email: str | None) -> str:
    """Resolve driver_id from driver_id or email. Raises HTTPException if not found."""
    if driver_id and driver_id.strip():
        driver = DriverRepository(session).get_by_id(driver_id.strip())
        if driver:
            return driver.id
        raise HTTPException(status_code=404, detail="Driver not found")
    if email and email.strip():
        user = UserRepository(session).get_by_email(email.strip())
        if not user:
            raise HTTPException(status_code=404, detail="User not found by email")
        driver = DriverRepository(session).get_by_user_id(user.id)
        if not driver:
            raise HTTPException(status_code=404, detail="No driver linked to this user")
        return driver.id
    raise HTTPException(status_code=400, detail="Provide driver_id or email")


@router.get("/license-award-check", response_model=LicenseAwardCheckRead)
def license_award_check(
    discipline: str,
    driver_id: str | None = None,
    email: str | None = None,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Check eligibility for next license. Use driver_id or email."""
    did = _resolve_driver_id(session, driver_id, email)
    result = check_eligibility(session, did, discipline)
    return LicenseAwardCheckRead(
        eligible=result.eligible,
        next_level_code=result.next_level_code,
        reasons=result.reasons,
        current_crs=result.current_crs,
        completed_task_codes=result.completed_task_codes,
        required_task_codes=result.required_task_codes,
    )


@router.post("/license-award", response_model=DriverLicenseRead)
def admin_license_award(
    payload: LicenseAwardRequest,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Award next license by driver_id or email. Returns 400 with reasons if not eligible."""
    driver_id = _resolve_driver_id(session, payload.driver_id, payload.email)
    result = check_eligibility(session, driver_id, payload.discipline)
    if not result.eligible:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Not eligible for next license",
                "reasons": result.reasons,
                "next_level_code": result.next_level_code,
                "current_crs": result.current_crs,
                "completed_task_codes": result.completed_task_codes,
                "required_task_codes": result.required_task_codes,
            },
        )
    awarded = award_license(session, driver_id, payload.discipline)
    if not awarded:
        raise HTTPException(status_code=400, detail="Award failed unexpectedly")
    return awarded


@router.get("/driver-crs-diagnostic", response_model=AdminDriverCrsDiagnostic)
def driver_crs_diagnostic(
    email: str | None = None,
    driver_id: str | None = None,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Diagnose why CRS might be 0: no participations, events missing classification, or CRS never computed."""
    did = _resolve_driver_id(session, driver_id, email)
    driver = DriverRepository(session).get_by_id(did)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    discipline = driver.primary_discipline or "gt"

    all_parts = ParticipationRepository(session).list_by_driver_id(did)
    participations = [p for p in all_parts if (p.discipline.value if hasattr(p.discipline, "value") else p.discipline) == discipline]
    participations_count = len(participations)

    events_missing_classification: list[str] = []
    for p in participations:
        classification = ClassificationRepository(session).get_latest_for_event(p.event_id)
        if not classification:
            events_missing_classification.append(p.event_id)

    last_crs = CRSHistoryRepository(session).latest_by_driver_and_discipline(did, discipline)
    latest_crs_score = last_crs.score if last_crs else None
    latest_crs_discipline = last_crs.discipline if last_crs else None

    if participations_count == 0:
        reason = "No participations for this driver in discipline " + discipline + "; CRS is 0 or never computed."
    elif events_missing_classification:
        reason = (
            f"{len(events_missing_classification)} event(s) have no classification; "
            "add classification for those events then call POST /api/crs/compute or POST /api/dev/recompute."
        )
    elif latest_crs_score is None:
        reason = "CRS was never computed; call POST /api/crs/compute?driver_id=...&discipline=... or POST /api/dev/recompute."
    else:
        reason = "OK" if latest_crs_score > 0 else "CRS was computed and is 0 (e.g. no participations at compute time)."

    return AdminDriverCrsDiagnostic(
        driver_id=did,
        primary_discipline=discipline,
        participations_count=participations_count,
        events_missing_classification=events_missing_classification,
        latest_crs_score=latest_crs_score,
        latest_crs_discipline=latest_crs_discipline,
        reason=reason,
    )


# --- Classifications (admin) ---


@router.get("/classifications", response_model=List[ClassificationRead])
def list_classifications_admin(
    event_id: str | None = None,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """List classifications. Optional filter by event_id."""
    return ClassificationRepository(session).list_for_event_admin(event_id)


@router.post("/classifications", response_model=ClassificationRead)
def create_classification_admin(
    payload: ClassificationCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Create a classification (1 event = 1 classification; event must exist)."""
    event = EventRepository(session).get_by_id(payload.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    existing = ClassificationRepository(session).get_latest_for_event(payload.event_id)
    if existing:
        raise HTTPException(status_code=400, detail="Event already has a classification")
    classification = Classification(**payload.model_dump())
    session.add(classification)
    session.commit()
    session.refresh(classification)
    return classification


@router.get("/classifications/{classification_id}", response_model=ClassificationRead)
def get_classification_admin(
    classification_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    classification = ClassificationRepository(session).get_by_id(classification_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification


@router.patch("/classifications/{classification_id}", response_model=ClassificationRead)
def update_classification_admin(
    classification_id: str,
    payload: ClassificationUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    classification = ClassificationRepository(session).get_by_id(classification_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(classification, key, value)
    session.commit()
    session.refresh(classification)
    return classification


# --- Task definitions (admin: list with license links, CRUD) ---


def _required_by_license_levels(session: Session, task_code: str) -> list:
    """License levels that have task_code in required_task_codes."""
    from app.schemas.admin import AdminLicenseLevelRef
    levels = LicenseLevelRepository(session).list_by_discipline(active_only=True)
    refs = []
    for lev in levels:
        codes = lev.required_task_codes or []
        if task_code in codes:
            refs.append(AdminLicenseLevelRef(level_code=lev.code, discipline=lev.discipline))
    return refs


@router.get("/task-definitions", response_model=List[AdminTaskDefinitionRead])
def list_task_definitions_admin(
    discipline: str | None = None,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """List task definitions with which license levels require each task (by code)."""
    tasks = TaskDefinitionRepository(session).list_all()
    if discipline:
        tasks = [t for t in tasks if t.discipline == discipline]
    tasks = sorted(tasks, key=lambda t: (t.discipline or "", t.code or ""))
    out = []
    for t in tasks:
        refs = _required_by_license_levels(session, t.code)
        out.append(AdminTaskDefinitionRead.model_validate(t).model_copy(update={"required_by_license_levels": refs}))
    return out


@router.post("/task-definitions", response_model=AdminTaskDefinitionRead)
def create_task_definition_admin(
    payload: TaskDefinitionCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Create task definition."""
    task = TaskDefinition(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    refs = _required_by_license_levels(session, task.code)
    return AdminTaskDefinitionRead.model_validate(task).model_copy(update={"required_by_license_levels": refs})


@router.get("/task-definitions/{task_id}", response_model=AdminTaskDefinitionRead)
def get_task_definition_admin(
    task_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    task = TaskDefinitionRepository(session).get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    refs = _required_by_license_levels(session, task.code)
    return AdminTaskDefinitionRead.model_validate(task).model_copy(update={"required_by_license_levels": refs})


@router.patch("/task-definitions/{task_id}", response_model=AdminTaskDefinitionRead)
def update_task_definition_admin(
    task_id: str,
    payload: TaskDefinitionUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    task = TaskDefinitionRepository(session).get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)
    session.commit()
    session.refresh(task)
    refs = _required_by_license_levels(session, task.code)
    return AdminTaskDefinitionRead.model_validate(task).model_copy(update={"required_by_license_levels": refs})

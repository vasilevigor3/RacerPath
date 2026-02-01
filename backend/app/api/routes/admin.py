from datetime import datetime, timezone
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
from app.models.crs_history import CRSHistory
from app.models.recommendation import Recommendation
from app.models.tier_progression_rule import TierProgressionRule
from app.schemas.admin import (
    AdminLookupRead,
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
)
from app.schemas.driver import DriverRead
from app.models.enums.event_enums import EventStatus
from app.schemas.event import EventRead
from app.schemas.classification import ClassificationRead
from app.schemas.participation import ParticipationRead, ParticipationAdminRead
from app.schemas.profile import UserProfileRead, UserProfileUpsert
from app.services.auth import require_roles
from app.services.next_tier import compute_next_tier_progress
from app.services.tasks import ensure_task_completion

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/profiles/{user_id}", response_model=UserProfileRead)
def get_profile(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
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
    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "sim_platforms" and value is None:
            value = []
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    driver = session.query(Driver).filter(Driver.user_id == user_id).first()
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
    users = (
        session.query(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    user_ids = [user.id for user in users]
    profiles = session.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).all()
    drivers = session.query(Driver).filter(Driver.user_id.in_(user_ids)).all()
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
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    driver = session.query(Driver).filter(Driver.user_id == user.id).first()
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
    if "@" in query:
        user = session.query(User).filter(User.email == query).first()
        driver = session.query(Driver).filter(Driver.user_id == user.id).first() if user else None
        return user, driver
    driver = session.query(Driver).filter(Driver.id == query).first()
    user = session.query(User).filter(User.id == driver.user_id).first() if driver else None
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
        user = session.query(User).filter(User.id == driver.user_id).first()

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

    participations = (
        session.query(Participation, Event)
        .join(Event, Participation.event_id == Event.id, isouter=True)
        .filter(Participation.driver_id == driver.id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .limit(50)
        .all()
    )
    part_items = []
    participation_ids = []
    for part, event in participations:
        participation_ids.append(part.id)
        incidents_count = (
            session.query(Incident).filter(Incident.participation_id == part.id).count()
        )
        part_items.append(
            AdminLookupParticipationItem(
                id=part.id,
                event_id=part.event_id,
                event_title=event.title if event else None,
                event_game=event.game if event else None,
                started_at=part.started_at,
                status=part.status.value if hasattr(part.status, "value") else str(part.status),
                incidents_count=incidents_count,
            )
        )

    incidents = (
        session.query(Incident)
        .filter(Incident.participation_id.in_(participation_ids))
        .order_by(Incident.created_at.desc())
        .limit(100)
        .all()
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

    licenses = (
        session.query(DriverLicense)
        .filter(DriverLicense.driver_id == driver.id)
        .order_by(DriverLicense.awarded_at.desc())
        .all()
    )
    license_items = [
        AdminLookupLicenseItem(id=l.id, discipline=l.discipline, level_code=l.level_code, status=l.status)
        for l in licenses
    ]

    last_crs = (
        session.query(CRSHistory)
        .filter(CRSHistory.driver_id == driver.id)
        .order_by(CRSHistory.computed_at.desc())
        .first()
    )
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

    last_rec = (
        session.query(Recommendation)
        .filter(Recommendation.driver_id == driver.id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
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
    user = session.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    driver = session.query(Driver).filter(Driver.user_id == user.id).first()
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
    participations = (
        session.query(Participation, Event)
        .join(Event, Participation.event_id == Event.id, isouter=True)
        .filter(Participation.driver_id == driver.id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .all()
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
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver.id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .all()
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


@router.get("/events/{event_id}", response_model=AdminEventDetailRead)
def get_event_detail(
    event_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Event details + classification + participations list."""
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification = (
        session.query(Classification).filter(Classification.event_id == event_id).first()
    )
    participations = (
        session.query(Participation, Driver)
        .join(Driver, Participation.driver_id == Driver.id, isouter=True)
        .filter(Participation.event_id == event_id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .limit(200)
        .all()
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
    part = session.query(Participation).filter(Participation.id == participation_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    driver = session.query(Driver).filter(Driver.id == part.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    event = session.query(Event).filter(Event.id == part.event_id).first()
    incidents = (
        session.query(Incident)
        .filter(Incident.participation_id == participation_id)
        .order_by(Incident.lap.asc().nulls_last(), Incident.created_at.asc())
        .all()
    )
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
    """Update participation fields (status, participation_state, position, laps, started_at, finished_at)."""
    part = session.query(Participation).filter(Participation.id == participation_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] is not None:
        data["status"] = ParticipationStatus(data["status"])
    if "participation_state" in data and data["participation_state"] is not None:
        data["participation_state"] = ParticipationState(data["participation_state"])
    for key, value in data.items():
        setattr(part, key, value)
    session.commit()
    session.refresh(part)
    return part


@router.get("/incidents/{incident_id}", response_model=AdminIncidentDetailRead)
def get_incident_detail(
    incident_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """Incident details + participation + event + driver."""
    incident = session.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    part = (
        session.query(Participation)
        .filter(Participation.id == incident.participation_id)
        .first()
    )
    if not part:
        raise HTTPException(status_code=404, detail="Participation not found")
    event = session.query(Event).filter(Event.id == part.event_id).first()
    driver = session.query(Driver).filter(Driver.id == part.driver_id).first()
    return AdminIncidentDetailRead(
        incident=AdminIncidentRead(
            id=incident.id,
            participation_id=incident.participation_id,
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

VALID_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5")


@router.get("/tier-rules", response_model=List[TierProgressionRuleRead])
def list_tier_rules(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    """List all tier progression rules. Missing tiers are not returned (use PATCH to create)."""
    return session.query(TierProgressionRule).order_by(TierProgressionRule.tier).all()


@router.get("/tier-rules/{tier}", response_model=TierProgressionRuleRead)
def get_tier_rule(
    tier: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    tier = tier.strip().upper()
    if tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    rule = session.query(TierProgressionRule).filter(TierProgressionRule.tier == tier).first()
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
    rule = session.query(TierProgressionRule).filter(TierProgressionRule.tier == tier).first()
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

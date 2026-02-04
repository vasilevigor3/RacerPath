from datetime import datetime

from app.schemas.participation import ParticipationAdminRead
from app.schemas.event import EventRead
from app.schemas.classification import ClassificationRead

from pydantic import BaseModel


class AdminLookupUser(BaseModel):
    id: str
    name: str
    email: str | None
    role: str
    active: bool


class AdminLookupDriver(BaseModel):
    id: str
    name: str
    primary_discipline: str
    tier: str = "E0"
    sim_games: list[str] = []


class AdminLookupParticipationItem(BaseModel):
    id: str
    event_id: str
    event_title: str | None
    event_game: str | None
    started_at: datetime | None
    finished_at: datetime | None
    status: str
    participation_state: str
    incidents_count: int


class AdminLookupIncidentItem(BaseModel):
    id: str
    participation_id: str
    incident_type: str
    severity: int
    lap: int | None


class AdminLookupLicenseItem(BaseModel):
    id: str
    discipline: str
    level_code: str
    status: str


class AdminLookupCrsItem(BaseModel):
    id: str
    discipline: str
    score: float
    computed_at: datetime | None


class AdminLookupRecommendationItem(BaseModel):
    id: str
    discipline: str
    readiness_status: str
    summary: str
    created_at: datetime | None


class AdminLookupRead(BaseModel):
    user: AdminLookupUser | None
    driver: AdminLookupDriver | None
    participations: list[AdminLookupParticipationItem] = []
    incidents: list[AdminLookupIncidentItem] = []
    licenses: list[AdminLookupLicenseItem] = []
    last_crs: AdminLookupCrsItem | None = None
    last_recommendation: AdminLookupRecommendationItem | None = None


class AdminDriverCrsDiagnostic(BaseModel):
    """Why CRS might be 0: no participations, events missing classification, or CRS never computed."""
    driver_id: str
    primary_discipline: str
    participations_count: int = 0
    events_missing_classification: list[str] = []
    latest_crs_score: float | None = None
    latest_crs_discipline: str | None = None
    reason: str = ""


class AdminUserRead(BaseModel):
    id: str
    name: str
    email: str | None
    role: str
    active: bool
    created_at: datetime
    profile_id: str | None
    profile_completion_percent: int
    level: str
    driver_id: str | None

    model_config = {"from_attributes": True}


class AdminUserSearchRead(BaseModel):
    driver_id: str
    email: str | None
    primary_discipline: str | None
    sim_games: list[str] = []


class AdminParticipationSearchRead(BaseModel):
    driver_id: str
    driver_email: str | None
    primary_discipline: str | None
    sim_games: list[str] = []
    participations: list[ParticipationAdminRead] = []


class AdminParticipationSummary(BaseModel):
    id: str
    started_at: datetime | None


class AdminPlayerInspectRead(BaseModel):
    driver_id: str
    driver_email: str | None
    primary_discipline: str | None
    sim_games: list[str] = []
    participations: list[AdminParticipationSummary] = []


# --- Admin detail DTOs (event, participation, incident) ---


class AdminEventParticipationItem(BaseModel):
    id: str
    driver_id: str
    driver_name: str | None
    status: str
    position_overall: int | None
    laps_completed: int
    incidents_count: int
    started_at: datetime | None


class AdminEventDetailRead(BaseModel):
    event: EventRead
    classification: ClassificationRead | None = None
    participations: list[AdminEventParticipationItem] = []


class AdminParticipationDriverRef(BaseModel):
    id: str
    name: str
    primary_discipline: str
    sim_games: list[str] = []


class AdminParticipationEventRef(BaseModel):
    id: str
    title: str
    game: str | None


class AdminParticipationIncidentItem(BaseModel):
    id: str
    code: str | None = None
    score: float = 0.0
    incident_type: str
    severity: int
    lap: int | None
    description: str | None
    created_at: datetime | None


class AdminParticipationDetailRead(BaseModel):
    participation: ParticipationAdminRead  # has game from join
    driver: AdminParticipationDriverRef
    event: AdminParticipationEventRef
    incidents: list[AdminParticipationIncidentItem] = []


class AdminParticipationUpdate(BaseModel):
    """Partial update for participation (admin constructor / driver flow)."""
    status: str | None = None
    participation_state: str | None = None
    position_overall: int | None = None
    position_class: int | None = None
    laps_completed: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AdminIncidentParticipationRef(BaseModel):
    id: str
    driver_id: str
    event_id: str
    status: str
    started_at: datetime | None


class AdminIncidentEventRef(BaseModel):
    id: str
    title: str
    game: str | None


class AdminIncidentDriverRef(BaseModel):
    id: str
    name: str


class AdminIncidentRead(BaseModel):
    id: str
    participation_id: str
    code: str | None = None
    score: float = 0.0
    incident_type: str
    severity: int
    lap: int | None
    description: str | None
    created_at: datetime | None


class AdminIncidentDetailRead(BaseModel):
    incident: AdminIncidentRead
    participation: AdminIncidentParticipationRef
    event: AdminIncidentEventRef | None = None
    driver: AdminIncidentDriverRef | None = None


class TierProgressionRuleRead(BaseModel):
    tier: str
    min_events: int
    difficulty_threshold: float
    required_license_codes: list[str] = []

    model_config = {"from_attributes": True}


class TierProgressionRuleUpdate(BaseModel):
    min_events: int | None = None
    difficulty_threshold: float | None = None
    required_license_codes: list[str] | None = None


class AdminLicenseLevelRef(BaseModel):
    """License level reference (code + discipline) for task–license link."""
    level_code: str
    discipline: str


class AdminTaskDefinitionRead(BaseModel):
    """Task definition with which license levels require this task (by code)."""
    id: str
    code: str
    name: str
    discipline: str
    description: str
    requirements: dict = {}
    min_event_tier: str | None = None
    max_event_tier: str | None = None
    min_duration_minutes: float | None = None
    max_incidents: int | None = None
    max_penalties: int | None = None
    require_night: bool = False
    require_dynamic_weather: bool = False
    require_team_event: bool = False
    require_clean_finish: bool = False
    allow_non_finish: bool = False
    max_position_overall: int | None = None
    min_position_overall: int | None = None
    min_laps_completed: int | None = None
    repeatable: bool = False
    max_completions: int | None = None
    cooldown_hours: float | None = None
    diversity_window_days: int | None = None
    max_same_event_count: int | None = None
    require_event_diversity: bool | None = None
    max_same_signature_count: int | None = None
    signature_cooldown_hours: float | None = None
    diminishing_returns: bool = False
    diminishing_step: float | None = None
    diminishing_floor: float | None = None
    active: bool = True
    event_related: bool = True
    scope: str = "per_participation"
    cooldown_days: int | None = None
    period: str | None = None
    window_size: int | None = None
    window_unit: str | None = None
    created_at: datetime
    required_by_license_levels: list[AdminLicenseLevelRef] = []

    model_config = {"from_attributes": True}


class AdminClearUserRequest(BaseModel):
    email: str


class AdminClearUserResponse(BaseModel):
    licenses: int = 0
    task_completions: int = 0
    participations: int = 0

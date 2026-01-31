from datetime import datetime

from app.schemas.participation import ParticipationAdminRead

from pydantic import BaseModel


class AdminUserRead(BaseModel):
    id: str
    name: str
    email: str | None
    role: str
    active: bool
    created_at: datetime
    profile_id: str | None
    completion_percent: int
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

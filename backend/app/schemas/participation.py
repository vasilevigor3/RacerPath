from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class Discipline(str, Enum):
    formula = "formula"
    gt = "gt"
    rally = "rally"
    karting = "karting"
    historic = "historic"


class ParticipationStatus(str, Enum):
    finished = "finished"
    dnf = "dnf"
    dsq = "dsq"
    dns = "dns"


class ParticipationState(str, Enum):
    registered = "registered"
    withdrawn = "withdrawn"
    started = "started"
    completed = "completed"


class ParticipationCreate(BaseModel):
    driver_id: str
    event_id: str

    discipline: Discipline = Discipline.gt

    # Result status (what happened)
    status: ParticipationStatus = ParticipationStatus.finished

    # Lifecycle state (where we are in the process)
    participation_state: ParticipationState = ParticipationState.registered

    position_overall: int | None = Field(default=None, ge=0)
    position_class: int | None = Field(default=None, ge=0)

    laps_completed: int = Field(default=0, ge=0)
    incidents_count: int = Field(default=0, ge=0)
    penalties_count: int = Field(default=0, ge=0)

    pace_delta: float | None = None
    consistency_score: float | None = None

    raw_metrics: Dict[str, float | int | str] = Field(default_factory=dict)

    started_at: datetime | None = None
    finished_at: datetime | None = None


class ParticipationRead(ParticipationCreate):
    id: str
    duration_minutes: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParticipationAdminRead(ParticipationRead):
    game: str | None = None

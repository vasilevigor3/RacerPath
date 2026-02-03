from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Literal

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
    classification_id: str | None = None
    duration_minutes: int | None = None
    withdraw_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ParticipationWithEventRead(ParticipationRead):
    """Participation with event (race) info for list views."""
    event_title: str = ""
    event_start_time_utc: datetime | None = None


class ParticipationWithdrawUpdate(BaseModel):
    """Driver can only set participation_state to withdrawn (opt out of event)."""
    participation_state: Literal["withdrawn"] = "withdrawn"


class ActiveParticipationRead(ParticipationRead):
    """Current race: participation + event title for live stats display."""
    event_title: str | None = None


class ParticipationAdminRead(ParticipationRead):
    game: str | None = None

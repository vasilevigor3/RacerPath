"""Penalty schemas: create/read for penalty records."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.penalties.scores import ALLOWED_TIME_PENALTY_SECONDS


class PenaltyTypeEnum(str, Enum):
    time_penalty = "time_penalty"
    drive_through = "drive_through"
    stop_and_go = "stop_and_go"
    dsq = "dsq"


class PenaltyCreate(BaseModel):
    """Legacy: participation_id optional when creating via incident. Prefer POST /incidents/{id}/penalties."""
    participation_id: str | None = Field(default=None)
    incident_id: str | None = Field(default=None)  # required for create; penalty belongs to incident
    penalty_type: PenaltyTypeEnum
    score: float | None = Field(default=None, ge=0)  # UI only; if omitted, backend sets from PENALTY_TYPE_SCORES
    time_seconds: int | None = Field(default=None, ge=0)
    lap: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def time_required_and_allowed_for_time_penalty(self):
        if self.penalty_type != PenaltyTypeEnum.time_penalty:
            return self
        if self.time_seconds is None or self.time_seconds <= 0:
            raise ValueError("time_penalty requires time_seconds > 0")
        if self.time_seconds not in ALLOWED_TIME_PENALTY_SECONDS:
            raise ValueError(
                f"time_penalty time_seconds must be one of {sorted(ALLOWED_TIME_PENALTY_SECONDS)}, got {self.time_seconds}"
            )
        return self


class PenaltyCreateByIncident(BaseModel):
    """Create penalty for an incident; participation_id is taken from the incident."""
    penalty_type: PenaltyTypeEnum
    score: float | None = Field(default=None, ge=0)  # UI only; if omitted, backend sets from PENALTY_TYPE_SCORES
    time_seconds: int | None = Field(default=None, ge=0)
    lap: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def time_required_and_allowed_for_time_penalty(self):
        if self.penalty_type != PenaltyTypeEnum.time_penalty:
            return self
        if self.time_seconds is None or self.time_seconds <= 0:
            raise ValueError("time_penalty requires time_seconds > 0")
        if self.time_seconds not in ALLOWED_TIME_PENALTY_SECONDS:
            raise ValueError(
                f"time_penalty time_seconds must be one of {sorted(ALLOWED_TIME_PENALTY_SECONDS)}, got {self.time_seconds}"
            )
        return self


class PenaltyRead(PenaltyCreate):
    id: str
    created_at: datetime
    score: float | None = None  # UI/result only; CRS uses Incident.score

    model_config = {"from_attributes": True}


class PenaltyWithEventRead(PenaltyRead):
    """Penalty with event (race) info for list views."""
    event_id: str | None = None
    event_title: str = ""
    event_start_time_utc: datetime | None = None

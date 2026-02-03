from datetime import datetime

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class IncidentType(str, Enum):
    contact = "Contact"
    off_track = "Off-track"
    track_limits = "Track limits"
    unsafe_rejoin = "Unsafe rejoin"
    blocking = "Blocking"
    avoidable_contact = "Avoidable contact"
    mechanical = "Mechanical"
    other = "Other"


_INCIDENT_TYPE_MAP = {
    "contact": IncidentType.contact,
    "avoidablecontact": IncidentType.avoidable_contact,
    "offtrack": IncidentType.off_track,
    "tracklimits": IncidentType.track_limits,
    "unsaferejoin": IncidentType.unsafe_rejoin,
    "blocking": IncidentType.blocking,
    "mechanical": IncidentType.mechanical,
    "other": IncidentType.other,
}


def _normalize_incident_type(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


class IncidentCreate(BaseModel):
    participation_id: str
    code: str = Field(..., min_length=1, max_length=40)  # required; e.g. off_track, contact
    score: float = Field(default=0.0, ge=0)  # CRS deduction input
    incident_type: IncidentType
    severity: int = Field(default=1, ge=1, le=5)
    lap: int | None = Field(default=None, ge=0)
    timestamp_utc: datetime | None = None
    description: str | None = Field(default=None, max_length=240)

    @field_validator("incident_type", mode="before")
    @classmethod
    def normalize_incident_type(cls, value):
        if isinstance(value, IncidentType):
            return value
        if not isinstance(value, str):
            raise ValueError("Invalid incident type")
        key = _normalize_incident_type(value)
        mapped = _INCIDENT_TYPE_MAP.get(key)
        if not mapped:
            raise ValueError("Invalid incident type")
        return mapped


class IncidentRead(IncidentCreate):
    id: str
    code: str | None = None  # optional when loading legacy rows from DB
    score: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentWithEventRead(IncidentRead):
    """Incident with event (race) info for list views."""
    event_id: str | None = None
    event_title: str = ""
    event_start_time_utc: datetime | None = None
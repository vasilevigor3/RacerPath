from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class LicenseLevelCreate(BaseModel):
    discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=500)
    min_crs: float = Field(ge=0, le=100)
    required_task_codes: List[str] = Field(default_factory=list)
    active: bool = True


class LicenseLevelRead(LicenseLevelCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LicenseLevelUpdate(BaseModel):
    discipline: Literal["formula", "gt", "rally", "karting", "historic"] | None = None
    code: str | None = Field(None, min_length=2, max_length=40)
    name: str | None = Field(None, min_length=2, max_length=120)
    description: str | None = Field(None, min_length=2, max_length=500)
    min_crs: float | None = Field(None, ge=0, le=100)
    required_task_codes: List[str] | None = None
    active: bool | None = None


class DriverLicenseRead(BaseModel):
    id: str
    driver_id: str
    discipline: str
    level_code: str
    status: str
    awarded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class LicenseRequirementsRead(BaseModel):
    next_level: str | None = None
    requirements: List[str] = Field(default_factory=list)


class LicenseAwardCheckRead(BaseModel):
    """Admin: eligibility check result for award."""
    eligible: bool
    next_level_code: str | None = None
    reasons: List[str] = Field(default_factory=list)
    current_crs: float | None = None
    completed_task_codes: List[str] = Field(default_factory=list)
    required_task_codes: List[str] = Field(default_factory=list)


class LicenseAwardRequest(BaseModel):
    """Admin: award by driver_id or email."""
    driver_id: str | None = None
    email: str | None = None
    discipline: str

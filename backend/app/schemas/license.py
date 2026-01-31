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

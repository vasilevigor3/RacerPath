from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, Field


class CRSHistoryCreate(BaseModel):
    driver_id: str
    discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    score: float = Field(ge=0, le=100)
    inputs: Dict[str, float | int | str] = Field(default_factory=dict)
    computed_at: datetime | None = None


class CRSHistoryRead(CRSHistoryCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class RecommendationCreate(BaseModel):
    driver_id: str
    discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    readiness_status: Literal["ready", "almost_ready", "not_ready"]
    summary: str = Field(min_length=2, max_length=300)
    items: List[str] = Field(default_factory=list)


class RecommendationRead(RecommendationCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}

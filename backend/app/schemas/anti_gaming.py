from datetime import datetime
from typing import List

from pydantic import BaseModel


class AntiGamingReportRead(BaseModel):
    id: str
    driver_id: str
    discipline: str
    flags: List[str]
    multiplier: float
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel


class ClassificationRead(BaseModel):
    id: str
    event_id: str
    event_tier: str
    tier_label: str
    difficulty_score: float
    seriousness_score: float
    realism_score: float
    discipline_compatibility: Dict[str, int]
    caps_applied: List[str]
    classification_version: str
    inputs_hash: str
    inputs_snapshot: Dict[str, object]
    created_at: datetime

    model_config = {"from_attributes": True}

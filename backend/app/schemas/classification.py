from datetime import datetime
from typing import Dict, List, Any

from pydantic import BaseModel, Field


class ClassificationCreate(BaseModel):
    event_id: str
    event_tier: str = Field(min_length=1, max_length=10)
    tier_label: str = Field(min_length=1, max_length=40)
    difficulty_score: float = Field(ge=0, le=100)
    seriousness_score: float = Field(ge=0, le=100)
    realism_score: float = Field(ge=0, le=100)
    discipline_compatibility: Dict[str, int] = Field(default_factory=dict)
    caps_applied: List[str] = Field(default_factory=list)
    classification_version: str = Field(min_length=1, max_length=20)
    inputs_hash: str = Field(min_length=1, max_length=64)
    inputs_snapshot: Dict[str, Any] = Field(default_factory=dict)


class ClassificationUpdate(BaseModel):
    event_tier: str | None = Field(None, min_length=1, max_length=10)
    tier_label: str | None = Field(None, min_length=1, max_length=40)
    difficulty_score: float | None = Field(None, ge=0, le=100)
    seriousness_score: float | None = Field(None, ge=0, le=100)
    realism_score: float | None = Field(None, ge=0, le=100)
    discipline_compatibility: Dict[str, int] | None = None
    caps_applied: List[str] | None = None
    classification_version: str | None = Field(None, min_length=1, max_length=20)
    inputs_hash: str | None = Field(None, min_length=1, max_length=64)
    inputs_snapshot: Dict[str, Any] | None = None


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

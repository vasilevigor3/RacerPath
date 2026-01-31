from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class RawEventIngest(BaseModel):
    source: Literal["wss", "gridfinder", "iracing", "acc_league", "lfm", "sro_esports", "other"]
    source_event_id: str | None = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    create_event: bool = True


class RawEventRead(BaseModel):
    id: str
    source: str
    source_event_id: str | None
    payload: Dict[str, Any]
    normalized_event: Dict[str, Any] | None
    status: str
    errors: List[str]
    event_id: str | None
    created_at: datetime
    normalized_at: datetime | None

    model_config = {"from_attributes": True}
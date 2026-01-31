from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.event import Event
from app.models.raw_event import RawEvent
from app.services.classifier import build_event_payload, classify_event, infer_primary_discipline
from app.services.normalizer import normalize_raw_event


def ingest_payload(
    session: Session,
    source: str,
    payload: dict,
    create_event: bool = True,
    source_event_id: str | None = None,
) -> RawEvent:
    resolved_source_event_id = source_event_id or payload.get("id")
    if resolved_source_event_id:
        existing = (
            session.query(RawEvent)
            .filter(
                RawEvent.source == source,
                RawEvent.source_event_id == resolved_source_event_id,
            )
            .first()
        )
        if existing:
            return existing

    with session.begin():
        raw_event = RawEvent(
            source=source,
            source_event_id=resolved_source_event_id,
            payload=payload,
            status="pending",
        )
        session.add(raw_event)
        session.flush()

        normalized_event, errors = normalize_raw_event(source, payload)
        raw_event.normalized_event = normalized_event
        raw_event.errors = errors
        raw_event.normalized_at = datetime.utcnow()

        if normalized_event is None or "missing_title" in errors:
            raw_event.status = "failed"
            return raw_event

        raw_event.status = "normalized"

        if create_event:
            event = Event(**normalized_event)
            session.add(event)
            session.flush()

            discipline = infer_primary_discipline(event.event_type, event.car_class_list, "gt")
            classification_payload = build_event_payload(event, discipline)
            classification_data = classify_event(classification_payload)

            classification = Classification(event_id=event.id, **classification_data)
            session.add(classification)
            raw_event.event_id = event.id
            raw_event.status = "classified"

    session.refresh(raw_event)
    return raw_event

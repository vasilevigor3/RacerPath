import json
import hashlib

from fastapi import APIRouter, Depends, Request

from app.schemas.classify import ClassificationRequest
from app.services.classifier import classify_event
from app.services.auth import require_user

router = APIRouter(prefix="/classify", tags=["classification"])


def cache_key(payload: dict) -> str:
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    return f"classify:{hashlib.sha256(payload_bytes).hexdigest()}"


def get_redis(request: Request):
    return getattr(request.app.state, "redis", None)


@router.post("")
def classify(payload: ClassificationRequest, redis=Depends(get_redis), _=Depends(require_user())):
    data = payload.model_dump()
    key = cache_key(data)

    if redis:
        cached = redis.get(key)
        if cached:
            return json.loads(cached)

    result = classify_event(data)

    if redis:
        try:
            redis.setex(key, 3600, json.dumps(result))
        except Exception:
            pass

    return result
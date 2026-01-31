from __future__ import annotations

import json
import urllib.request
from typing import Any


def fetch_json(url: str, api_key: str | None = None, timeout: int = 20) -> Any:
    headers = {"User-Agent": "RacerPath/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def extract_events(data: Any) -> list[dict]:
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict) and isinstance(data.get("events"), list):
        events = data.get("events", [])
    else:
        raise ValueError("Unsupported payload shape: expected list or {events: [...]}")
    return [event for event in events if isinstance(event, dict)]

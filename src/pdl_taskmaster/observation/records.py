from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import hashlib
import json


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_text(payload)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_events(workspace: Any) -> list[dict[str, Any]]:
    """The active turn's events (turns/<id>/events/events.jsonl in a session workspace)."""
    if workspace is None:
        return []
    return workspace.read_events()


def turn_key(workspace: Any) -> tuple[str, str | None] | None:
    """Which turn's event log read_events reads, so a delta never spans two turns."""
    return None if workspace is None else (str(workspace.path), workspace.turn_id)


def controller_snapshot(engine: Any) -> dict[str, Any] | None:
    if engine is None or engine.controller is None:
        return None
    return {
        "controller_state": engine.controller.state.to_dict(),
        "workspace_id": engine.workspace.metadata.get("workspace_id") if engine.workspace is not None else None,
        "workspace_path": str(engine.workspace.path) if engine.workspace is not None else None,
    }


def event_delta(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> dict[str, Any]:
    if len(after) >= len(before):
        new_events = after[len(before):]
    else:
        new_events = after
    return {
        "before_count": len(before),
        "after_count": len(after),
        "new": [
            {"at_utc": event.get("at_utc"), "kind": event.get("kind"), "payload": event.get("payload")}
            for event in new_events
        ],
    }

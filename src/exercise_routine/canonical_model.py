"""Canonical internal routine model (import + manual converge here)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def normalize_routine(routine: dict[str, Any]) -> dict[str, Any]:
    """Ensure sessions[] shape; preserve blocks[] + live_tracking (AD-005)."""
    out = deepcopy(routine) if routine else {}
    sessions = out.get("sessions")
    if isinstance(sessions, list) and sessions:
        out["sessions"] = [
            _normalize_session(s, idx) for idx, s in enumerate(sessions)
        ]
        out.pop("exercises", None)
        if "live_tracking" in out and out["live_tracking"] is None:
            out.pop("live_tracking", None)
        return out

    exercises = out.get("exercises") or []
    out["sessions"] = [
        {
            "id": "session-1",
            "name": "Session 1",
            "order": 1,
            "exercises": list(exercises),
            "blocks": [],
        }
    ]
    out.pop("exercises", None)
    return out


def _normalize_session(session: dict[str, Any], idx: int) -> dict[str, Any]:
    s = dict(session or {})
    s.setdefault("id", f"session-{idx + 1}")
    s.setdefault("name", f"Session {idx + 1}")
    s.setdefault("order", idx + 1)
    s["exercises"] = list(s.get("exercises") or [])
    blocks = list(s.get("blocks") or [])
    s["blocks"] = [_normalize_block(b, bidx) for bidx, b in enumerate(blocks)]
    return s


def _normalize_block(block: dict[str, Any], idx: int) -> dict[str, Any]:
    b = dict(block or {})
    b.setdefault("id", f"block-{idx + 1}")
    b.setdefault("name", f"Block {idx + 1}")
    b.setdefault("order", idx + 1)
    b.setdefault("type", "sequence")
    b.setdefault("rounds", 1)
    b["exercises"] = list(b.get("exercises") or [])
    return b


def exercise_count(routine: dict[str, Any]) -> int:
    norm = normalize_routine(routine)
    total = 0
    for session in norm.get("sessions") or []:
        blocks = session.get("blocks") or []
        if blocks:
            total += sum(len(b.get("exercises") or []) for b in blocks)
        else:
            total += len(session.get("exercises") or [])
    return total


def sorted_sessions(routine: dict[str, Any]) -> list[dict[str, Any]]:
    norm = normalize_routine(routine)
    sessions = list(norm.get("sessions") or [])
    return sorted(sessions, key=lambda s: int(s.get("order") or 0))


def flatten_session_for_runner(
    routine: dict[str, Any], session_id: str | None = None
) -> dict[str, Any]:
    """Return runner-shaped routine for one session; keep blocks when present."""
    norm = normalize_routine(routine)
    sessions = sorted_sessions(norm)
    if not sessions:
        return {
            "id": norm.get("id"),
            "name": norm.get("name") or "Routine",
            "exercises": [],
            "blocks": [],
            "source": norm.get("source"),
            "live_tracking": norm.get("live_tracking"),
            "sessions": [],
        }
    chosen = None
    if session_id:
        chosen = next((s for s in sessions if s.get("id") == session_id), None)
    if chosen is None:
        chosen = sessions[0]
    blocks = list(chosen.get("blocks") or [])
    exercises = list(chosen.get("exercises") or [])
    return {
        "id": norm.get("id"),
        "name": norm.get("name") or "Routine",
        "source": norm.get("source"),
        "import_schema_version": norm.get("import_schema_version"),
        "live_tracking": norm.get("live_tracking"),
        "session_id": chosen.get("id"),
        "session_name": chosen.get("name"),
        "exercises": exercises,
        "blocks": blocks,
        "sessions": sessions,
    }


def with_active_session_exercises(
    routine: dict[str, Any], exercises: list[dict[str, Any]], session_id: str | None = None
) -> dict[str, Any]:
    """Write exercise list back into the chosen (or first) session."""
    norm = normalize_routine(routine)
    sessions = list(norm.get("sessions") or [])
    if not sessions:
        sessions = [
            {
                "id": "session-1",
                "name": "Session 1",
                "order": 1,
                "exercises": exercises,
                "blocks": [],
            }
        ]
    else:
        target_idx = 0
        if session_id:
            for i, s in enumerate(sessions):
                if s.get("id") == session_id:
                    target_idx = i
                    break
        sessions[target_idx] = dict(sessions[target_idx])
        sessions[target_idx]["exercises"] = exercises
    norm["sessions"] = sessions
    norm.pop("exercises", None)
    return norm

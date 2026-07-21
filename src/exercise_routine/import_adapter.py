"""Map validated import DTO → canonical internal routine model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from exercise_routine.canonical_model import normalize_routine


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if item is not None)
    return str(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]


def _map_metric(metric: dict[str, Any]) -> dict[str, Any]:
    kind = metric.get("kind")
    reps = None
    duration_seconds = None
    min_reps = metric.get("min_reps")
    max_reps = metric.get("max_reps")
    if kind in ("reps", "reps_per_side"):
        reps = int(metric["reps"]) if metric.get("reps") is not None else None
    elif kind in ("duration", "duration_per_side"):
        duration_seconds = (
            int(metric["duration_seconds"])
            if metric.get("duration_seconds") is not None
            else None
        )
    elif kind == "rep_range":
        if min_reps is not None:
            min_reps = int(min_reps)
        if max_reps is not None:
            max_reps = int(max_reps)
        # Display midpoint / max as reps target for flat runners
        if max_reps is not None:
            reps = int(max_reps)
    return {
        "metric_kind": kind,
        "reps": reps,
        "duration_seconds": duration_seconds,
        "min_reps": min_reps,
        "max_reps": max_reps,
        "stop_rule": metric.get("stop_rule"),
    }


def _map_exercise(ex: dict[str, Any]) -> dict[str, Any]:
    metric = _map_metric(ex.get("metric") or {})
    transition = ex.get("transition_seconds")
    visual_ref = ex.get("visual_ref")
    instructions = ex.get("instructions") or _as_text(ex.get("execution_instructions"))
    return {
        "id": ex.get("id"),
        "name": ex.get("name"),
        "order": ex.get("order"),
        "sets": int(ex["sets"]) if ex.get("sets") is not None else 1,
        "duration_seconds": metric["duration_seconds"],
        "reps": metric["reps"],
        "metric_kind": metric["metric_kind"],
        "min_reps": metric["min_reps"],
        "max_reps": metric["max_reps"],
        "stop_rule": metric["stop_rule"],
        "rest_seconds": int(ex.get("rest_seconds") or 0),
        "transition_seconds": int(transition) if transition is not None else None,
        "instructions": instructions,
        "execution_instructions": _as_list(ex.get("execution_instructions")),
        "visual_url": visual_ref if visual_ref else None,
        "laterality": ex.get("laterality"),
        "side_sequence": list(ex.get("side_sequence") or []),
        "equipment": list(ex.get("equipment") or []),
        "load": deepcopy(ex.get("load")) if ex.get("load") is not None else None,
        "setup": deepcopy(ex.get("setup")) if ex.get("setup") is not None else None,
        "tempo": ex.get("tempo"),
        "technical_notes": _as_list(ex.get("technical_notes"))
        if isinstance(ex.get("technical_notes"), list)
        else (_as_text(ex.get("technical_notes")) if ex.get("technical_notes") else ""),
        "common_errors": list(ex.get("common_errors") or []),
        "pain_adaptation": ex.get("pain_adaptation") or "",
        "alternatives": list(ex.get("alternatives") or []),
    }


def _map_block(block: dict[str, Any]) -> dict[str, Any]:
    exercises = [_map_exercise(ex) for ex in (block.get("exercises") or [])]
    exercises.sort(key=lambda e: int(e.get("order") or 0))
    return {
        "id": block.get("id"),
        "name": block.get("name"),
        "order": int(block.get("order") or 0),
        "type": block.get("type"),
        "rounds": int(block["rounds"]) if block.get("rounds") is not None else 1,
        "rest_between_rounds_seconds": (
            int(block["rest_between_rounds_seconds"])
            if block.get("rest_between_rounds_seconds") is not None
            else None
        ),
        "transition_after_block_seconds": (
            int(block["transition_after_block_seconds"])
            if block.get("transition_after_block_seconds") is not None
            else None
        ),
        "estimated_duration_seconds": block.get("estimated_duration_seconds"),
        "exercises": exercises,
    }


def _map_session(session: dict[str, Any]) -> dict[str, Any]:
    blocks = [_map_block(b) for b in (session.get("blocks") or [])]
    blocks.sort(key=lambda b: int(b.get("order") or 0))
    exercises = [_map_exercise(ex) for ex in (session.get("exercises") or [])]
    exercises.sort(key=lambda e: int(e.get("order") or 0))
    out: dict[str, Any] = {
        "id": session.get("id"),
        "name": session.get("name"),
        "order": int(session.get("order") or 0),
        "description": session.get("description") or "",
        "approx_duration_minutes": session.get("approx_duration_minutes"),
        "reserved_duration_minutes": session.get("reserved_duration_minutes"),
        "session_type": session.get("session_type"),
        "target_rpe": session.get("target_rpe"),
        "completion_rule": session.get("completion_rule"),
        "exercises": exercises,
        "blocks": blocks,
    }
    # Keep check-in payload stored but unused in UI (AD-012)
    if "post_session_checkin" in session:
        out["post_session_checkin"] = deepcopy(session["post_session_checkin"])
    return out


def _map_live_tracking(live: dict[str, Any] | None) -> dict[str, Any] | None:
    if not live:
        return None
    prefs = live.get("display_preferences") or {}
    return {
        "countdown_before_start_seconds": live.get("countdown_before_start_seconds"),
        "auto_start_next_step": live.get("auto_start_next_step"),
        "allow_skip_step": live.get("allow_skip_step"),
        "allow_pause": live.get("allow_pause"),
        "allow_extend_rest": live.get("allow_extend_rest"),
        "rest_extension_increment_seconds": live.get(
            "rest_extension_increment_seconds"
        ),
        "audio_cues": deepcopy(live.get("audio_cues"))
        if live.get("audio_cues") is not None
        else None,
        "display_preferences": {
            "large_primary_numbers": prefs.get("large_primary_numbers"),
            "show_current_set": prefs.get("show_current_set"),
            "show_total_sets": prefs.get("show_total_sets"),
            "show_next_exercise": prefs.get("show_next_exercise"),
            "show_load": prefs.get("show_load"),
            "show_side": prefs.get("show_side"),
            "show_block_progress": prefs.get("show_block_progress"),
            "show_elapsed_time": prefs.get("show_elapsed_time"),
            "show_estimated_time_remaining": prefs.get(
                "show_estimated_time_remaining"
            ),
        },
    }


def adapt_import_document(document: dict[str, Any]) -> dict[str, Any]:
    """sessions[] → CanonicalRoutine; blocks + live_tracking preserved (AD-005)."""
    routine = deepcopy(document.get("routine") or {})
    sessions = [_map_session(s) for s in (routine.get("sessions") or [])]
    sessions.sort(key=lambda s: int(s.get("order") or 0))

    metadata: dict[str, Any] = {}
    for key in (
        "goal",
        "description",
        "level",
        "estimated_duration_minutes",
        "reserved_duration_minutes",
        "frequency",
        "equipment_required",
        "general_notes",
        "non_medical_warnings",
    ):
        if key in routine:
            metadata[key] = routine[key]

    canonical = {
        "id": routine.get("id"),
        "name": routine.get("name"),
        "source": "import",
        "import_schema_version": document.get("schema_version"),
        "metadata": metadata or None,
        "live_tracking": _map_live_tracking(routine.get("live_tracking")),
        "sessions": sessions,
        "updated_at": None,
    }
    return normalize_routine(canonical)


def allocate_copy_id(existing_id: str, taken_ids: set[str]) -> str:
    """New id for Import as copy when collision (never silent overwrite)."""
    base = f"{existing_id}-copy"
    candidate = base
    n = 2
    while candidate in taken_ids:
        candidate = f"{base}-{n}"
        n += 1
    return candidate


def resolve_id_collision(
    canonical: dict[str, Any],
    library_ids: set[str],
    *,
    choice: str,
) -> dict[str, Any]:
    """
    choice: 'replace' | 'copy'
    Raises ValueError if id exists and choice is missing/invalid.
    """
    out = deepcopy(canonical)
    rid = out.get("id")
    if rid not in library_ids:
        return out
    if choice == "replace":
        return out
    if choice == "copy":
        out["id"] = allocate_copy_id(str(rid), library_ids)
        return out
    raise ValueError(
        "Routine id already exists — choose Replace or Import as copy "
        f"(id={rid})."
    )

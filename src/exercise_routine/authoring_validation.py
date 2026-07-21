"""Dual-metric exercise validation (AC-007, AC-008, U-01)."""

from __future__ import annotations

from typing import Any


def exercise_has_metric(exercise: dict[str, Any]) -> bool:
    """True when duration seconds > 0 and/or reps > 0."""
    duration = exercise.get("duration_seconds")
    reps = exercise.get("reps")
    has_duration = duration is not None and int(duration) > 0
    has_reps = reps is not None and int(reps) > 0
    return has_duration or has_reps


def validate_routine_for_session(routine: dict[str, Any]) -> tuple[bool, list[str]]:
    """Fail-soft check before guided start — both metrics missing on any exercise."""
    errors: list[str] = []
    exercises = routine.get("exercises") or []
    if not exercises:
        errors.append("Routine has no exercises.")
        return False, errors
    for idx, ex in enumerate(exercises):
        name = (ex.get("name") or f"Exercise {idx + 1}").strip() or f"Exercise {idx + 1}"
        if not exercise_has_metric(ex):
            errors.append(
                f"{name}: add a duration and/or reps target before starting a session."
            )
    return len(errors) == 0, errors


def duration_owns_done(exercise: dict[str, Any]) -> bool:
    """U-01: when both set, duration drives done; reps are display target only."""
    duration = exercise.get("duration_seconds")
    reps = exercise.get("reps")
    has_duration = duration is not None and int(duration) > 0
    has_reps = reps is not None and int(reps) > 0
    if has_duration and has_reps:
        return True
    return has_duration

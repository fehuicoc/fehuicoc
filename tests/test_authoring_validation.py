from exercise_routine.authoring_validation import (
    duration_owns_done,
    exercise_has_metric,
    validate_routine_for_session,
)


def test_duration_and_reps_equally_supported():
    assert exercise_has_metric({"duration_seconds": 30, "reps": None})
    assert exercise_has_metric({"duration_seconds": None, "reps": 12})
    assert exercise_has_metric({"duration_seconds": 45, "reps": 10})
    assert not exercise_has_metric({"duration_seconds": 0, "reps": 0})


def test_fail_soft_both_metrics_missing():
    ok, errors = validate_routine_for_session(
        {"exercises": [{"name": "Plank", "duration_seconds": None, "reps": None}]}
    )
    assert ok is False
    assert errors
    assert "duration" in errors[0].lower() or "reps" in errors[0].lower()


def test_u01_duration_owns_done_when_both_set():
    assert duration_owns_done({"duration_seconds": 40, "reps": 12}) is True
    assert duration_owns_done({"duration_seconds": None, "reps": 12}) is False

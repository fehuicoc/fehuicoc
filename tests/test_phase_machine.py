from exercise_routine.phase_machine import (
    DEFAULT_TRANSITION_SECONDS,
    build_timeline,
    progress_caption,
)


def test_transition_default_fixed():
    assert DEFAULT_TRANSITION_SECONDS == 5


def test_timeline_includes_exercise_rest_transition():
    routine = {
        "exercises": [
            {
                "name": "Squat",
                "duration_seconds": 40,
                "reps": 10,
                "rest_seconds": 20,
                "sets": 1,
            },
            {
                "name": "Push-up",
                "duration_seconds": 0,
                "reps": 8,
                "rest_seconds": 0,
                "sets": 1,
            },
        ]
    }
    steps = build_timeline(routine)
    kinds = [s["kind"] for s in steps]
    assert "exercise" in kinds
    assert "rest" in kinds
    assert "transition" in kinds
    assert steps[0]["owns_done"] == "duration"
    assert any(s["kind"] == "transition" and s["duration_seconds"] == 5 for s in steps)


def test_transition_override_honors_per_exercise():
    routine = {
        "exercises": [
            {
                "name": "A",
                "duration_seconds": 10,
                "reps": None,
                "rest_seconds": 0,
                "sets": 1,
                "transition_seconds": 12,
            },
            {
                "name": "B",
                "duration_seconds": 10,
                "reps": None,
                "rest_seconds": 0,
                "sets": 1,
            },
        ]
    }
    steps = build_timeline(routine)
    transitions = [s for s in steps if s["kind"] == "transition"]
    assert transitions
    assert transitions[0]["duration_seconds"] == 12


def test_duration_imported_timeout_owns_done():
    routine = {
        "exercises": [
            {
                "name": "Hold",
                "duration_seconds": 40,
                "reps": None,
                "rest_seconds": 0,
                "sets": 1,
            }
        ]
    }
    steps = build_timeline(routine)
    assert steps[0]["owns_done"] == "duration"
    assert steps[0]["duration_seconds"] == 40


def test_paired_sets_round_wise_alternation():
    routine = {
        "blocks": [
            {
                "id": "pair",
                "name": "Pair",
                "order": 1,
                "type": "paired_sets",
                "rounds": 2,
                "rest_between_rounds_seconds": 30,
                "exercises": [
                    {
                        "id": "a",
                        "name": "A",
                        "order": 1,
                        "sets": 2,
                        "reps": 10,
                        "rest_seconds": 10,
                        "transition_seconds": 5,
                    },
                    {
                        "id": "b",
                        "name": "B",
                        "order": 2,
                        "sets": 2,
                        "reps": 8,
                        "rest_seconds": 30,
                        "transition_seconds": 5,
                    },
                ],
            }
        ]
    }
    steps = build_timeline(routine)
    work = [s for s in steps if s["kind"] == "exercise"]
    assert [s["name"] for s in work] == ["A", "B", "A", "B"]


def test_both_sides_each_set_before_rest():
    routine = {
        "blocks": [
            {
                "id": "bi",
                "name": "Bi",
                "order": 1,
                "type": "straight_sets_bilateral",
                "rounds": 1,
                "exercises": [
                    {
                        "id": "march",
                        "name": "March",
                        "order": 1,
                        "sets": 1,
                        "duration_seconds": 20,
                        "metric_kind": "duration_per_side",
                        "laterality": "both_sides_each_set",
                        "side_sequence": ["left", "right"],
                        "rest_seconds": 40,
                        "transition_seconds": 0,
                    }
                ],
            }
        ]
    }
    steps = build_timeline(routine)
    assert steps[0]["side"] == "left"
    assert steps[1]["side"] == "right"
    assert steps[0]["kind"] == "exercise"
    assert steps[1]["kind"] == "exercise"
    # No rest between sides; rest only after both when more work follows —
    # single exercise last block: no trailing rest
    assert all(s["kind"] != "rest" or i > 1 for i, s in enumerate(steps))


def test_circuit_timeline_expansion():
    routine = {
        "blocks": [
            {
                "id": "c",
                "name": "Circuit",
                "order": 1,
                "type": "circuit",
                "rounds": 2,
                "rest_between_rounds_seconds": 15,
                "exercises": [
                    {
                        "id": "x",
                        "name": "X",
                        "order": 1,
                        "sets": 1,
                        "reps": 5,
                        "rest_seconds": 0,
                        "transition_seconds": 0,
                    },
                    {
                        "id": "y",
                        "name": "Y",
                        "order": 2,
                        "sets": 1,
                        "reps": 5,
                        "rest_seconds": 0,
                        "transition_seconds": 0,
                    },
                ],
            }
        ]
    }
    steps = build_timeline(routine)
    work = [s for s in steps if s["kind"] == "exercise"]
    assert len(work) == 4
    rests = [s for s in steps if s["kind"] == "rest"]
    assert any(s["duration_seconds"] == 15 for s in rests)
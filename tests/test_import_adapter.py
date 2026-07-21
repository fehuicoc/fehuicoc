"""Unit tests for import_adapter + canonical normalize (AD-001–AD-003, AD-018)."""

from __future__ import annotations

import json
from pathlib import Path

from exercise_routine.canonical_model import (
    flatten_session_for_runner,
    normalize_routine,
)
from exercise_routine.import_adapter import (
    adapt_import_document,
    resolve_id_collision,
)
from exercise_routine.phase_machine import build_timeline

FIXTURES = Path(__file__).parent / "fixtures"


def _doc():
    return json.loads((FIXTURES / "example_valid_routine.json").read_text(encoding="utf-8"))


def test_adapter_auto_create_canonical():
    canonical = adapt_import_document(_doc())
    assert canonical["id"] == "ex-full-body-a"
    assert canonical["source"] == "import"
    assert len(canonical["sessions"]) == 2


def test_adapter_multi_session_order_exercise_order():
    canonical = adapt_import_document(_doc())
    sessions = canonical["sessions"]
    assert [s["order"] for s in sessions] == [1, 2]
    assert sessions[0]["id"] == "day-1"
    assert [e["name"] for e in sessions[0]["exercises"]] == [
        "Goblet squat",
        "Plank hold",
    ]
    assert sessions[1]["exercises"][0]["name"] == "Dumbbell row"


def test_adapter_reps_map_sets_map():
    canonical = adapt_import_document(_doc())
    squat = canonical["sessions"][0]["exercises"][0]
    assert squat["reps"] == 10
    assert squat["duration_seconds"] is None
    assert squat["sets"] == 3


def test_adapter_duration_map_rest_seconds():
    canonical = adapt_import_document(_doc())
    plank = canonical["sessions"][0]["exercises"][1]
    assert plank["duration_seconds"] == 40
    assert plank["reps"] is None
    assert plank["rest_seconds"] == 45


def test_adapter_visual_ref_maps_to_visual_url():
    doc = _doc()
    doc["routine"]["sessions"][0]["exercises"][0]["visual_ref"] = "https://example.com/squat.png"
    canonical = adapt_import_document(doc)
    assert (
        canonical["sessions"][0]["exercises"][0]["visual_url"]
        == "https://example.com/squat.png"
    )


def test_legacy_normalize_flat_to_sessions():
    legacy = {
        "id": "old-1",
        "name": "Legacy",
        "exercises": [{"name": "A", "reps": 5, "duration_seconds": None}],
    }
    norm = normalize_routine(legacy)
    assert "exercises" not in norm or not norm.get("exercises")
    assert len(norm["sessions"]) == 1
    assert norm["sessions"][0]["exercises"][0]["name"] == "A"


def test_id_collision_replace_or_copy():
    canonical = adapt_import_document(_doc())
    taken = {canonical["id"]}
    replaced = resolve_id_collision(canonical, taken, choice="replace")
    assert replaced["id"] == canonical["id"]
    copied = resolve_id_collision(canonical, taken, choice="copy")
    assert copied["id"] != canonical["id"]
    assert copied["id"] not in taken or copied["id"].endswith("-copy")


def test_multi_day_flatten_session_order():
    canonical = adapt_import_document(_doc())
    day2 = flatten_session_for_runner(canonical, "day-2")
    assert day2["session_id"] == "day-2"
    assert len(day2["exercises"]) == 1
    assert day2["exercises"][0]["name"] == "Dumbbell row"


def test_transition_override_and_rest_imported_in_timeline():
    canonical = adapt_import_document(_doc())
    flat = flatten_session_for_runner(canonical, "day-1")
    steps = build_timeline(flat)
    transitions = [s for s in steps if s["kind"] == "transition"]
    assert any(s["duration_seconds"] == 10 for s in transitions)
    rests = [s for s in steps if s["kind"] == "rest"]
    assert any(s["duration_seconds"] == 60 for s in rests)

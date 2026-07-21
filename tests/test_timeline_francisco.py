"""Francisco Semana 6 Día 1 timeline authority (AD-006, AD-011)."""

from __future__ import annotations

import json
from pathlib import Path

from exercise_routine.canonical_model import flatten_session_for_runner
from exercise_routine.import_adapter import adapt_import_document
from exercise_routine.phase_machine import build_timeline

FIXTURES = Path(__file__).parent / "fixtures"
FRANCISCO = FIXTURES / "francisco_semana6_dia1_webapp_v2.json"


def _francisco_runner():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    return flatten_session_for_runner(canonical, "week6-day1")


def test_francisco_timeline_has_all_block_types():
    steps = build_timeline(_francisco_runner())
    assert steps
    kinds = {s["kind"] for s in steps}
    assert "exercise" in kinds
    assert "rest" in kinds
    block_types = {s.get("block_type") for s in steps if s.get("block_type")}
    assert "circuit" in block_types
    assert "paired_sets" in block_types
    assert "straight_sets" in block_types
    assert "straight_sets_bilateral" in block_types
    assert "sequence" in block_types


def test_francisco_paired_sets_round_wise_alternation():
    steps = build_timeline(_francisco_runner())
    block_b = [
        s
        for s in steps
        if s.get("block_id") == "block-b-squat-press" and s["kind"] == "exercise"
    ]
    names = [s["name"] for s in block_b]
    # Round-wise A then B: squat, press, squat, press, ...
    assert "Sentadilla frontal con dos mancuernas" in names[0]
    assert "Press inclinado con agarre neutro" in names[1]
    assert "Sentadilla frontal con dos mancuernas" in names[2]
    assert names[0].count("Sentadilla") >= 1
    # Must not be all squats then all presses
    first_half_squats = all("Sentadilla" in n for n in names[:3])
    assert not first_half_squats


def test_francisco_both_sides_before_rest():
    steps = build_timeline(_francisco_runner())
    # Supported single-leg RDL: left then right then rest
    rdl_idx = next(
        i
        for i, s in enumerate(steps)
        if s.get("exercise_id") == "supported-single-leg-rdl"
        and s["kind"] == "exercise"
        and s.get("side") == "left"
        and s.get("set") == 1
    )
    assert steps[rdl_idx]["side"] == "left"
    assert steps[rdl_idx + 1]["kind"] == "exercise"
    assert steps[rdl_idx + 1]["side"] == "right"
    assert steps[rdl_idx + 1]["exercise_id"] == "supported-single-leg-rdl"
    # Rest must not appear between left and right
    assert steps[rdl_idx + 1]["kind"] != "rest"
    after = steps[rdl_idx + 2]
    assert after["kind"] in ("rest", "transition", "exercise")


def test_francisco_suitcase_march_bilateral_before_rest():
    steps = build_timeline(_francisco_runner())
    idx = next(
        i
        for i, s in enumerate(steps)
        if s.get("exercise_id") == "suitcase-march"
        and s["kind"] == "exercise"
        and s.get("side") == "left"
        and s.get("set") == 1
    )
    assert steps[idx + 1]["side"] == "right"
    assert steps[idx + 1]["kind"] == "exercise"
    assert steps[idx + 2]["kind"] == "rest"


def test_francisco_circuit_rest_between_rounds():
    steps = build_timeline(_francisco_runner())
    warmup_rests = [
        s
        for s in steps
        if s.get("block_id") == "warmup"
        and s["kind"] == "rest"
        and s.get("duration_seconds") == 20
    ]
    assert warmup_rests, "circuit rest_between_rounds_seconds=20 expected"

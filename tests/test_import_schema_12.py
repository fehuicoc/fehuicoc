"""Schema 1.2 import acceptance (AD-001–AD-004, AD-010, AD-011)."""

from __future__ import annotations

import json
from pathlib import Path

from exercise_routine.import_adapter import adapt_import_document
from exercise_routine.import_validate import validate_bytes

FIXTURES = Path(__file__).parent / "fixtures"
FRANCISCO = FIXTURES / "francisco_semana6_dia1_webapp_v2.json"


def test_schema_12_francisco_import_accepts_blocks():
    raw = FRANCISCO.read_bytes()
    result = validate_bytes(raw, filename="francisco_semana6_dia1_webapp_v2.json")
    assert result.ok, result.errors
    assert result.preview is not None
    assert result.preview["schema_version"] == "1.2"
    assert result.preview["sessions"][0]["block_count"] == 6
    types = [b["type"] for b in result.preview["sessions"][0]["blocks"]]
    assert "circuit" in types
    assert "straight_sets" in types
    assert "paired_sets" in types
    assert "straight_sets_bilateral" in types
    assert "sequence" in types


def test_schema_12_blocks_metrics_laterality():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    result = validate_bytes(
        json.dumps(doc).encode("utf-8"),
        filename="francisco.json",
    )
    assert result.ok, result.errors
    warmup = doc["routine"]["sessions"][0]["blocks"][0]["exercises"]
    kinds = {ex["metric"]["kind"] for ex in warmup}
    assert "reps_per_side" in kinds
    pull = doc["routine"]["sessions"][0]["blocks"][1]["exercises"][0]
    assert pull["metric"]["kind"] == "rep_range"
    rdl = doc["routine"]["sessions"][0]["blocks"][3]["exercises"][0]
    assert rdl["laterality"] == "both_sides_each_set"
    assert rdl["side_sequence"] == ["left", "right"]


def test_schema_12_notes_level_advanced_recreational():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    assert doc["routine"]["level"] == "advanced_recreational"
    assert isinstance(doc["routine"]["general_notes"], list)
    result = validate_bytes(
        json.dumps(doc).encode("utf-8"), filename="francisco.json"
    )
    assert result.ok, result.errors


def test_flat_1_0_1_1_still_valid():
    raw = (FIXTURES / "example_valid_routine.json").read_bytes()
    result = validate_bytes(raw, filename="example_valid_routine.json")
    assert result.ok, result.errors
    assert result.preview["schema_version"] in ("1.0", "1.1")


def test_francisco_live_tracking_preview():
    result = validate_bytes(
        FRANCISCO.read_bytes(), filename="francisco_semana6_dia1_webapp_v2.json"
    )
    assert result.ok
    live = result.preview["live_tracking"]
    assert live["countdown_before_start_seconds"] == 10
    assert live["allow_extend_rest"] is True
    assert live["rest_extension_increment_seconds"] == 15


def test_adapt_francisco_preserves_blocks():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    session = canonical["sessions"][0]
    assert len(session["blocks"]) == 6
    assert session["exercises"] == []
    assert canonical["live_tracking"]["countdown_before_start_seconds"] == 10

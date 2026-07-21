"""Canonical blocks + live_tracking round-trip (AD-004, AD-005)."""

from __future__ import annotations

import json
from pathlib import Path

from exercise_routine.canonical_model import (
    exercise_count,
    flatten_session_for_runner,
    normalize_routine,
)
from exercise_routine.import_adapter import adapt_import_document

FIXTURES = Path(__file__).parent / "fixtures"
FRANCISCO = FIXTURES / "francisco_semana6_dia1_webapp_v2.json"


def test_canonical_blocks_round_trip():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    norm = normalize_routine(canonical)
    blocks = norm["sessions"][0]["blocks"]
    assert blocks[0]["type"] == "circuit"
    assert blocks[2]["type"] == "paired_sets"
    assert blocks[2]["rounds"] == 3
    assert blocks[3]["exercises"][0]["side_sequence"] == ["left", "right"]
    assert blocks[3]["exercises"][0]["load"]["value"] == 8


def test_live_tracking_countdown_extend_rest():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    live = canonical["live_tracking"]
    assert live["countdown_before_start_seconds"] == 10
    assert live["allow_extend_rest"] is True
    assert live["rest_extension_increment_seconds"] == 15
    prefs = live["display_preferences"]
    assert prefs["show_block_progress"] is True
    assert prefs["show_side"] is True
    assert prefs["show_load"] is True


def test_flatten_runner_keeps_blocks_and_live_tracking():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    flat = flatten_session_for_runner(canonical, "week6-day1")
    assert len(flat["blocks"]) == 6
    assert flat["live_tracking"]["countdown_before_start_seconds"] == 10
    assert exercise_count(canonical) >= 10


def test_post_session_checkin_stored_not_required_for_runner():
    doc = json.loads(FRANCISCO.read_text(encoding="utf-8"))
    canonical = adapt_import_document(doc)
    assert "post_session_checkin" in canonical["sessions"][0]
    flat = flatten_session_for_runner(canonical)
    assert flat["blocks"]

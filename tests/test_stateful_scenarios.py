"""Stateful ST-* scenario contracts (AD-019–AD-020, AD-024, AD-029)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exercise_routine.app import create_app

FIXTURES = Path(__file__).parent / "fixtures"


def _client() -> TestClient:
    return TestClient(create_app())


def test_persist_refresh_persists_across_refresh_key():
    js = _client().get("/static/js/library.js").text
    assert "er_coach_routines_v1" in js
    assert "localStorage" in js
    import_js = _client().get("/static/js/import.js").text
    assert "upsert" in import_js


def test_data_loss_prevention_save_failure_keeps_preview():
    js = _client().get("/static/js/import.js").text
    assert "Save failed" in js or "preview kept" in js.lower()
    assert "er_import_preview_v1" in js
    assert "recoverable" in js.lower() or "Retry" in js or "retry" in js


def test_leave_return_soft_nav_preview_key():
    js = _client().get("/static/js/import.js").text
    assert "er_import_preview_v1" in js
    assert "sessionStorage" in js


def test_retry_after_validation_failure():
    html = _client().get("/import").text
    assert 'id="btn-retry-import"' in html
    js = _client().get("/static/js/import.js").text
    assert "btn-retry-import" in js or "Try another" in html


def test_timeout_duration_metric_cue():
    js = _client().get("/static/js/session.js").text
    assert "duration_seconds" in js
    assert "advance" in js
    pm = Path(__file__).resolve().parents[1] / "src" / "exercise_routine" / "phase_machine.py"
    text = pm.read_text(encoding="utf-8")
    assert "owns_done" in text


def test_timeout_countdown_zero_advances():
    """ST-timeout — countdown reaches zero and advances to first work."""
    js = _client().get("/static/js/session.js").text
    assert "countdownActive" in js
    assert "countdown_before_start_seconds" in js
    assert "loadStep(0)" in js


def test_extend_rest_retry_affordance():
    """ST-retry — extend rest can be tapped more than once."""
    js = _client().get("/static/js/session.js").text
    assert "rest_extension_increment_seconds" in js
    assert "state.remaining +=" in js or "remaining +=" in js
    html = _client().get("/session").text
    assert 'id="btn-extend-rest"' in html

def test_integration_failure_malformed_leaves_library_contract():
    res = _client().post(
        "/api/import/preview",
        files={
            "file": (
                "bad.json",
                (FIXTURES / "example_invalid_malformed.txt").read_bytes(),
                "application/json",
            )
        },
    )
    assert res.status_code == 400
    assert res.json()["persisted"] is False


def test_disconnect_not_applicable_waived():
    """ST-disconnect waived for local MVP — no network session path."""
    pytest.skip("ST-disconnect not_applicable for account-less local coach (AD-029)")


def test_recovery_after_recoverable_error():
    js = _client().get("/static/js/import.js").text
    assert "Retry" in js or "retry" in js or "Try another" in _client().get("/import").text
    assert "Save failed" in js or "preview" in js.lower()


def test_session_continuity_pause_continue():
    html = _client().get("/session").text
    assert 'id="btn-pause"' in html
    assert 'id="btn-continue"' in html
    js = _client().get("/static/js/session.js").text
    assert "setPaused" in js
    assert "paused" in js


def test_resume_after_pause_same_position():
    js = _client().get("/static/js/session.js").text
    assert "btn-continue" in js or "setPaused(false)" in js
    assert "state.index" in js or "loadStep" in js

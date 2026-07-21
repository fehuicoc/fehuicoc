"""SC-001 session panel contracts (AD-021..AD-023)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from exercise_routine.app import create_app

SRC = Path(__file__).resolve().parents[1] / "src" / "exercise_routine"


def _client() -> TestClient:
    return TestClient(create_app())


def _session_html() -> str:
    return _client().get("/session").text


def _session_js() -> str:
    return (SRC / "static" / "js" / "session.js").read_text(encoding="utf-8")


def _visuals_js() -> str:
    return (SRC / "static" / "js" / "visuals.js").read_text(encoding="utf-8")


def _coach_css() -> str:
    return (SRC / "static" / "css" / "coach.css").read_text(encoding="utf-8")


# --- AD-021 ---


def test_sc001_instructions_panel_replaces_visual_coming_soon():
    html = _session_html()
    assert 'id="visual-panel"' in html
    assert "visual-panel--instructions" in html
    assert "instructions-panel" in html
    assert "Current step instructions" in html
    assert "Visual coming soon" not in html
    # F-001: no dual hidden #instructions slot on guided stage
    assert 'id="instructions"' not in html
    visuals = _visuals_js()
    assert "Visual coming soon" not in visuals
    assert "step-instructions-text" in visuals
    assert "Current step instructions" in visuals
    assert "instructions-panel" in visuals


def test_sc001_instructions_prefer_execution_instructions():
    js = _session_js()
    assert "resolveExerciseInstructions" in js
    assert "execution_instructions" in js
    assert "technical_notes" in js
    assert 'getElementById("instructions")' not in js


def test_sc001_panel_overflow_clamp_bounds():
    css = _coach_css()
    assert "visual-panel--instructions" in css
    assert "max-height" in css
    assert "overflow-y: auto" in css or "overflow-y:auto" in css
    assert "clamp(" in css
    assert "step-instructions-text" in css
    # F-001: no cyan media-placeholder chrome; glance-large above 18px floor
    assert "#ecfeff" not in css
    assert "min-height: 140px" not in css
    assert "clamp(1.375rem" in css or "clamp(1.375rem," in css


# --- AD-022 ---


def test_sc001_total_timer_at_top():
    html = _session_html()
    assert 'id="session-total-bar"' in html
    assert 'id="total-elapsed"' in html
    assert "TOTAL" in html
    # TOTAL chrome appears before progress strip in markup
    assert html.index("session-total-bar") < html.index("progress-glance")


def test_sc001_total_elapsed_starts_after_countdown():
    js = _session_js()
    assert "ensureTotalStarted" in js
    assert "totalRunning" in js
    assert "totalElapsed" in js
    assert "countdownActive" in js
    # TOTAL must not run during countdown
    assert "if (state.totalRunning || state.countdownActive) return" in js
    assert "ensureTotalStarted()" in js


def test_sc001_strip_with_total_option_1():
    html = _session_html()
    assert 'id="progress-glance"' in html
    assert 'id="session-total-bar"' in html
    assert "session-sidebar" not in html
    css = _coach_css()
    assert "session-total-bar" in css
    assert "session-total-value" in css


# --- AD-023 ---


def test_sc001_pause_step_only_total_keeps_running():
    js = _session_js()
    assert "totalRunning" in js
    # TOTAL advances before paused early-return
    tick_idx = js.index("function tick()")
    paused_idx = js.index("if (state.paused) return", tick_idx)
    total_adv_idx = js.index("state.totalElapsed", tick_idx)
    assert total_adv_idx < paused_idx
    assert "setPaused" in js
    assert "btnPause" in js


def test_sc001_pause_controls_regression():
    html = _session_html()
    assert 'id="btn-pause"' in html
    assert 'id="btn-continue"' in html
    assert 'id="btn-end"' in html
    js = _session_js()
    assert "stopTotal" in js
    assert "finish(" in js

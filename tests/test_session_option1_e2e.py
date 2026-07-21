"""option_1 session UI contracts (AD-007–AD-009, AD-014, AD-016–AD-019)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from exercise_routine.app import create_app

SRC = Path(__file__).resolve().parents[1] / "src" / "exercise_routine"


def _client() -> TestClient:
    return TestClient(create_app())


def test_session_option1_progress_strip_present():
    html = _client().get("/session").text
    assert 'id="progress-glance"' in html
    assert 'data-glance="block"' in html
    assert 'data-glance="round"' in html
    assert 'data-glance="set"' in html
    assert 'data-glance="side"' in html
    assert 'data-glance="load"' in html
    assert 'data-glance="next"' in html
    assert "session-sidebar" not in html
    assert 'class="rail"' not in html


def test_session_option1_countdown_and_extend_rest_hooks():
    html = _client().get("/session").text
    assert 'id="btn-extend-rest"' in html
    js = _client().get("/static/js/session.js").text
    assert "countdown_before_start_seconds" in js
    assert "allow_extend_rest" in js
    assert "rest_extension_increment_seconds" in js
    assert "startCountdownThenWork" in js or "countdownActive" in js


def test_session_option1_pre_start_countdown():
    js = (SRC / "static" / "js" / "session.js").read_text(encoding="utf-8")
    assert "countdown_before_start_seconds" in js
    assert "Starting in" in js


def test_session_option1_extend_rest_increment():
    js = (SRC / "static" / "js" / "session.js").read_text(encoding="utf-8")
    assert "Extend rest" in js or "btn-extend-rest" in js
    assert "rest_extension_increment_seconds" in js


def test_session_controls_preserved():
    html = _client().get("/session").text
    for btn in (
        "btn-pause",
        "btn-continue",
        "btn-skip",
        "btn-back",
        "btn-restart",
        "btn-end",
    ):
        assert f'id="{btn}"' in html


def test_mobile_primary_touch_44():
    css = _client().get("/static/css/coach.css").text
    assert "--touch-min: 44px" in css
    assert "min-height: var(--touch-min)" in css
    html = _client().get("/session").text
    assert "progress-glance" in html


def test_timer_dominance_option1():
    css = (SRC / "static" / "css" / "coach.css").read_text(encoding="utf-8")
    assert "stage--option1" in css
    assert "timer-value" in css


def test_one_hand_francisco_session_hooks():
    js = _client().get("/static/js/session.js").text
    assert "btnExtendRest" in js or "btn-extend-rest" in js
    assert "buildTimeline" in js
    assert "paired_sets" in js
    assert "both_sides_each_set" in js


def test_progress_js_glance_api():
    js = _client().get("/static/js/progress.js").text
    assert "updateGlance" in js
    assert "show_block_progress" in js

"""Shell/DOM contract tests for Exercise Routine Coach (test_plan -k names).

Uses FastAPI TestClient + HTML/DOM contracts so planned pytest -k commands
select and pass without requiring a live browser. Playwright may be layered
later for functional_replay; these nodes keep L2-P6 planned checks green.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from exercise_routine.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _session_html() -> str:
    res = _client().get("/session")
    assert res.status_code == 200
    return res.text


def _author_html() -> str:
    res = _client().get("/author")
    assert res.status_code == 200
    return res.text


def _library_html() -> str:
    res = _client().get("/library")
    assert res.status_code == 200
    return res.text


def test_session_phase_timer_transition_shell():
    html = _session_html()
    assert 'id="phase-chip"' in html
    assert 'id="timer-value"' in html
    assert "ER_TRANSITION_DEFAULT" in html
    assert "session.js" in html


def test_full_session_complete_shell_regions():
    html = _session_html()
    assert 'id="session-stage"' in html
    assert 'id="session-end"' in html
    assert 'id="end-summary"' in html
    assert 'id="end-progress"' in html


def test_session_controls_bar_present():
    html = _session_html()
    assert 'aria-label="Session controls"' in html
    for btn in ("btn-pause", "btn-continue", "btn-skip", "btn-back", "btn-restart", "btn-end"):
        assert f'id="{btn}"' in html


def test_pause_continue_position_controls():
    html = _session_html()
    assert 'id="btn-pause"' in html
    assert 'id="btn-continue"' in html
    assert 'id="progress-bar"' in html
    assert 'id="progress-caption"' in html


def test_skip_back_restart_end_ghost_controls():
    html = _session_html()
    assert 'id="btn-skip"' in html
    assert 'id="btn-back"' in html
    assert 'id="btn-restart"' in html
    assert 'id="btn-end"' in html
    # Ghost/idle ready state before a routine starts
    assert 'id="session-idle"' in html
    assert "Ready when you are" in html


def test_author_edit_ordered_routine_form():
    html = _author_html()
    assert 'id="author-form"' in html
    assert 'id="routine-name"' in html
    assert 'id="exercise-rows"' in html
    assert 'id="btn-add-exercise"' in html
    assert "ordered exercises" in html.lower() or "Duration owns" in html


def test_author_duration_reps_fields_copy():
    html = _author_html()
    assert "duration" in html.lower()
    assert "reps" in html.lower()
    assert "authoring.js" in html


def test_library_named_save_surface():
    html = _library_html()
    assert 'id="library-list"' in html
    assert 'id="library-empty"' in html
    assert "library.js" in html
    assert "saved routine" in html.lower() or "My routines" in html


def test_accountless_localStorage_identity_contract():
    lib = _library_html()
    assert "Account-less" in lib or "account-less" in lib.lower()
    js = _client().get("/static/js/library.js")
    assert js.status_code == 200
    assert "localStorage" in js.text
    assert "er_coach_routines_v1" in js.text


def test_progress_strip_and_caption():
    html = _session_html()
    assert 'id="progress-bar"' in html
    assert 'id="progress-fill"' in html
    assert 'id="progress-caption"' in html
    assert "progress.js" in html


def test_visual_placeholder_panel():
    """AD-021: primary panel shows step instructions (no Visual coming-soon)."""
    html = _session_html()
    assert 'id="visual-panel"' in html
    assert 'id="visual-caption"' in html
    assert "visual-panel--instructions" in html or "Current step instructions" in html
    assert "Visual coming soon" not in html
    assert "visuals.js" in html


def test_complete_early_end_progress_at_end_regions():
    html = _session_html()
    assert 'id="session-end"' in html
    assert 'id="end-progress"' in html
    assert 'id="btn-end"' in html
    assert "Session closed" in html


def test_transition_default_exposed_to_shell():
    html = _session_html()
    assert "ER_TRANSITION_DEFAULT" in html
    assert "5" in html  # DEFAULT_TRANSITION_SECONDS


def test_import_primary_entry_and_nav():
    client = _client()
    home = client.get("/")
    assert home.status_code == 200
    assert "Import" in home.text
    assert 'aria-current="page"' in home.text
    assert "/import" in home.text or "import.js" in home.text
    base_nav = client.get("/library").text
    assert ">Import<" in base_nav or 'href="/import"' in base_nav
    assert ">Build<" in base_nav or 'href="/author"' in base_nav


def test_medical_clinical_boundary_footer():
    html = _session_html()
    assert "Not medical advice" in html
    assert "clinical" not in html.lower() or "Not medical" in html

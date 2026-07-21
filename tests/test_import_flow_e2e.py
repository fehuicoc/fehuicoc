"""Import flow e2e (shell/DOM + API) — AD-001, AD-013–AD-016, AD-030."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from exercise_routine.app import create_app

FIXTURES = Path(__file__).parent / "fixtures"


def _client() -> TestClient:
    return TestClient(create_app())


def test_import_happy_confirm_import_upsert_path():
    client = _client()
    home = client.get("/")
    assert home.status_code == 200
    assert "Import routine" in home.text
    assert 'id="import-dropzone"' in home.text
    assert 'id="btn-confirm-import"' in home.text
    assert "import.js" in home.text

    preview = client.post(
        "/api/import/preview",
        files={
            "file": (
                "ok.json",
                (FIXTURES / "example_valid_routine.json").read_bytes(),
                "application/json",
            )
        },
    )
    assert preview.status_code == 200
    data = preview.json()
    assert data["ok"] is True
    assert data["persisted"] is False
    assert data["canonical"]["id"] == "ex-full-body-a"
    # Persist is client-side; API never writes library (auto_create via confirm UX)
    assert data["preview"]["persisted"] is False


def test_import_invalid_file_negative_import():
    client = _client()
    res = client.post(
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
    body = res.json()
    assert body["ok"] is False
    assert body["canonical"] is None
    assert body["persisted"] is False


def test_cancel_import_cancel_clears_contract():
    html = _client().get("/import").text
    assert 'id="btn-cancel-import"' in html
    js = _client().get("/static/js/import.js").text
    assert "er_import_preview_v1" in js
    assert "clearPreviewStore" in js or "removeItem" in js
    assert "Confirm import" in html or "btn-confirm-import" in html


def test_preview_before_persist_ui_and_api():
    client = _client()
    html = client.get("/import").text
    assert 'id="import-preview"' in html
    assert "not saved yet" in html.lower() or "Preview" in html
    res = client.post(
        "/api/import/preview",
        files={
            "file": (
                "ok.json",
                (FIXTURES / "example_valid_routine.json").read_bytes(),
                "application/json",
            )
        },
    )
    assert res.json()["persisted"] is False


def test_edit_imported_author_edit_leave_return_links():
    client = _client()
    author = client.get("/author").text
    assert 'id="author-form"' in author
    import_js = client.get("/static/js/import.js").text
    assert "/author?id=" in import_js
    lib = client.get("/library").text
    assert "Edit" in lib or "author?id=" in client.get("/static/js/library.js").text


def test_multi_day_day_picker_shell():
    client = _client()
    session = client.get("/session").text
    assert 'id="session-day-picker"' in session
    assert 'id="session-day-select"' in session
    lib_js = client.get("/static/js/library.js").text
    assert "session-picker" in lib_js or "sortedSessions" in lib_js
    assert "flattenForRunner" in lib_js


def test_reps_imported_duration_imported_execute_exercise_shell():
    session = _client().get("/session").text
    assert "session.js" in session
    assert 'id="btn-pause"' in session
    js = _client().get("/static/js/session.js").text
    assert "buildTimeline" in js
    assert "reps" in js
    assert "duration_seconds" in js


def test_single_runner_start_session_controls():
    client = _client()
    html = client.get("/session").text
    assert 'aria-label="Session controls"' in html
    assert html.count("session.js") == 1
    # No second engine script
    assert "session2.js" not in html
    assert "runner-alt" not in html


def test_full_session_complete_end_session_regions():
    html = _client().get("/session").text
    assert 'id="session-end"' in html
    assert 'id="btn-end"' in html
    assert "Session closed" in html or "Session complete" in html


def test_save_failure_keeps_preview_contract():
    js = _client().get("/static/js/import.js").text
    assert "Save failed" in js or "preview kept" in js.lower()
    assert "er_import_preview_v1" in js


def test_persists_across_refresh_storage_key():
    js = _client().get("/static/js/library.js").text
    assert "er_coach_routines_v1" in js
    assert "localStorage" in js

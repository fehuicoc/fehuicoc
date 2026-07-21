"""Unit tests for import_validate (AD-007–AD-014 gates)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from exercise_routine.app import create_app
from exercise_routine.import_validate import MAX_FILE_BYTES, validate_bytes

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_valid_preview_before_persist():
    raw = _load("example_valid_routine.json")
    result = validate_bytes(raw, filename="example_valid_routine.json")
    assert result.ok
    assert result.preview is not None
    assert result.preview["persisted"] is False
    assert result.preview["name"] == "Full Body A"
    assert result.preview["session_count"] == 2


def test_optional_absent_warnings_only():
    doc = json.loads(_load("example_valid_routine.json"))
    # Strip optional fields
    for key in (
        "goal",
        "description",
        "level",
        "estimated_duration_minutes",
        "frequency",
        "equipment_required",
        "general_notes",
        "non_medical_warnings",
    ):
        doc["routine"].pop(key, None)
    for session in doc["routine"]["sessions"]:
        for ex in session["exercises"]:
            ex.pop("visual_ref", None)
            ex.pop("technical_notes", None)
            ex.pop("alternatives", None)
            ex.pop("equipment", None)
            ex.pop("laterality", None)
    raw = json.dumps(doc).encode("utf-8")
    result = validate_bytes(raw, filename="partial.json")
    assert result.ok
    assert result.warnings
    assert any("Optional" in w or "visual_ref" in w for w in result.warnings)


def test_missing_required_validation_error():
    raw = _load("example_invalid_missing_required.json")
    result = validate_bytes(raw, filename="bad.json")
    assert not result.ok
    assert result.errors
    assert result.document is None


def test_malformed_invalid_json_no_partial():
    raw = _load("example_invalid_malformed.txt")
    result = validate_bytes(raw, filename="broken.json")
    assert not result.ok
    assert any("Malformed" in e or "JSON" in e for e in result.errors)


def test_schema_version_incompatible_version():
    raw = _load("example_invalid_version.json")
    result = validate_bytes(raw, filename="v2.json")
    assert not result.ok
    assert any("schema_version" in e.lower() or "Incompatible" in e for e in result.errors)


def test_oversize_size_limit_max_file():
    raw = b'{"format_id":"exercise-routine-coach"}' + (b"x" * (MAX_FILE_BYTES + 10))
    result = validate_bytes(raw, filename="big.json")
    assert not result.ok
    assert any("size" in e.lower() or "limit" in e.lower() for e in result.errors)


def test_extension_disallowed_ext_bad_extension():
    raw = _load("example_valid_routine.json")
    result = validate_bytes(raw, filename="routine.exe")
    assert not result.ok
    assert any("extension" in e.lower() for e in result.errors)


def test_preview_api_rejects_invalid_and_accepts_valid():
    client = TestClient(create_app())
    bad = client.post(
        "/api/import/preview",
        files={
            "file": (
                "bad.json",
                _load("example_invalid_missing_required.json"),
                "application/json",
            )
        },
    )
    assert bad.status_code == 400
    body = bad.json()
    assert body["ok"] is False
    assert body["persisted"] is False

    good = client.post(
        "/api/import/preview",
        files={
            "file": (
                "ok.json",
                _load("example_valid_routine.json"),
                "application/json",
            )
        },
    )
    assert good.status_code == 200
    g = good.json()
    assert g["ok"] is True
    assert g["persisted"] is False
    assert g["preview"]["name"] == "Full Body A"
    assert g["canonical"]["source"] == "import"

"""Pack 3 integration env parity probes for local /health controlled_target.

Covers: simulate (offline mock), live GET :8765 when server up, negative :18765.
No secrets; no corporate hosts. CBRA surface: health probe tests only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

EXPECTED_HEALTH = {"status": "ok", "service": "exercise-routine"}
LIVE_URL = "http://127.0.0.1:8765/health"
NEGATIVE_URL = "http://127.0.0.1:18765/health"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_mock_path() -> Path:
    return (
        _repo_root()
        / "Factory_v3"
        / "runs"
        / "exercise-routine-002-change"
        / "layer2"
        / "integration_contracts"
        / "mocks"
        / "er-health-response.json"
    )


def test_simulate_health_mock_shape():
    """Offline mock matches declared /health JSON (simulate row)."""
    mock_path = Path(os.environ.get("ER_HEALTH_MOCK_PATH", str(_default_mock_path())))
    assert mock_path.is_file(), f"simulate mock missing: {mock_path}"
    body = json.loads(mock_path.read_text(encoding="utf-8"))
    assert body == EXPECTED_HEALTH


def test_live_health_positive_when_server_up():
    """Live GET http://127.0.0.1:8765/health — skip if process not listening."""
    require_live = os.environ.get("ER_REQUIRE_LIVE_HEALTH", "").strip() in ("1", "true", "yes")
    try:
        with urllib.request.urlopen(LIVE_URL, timeout=2) as resp:
            status = resp.getcode()
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if require_live:
            pytest.fail(f"live health required but unreachable: {exc}")
        pytest.skip(f"live server not up on 8765: {exc}")

    assert status == 200
    assert json.loads(raw) == EXPECTED_HEALTH


def test_negative_wrong_port_unreachable():
    """Wrong port 18765 must be unreachable (pass_unreachable)."""
    with pytest.raises((urllib.error.URLError, TimeoutError, OSError)):
        urllib.request.urlopen(NEGATIVE_URL, timeout=2)

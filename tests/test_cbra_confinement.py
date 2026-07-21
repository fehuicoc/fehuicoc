"""CBRA confinement — retargeted to exercise-routine-001-change (AD-026)."""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "Factory_v3" / "runs" / "exercise-routine-001-change"
WORKSPACE = REPO / "generated-solutions" / "exercise-routine"
BLAST = RUN / "layer2" / "blast_radius.yaml"

SIBLINGS = (
    "generated-solutions/device-pricing/",
    "generated-solutions/pos-m1/",
    "generated-solutions/hotfix-tools/",
    "generated-solutions/pos-m2/",
)


def _blast():
    return yaml.safe_load(BLAST.read_text(encoding="utf-8"))


def test_approved_surface_hosts_coach_under_exercise_routine_only():
    data = _blast()
    assert data["run_id"] == "exercise-routine-001-change"
    for surface in data["approved_surface"]:
        for p in surface["paths"]:
            assert p.startswith("generated-solutions/exercise-routine/"), p
            for sib in SIBLINGS:
                assert not p.startswith(sib.rstrip("/")), p


def test_preserved_siblings_declared():
    """AD-026 — sibling product modules stay out of approved_surface."""
    data = _blast()
    approved = [
        p for s in data["approved_surface"] for p in s["paths"]
    ]
    for sib in (
        "generated-solutions/device-pricing/",
        "generated-solutions/pos-m1/",
        "generated-solutions/hotfix-tools/",
    ):
        assert not any(p.startswith(sib.rstrip("/")) for p in approved)
    # Workspace isolation: no sibling trees under this coach package
    assert not (WORKSPACE / "src" / "device_pricing").exists()
    assert not (WORKSPACE / "src" / "pos_m1").exists()


def test_no_silent_sibling_indirect_consumer():
    data = _blast()
    for c in data.get("consumers") or []:
        surfaces = " ".join(c.get("surfaces") or []).lower()
        assert "device-pricing" not in surfaces
        assert "pos-m" not in surfaces
        assert "hotfix" not in surfaces
        assert "amc" not in surfaces


def test_coach_src_exists_under_workspace():
    assert (WORKSPACE / "src" / "exercise_routine" / "app.py").is_file()
    assert (WORKSPACE / "src" / "exercise_routine" / "import_validate.py").is_file()
    assert (WORKSPACE / "src" / "exercise_routine" / "import_adapter.py").is_file()
    for path in (WORKSPACE / "src" / "exercise_routine").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "device_pricing" not in text
        assert "pos_m1" not in text
        assert "hotfix_tools" not in text

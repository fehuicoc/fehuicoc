"""UX acceptance matrix binding checks (AD-027–AD-029)."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
RUN = REPO / "Factory_v3" / "runs" / "exercise-routine-001-change"
MATRIX = RUN / "layer2" / "ux" / "UX_ACCEPTANCE_MATRIX.yaml"
TEST_PLAN = RUN / "layer2" / "test_plan.yaml"


def _matrix():
    return yaml.safe_load(MATRIX.read_text(encoding="utf-8"))


def _plan():
    return yaml.safe_load(TEST_PLAN.read_text(encoding="utf-8"))


def test_matrix_authority_ready_for_apply():
    data = _matrix()
    assert data.get("status") == "ready_for_apply"
    assert data.get("run_id") == "exercise-routine-001-change"
    assert MATRIX.is_file()


def test_row_id_only_in_test_plan_citations():
    plan = _plan()
    for mapping in plan.get("mappings") or []:
        for check in mapping.get("planned_checks") or []:
            for rid in check.get("matrix_row_ids") or []:
                assert str(rid).startswith("UXR-"), rid


def test_role_routine_owner_declared():
    data = _matrix()
    roles = data.get("roles") or data.get("operator_roles") or []
    text = MATRIX.read_text(encoding="utf-8")
    assert (
        "routine_owner" in text
        or "ROLE-routine_owner" in text
        or any("routine_owner" in str(r).lower() for r in roles)
    )


def test_flows_coverage_applicability():
    text = MATRIX.read_text(encoding="utf-8")
    assert "FLOW-" in text or "flow_id" in text
    assert "applicable" in text or "not_applicable" in text


def test_stateful_profile_mandatory_scenario_pack():
    data = _matrix()
    text = MATRIX.read_text(encoding="utf-8")
    assert "stateful" in text.lower() or data.get("stateful_profile")
    for token in (
        "ST-persist-refresh",
        "ST-leave-return",
        "ST-retry",
        "ST-resume",
    ):
        assert token in text
    # ST-disconnect waived / N/A documented
    assert "ST-disconnect" in text

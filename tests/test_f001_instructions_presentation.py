"""F-001 AD-021 presentation: primary instructions surface + hardened checks."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from exercise_routine.app import create_app
from f001_panel_contracts import (
    FORBIDDEN_MEDIA_CHROME_MARKERS,
    FRANCISCO_SQUAT_CUE_SUBSTRINGS,
    MIN_OWNER_GRADE_FONT_PX,
    SHALLOW_FALSE_PASS_FONT_PX,
    owner_grade_panel_passes,
    shallow_fr_er003_observation,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "exercise_routine"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FRANCISCO = FIXTURES / "francisco_semana6_dia1_webapp_v2.json"


def _client() -> TestClient:
    return TestClient(create_app())


def _session_html() -> str:
    return _client().get("/session").text


def _session_stage_html() -> str:
    html = _session_html()
    start = html.index('id="session-stage"')
    end = html.index('id="session-day-picker"')
    return html[start:end]


def _coach_css() -> str:
    return (SRC / "static" / "css" / "coach.css").read_text(encoding="utf-8")


def _session_js() -> str:
    return (SRC / "static" / "js" / "session.js").read_text(encoding="utf-8")


def _visuals_js() -> str:
    return (SRC / "static" / "js" / "visuals.js").read_text(encoding="utf-8")


def _clamp_min_rem(css: str) -> float:
    m = re.search(
        r"\.step-instructions-text\s*\{[^}]*font-size:\s*clamp\(\s*([\d.]+)rem",
        css,
        re.S,
    )
    assert m, "step-instructions-text clamp() floor missing"
    return float(m.group(1))


# --- CHK-F001-PRIMARY-VISIBLE ---


def test_f001_primary_visible_instructions_surface():
    """Primary instructions surface sits above meta/reps; glance-primary chrome."""
    stage = _session_stage_html()
    assert 'id="visual-panel"' in stage
    assert "instructions-panel" in stage
    assert "Current step instructions" in stage
    # Instructions before compact reps meta (not subordinate under reps-only chrome)
    assert stage.index("visual-panel") < stage.index("meta-row")
    css = _coach_css()
    assert "instructions-panel" in css
    rem = _clamp_min_rem(css)
    assert rem * 16 > SHALLOW_FALSE_PASS_FONT_PX
    assert rem * 16 >= MIN_OWNER_GRADE_FONT_PX


def test_primary_instructions_surface_not_caption_under_media():
    css = _coach_css()
    # Must not use the old caption-sized 1.125rem floor
    assert "clamp(1.125rem" not in css
    assert "font-weight: 600" in css or "font-weight:600" in css


def test_glance_primary_panel_order_and_aria():
    stage = _session_stage_html()
    assert stage.index("timer-block") < stage.index("visual-panel")
    assert 'aria-label="Current step instructions"' in stage


# --- CHK-F001-NO-MEDIA-CHROME ---


def test_f001_no_media_chrome_residual():
    css = _coach_css()
    html = _session_html()
    visuals = _visuals_js()
    block = _visual_panel_block(css)
    for marker in FORBIDDEN_MEDIA_CHROME_MARKERS:
        assert marker not in block, f"media chrome residual in panel CSS: {marker}"
        assert marker not in html
        assert marker not in visuals
    assert "min-height: 140px" not in css
    assert "#ecfeff" not in css
    assert "linear-gradient" not in block


def test_no_visual_placeholder_chrome():
    css = _coach_css()
    block = _visual_panel_block(css)
    assert "linear-gradient" not in block
    assert "var(--color-surface)" in block
    assert "Visual coming soon" not in _visuals_js()


def test_no_cyan_media_box():
    css = _coach_css()
    block = _visual_panel_block(css)
    assert "#ecfeff" not in css
    assert "#f0f9ff" not in block


def _visual_panel_block(css: str) -> str:
    m = re.search(r"\.visual-panel\s*,\s*\.instructions-panel\s*\{[^}]+\}", css, re.S)
    if not m:
        m = re.search(r"\.visual-panel\s*\{[^}]+\}", css, re.S)
    assert m, "visual-panel rule missing"
    return m.group(0)


# --- CHK-F001-NO-DUAL-SLOT ---


def test_f001_no_dual_slot_hidden_instructions():
    stage = _session_stage_html()
    assert 'id="instructions"' not in stage
    assert "instructions--secondary" not in stage
    js = _session_js()
    assert 'getElementById("instructions")' not in js
    assert "ui.instructions" not in js


def test_no_hidden_instructions_slot():
    html = _session_html()
    # Dual slot id retired from guided stage; idle/day copy may still use class only
    assert re.search(r'id=["\']instructions["\']', html) is None


def test_single_instructions_surface():
    stage = _session_stage_html()
    assert stage.count('id="visual-panel"') == 1
    assert stage.count("step-instructions-text") >= 1
    assert 'id="instructions"' not in stage


# --- CHK-F001-FIXTURE-CUES-GLANCE ---


def test_f001_fixture_cues_wired_to_primary_panel():
    js = _session_js()
    assert "resolveExerciseInstructions" in js
    assert "execution_instructions" in js
    raw = FRANCISCO.read_text(encoding="utf-8")
    for cue in FRANCISCO_SQUAT_CUE_SUBSTRINGS:
        assert cue in raw
    visuals = _visuals_js()
    assert "step-instructions-text" in visuals
    assert "renderVisual" in visuals


def test_francisco_squat_cues_present_in_fixture():
    raw = FRANCISCO.read_text(encoding="utf-8")
    assert "Pies al ancho cómodo" in raw
    assert "rodillas alineadas" in raw


def test_glance_large_type_above_shallow_18px():
    css = _coach_css()
    rem = _clamp_min_rem(css)
    px = rem * 16
    assert px > SHALLOW_FALSE_PASS_FONT_PX
    assert px >= MIN_OWNER_GRADE_FONT_PX
    text_block = re.search(
        r"\.step-instructions-text\s*\{[^}]+\}", css, re.S
    )
    assert text_block
    assert "1.125rem" not in text_block.group(0)
    assert "1.375rem" in text_block.group(0)


# --- CHK-F001-FR-HARDENED ---


def test_f001_fr_hardened_rejects_shallow_observation():
    """Would fail FR-ER003-OBSERVED shallow nonblank+18px alone."""
    shallow = shallow_fr_er003_observation()
    assert shallow["instructions_nonblank"] is True
    assert shallow["instructions_font_px"] == SHALLOW_FALSE_PASS_FONT_PX
    assert owner_grade_panel_passes(shallow) is False


def test_fr_instructions_owner_grade_accepts_fixed_observation():
    fixed = {
        "primary_visible": True,
        "instructions_nonblank": True,
        "instructions_font_px": 22,
        "has_media_chrome": False,
        "has_dual_instructions_slot": False,
        "fixture_cues_present": True,
    }
    assert owner_grade_panel_passes(fixed) is True


def test_sc001_fr_panel_hard_source_matches_owner_grade():
    """Source/CSS after Apply must satisfy the same hardened FR contract."""
    css = _coach_css()
    stage = _session_stage_html()
    rem = _clamp_min_rem(css)
    obs = {
        "primary_visible": "instructions-panel" in stage
        and stage.index("visual-panel") < stage.index("meta-row"),
        "instructions_nonblank": True,
        "instructions_font_px": rem * 16,
        "has_media_chrome": any(m in css for m in ("#ecfeff", "min-height: 140px")),
        "has_dual_instructions_slot": 'id="instructions"' in stage,
        "fixture_cues_present": all(
            c in FRANCISCO.read_text(encoding="utf-8")
            for c in FRANCISCO_SQUAT_CUE_SUBSTRINGS
        ),
    }
    assert owner_grade_panel_passes(obs) is True

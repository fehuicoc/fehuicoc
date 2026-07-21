"""F-001 / AD-021 owner-grade panel observation contracts.

Shallow FR bars (instructions_nonblank + font_px == 18) must NOT pass.
Used by unit tests and as the contract FR helpers must enforce after restage.
"""

from __future__ import annotations

from typing import Any, Mapping

# Prior false-pass ceiling observed in FR-ER003-OBSERVED / F-001-live-dom.json
SHALLOW_FALSE_PASS_FONT_PX = 18

# Glance-large floor: must clear the shallow bar (1.375rem ≈ 22px at 16px root)
MIN_OWNER_GRADE_FONT_PX = 20

FRANCISCO_SQUAT_CUE_SUBSTRINGS = (
    "Pies al ancho cómodo",
    "rodillas alineadas",
)

FORBIDDEN_MEDIA_CHROME_MARKERS = (
    "linear-gradient(135deg, #ecfeff",
    "#ecfeff",
    "min-height: 140px",
    "clamp(1.125rem",
    "Visual coming soon",
)


def owner_grade_panel_passes(obs: Mapping[str, Any]) -> bool:
    """Return True only when observation meets F-001 owner-grade bar."""
    if not obs.get("primary_visible"):
        return False
    if not obs.get("instructions_nonblank"):
        return False
    font_px = obs.get("instructions_font_px")
    try:
        font_n = float(font_px)
    except (TypeError, ValueError):
        return False
    if font_n <= SHALLOW_FALSE_PASS_FONT_PX:
        return False
    if font_n < MIN_OWNER_GRADE_FONT_PX:
        return False
    if obs.get("has_media_chrome"):
        return False
    if obs.get("has_dual_instructions_slot"):
        return False
    if not obs.get("fixture_cues_present"):
        return False
    return True


def shallow_fr_er003_observation() -> dict[str, Any]:
    """Replica of the shallow FR-ER003-OBSERVED / live-DOM false-pass."""
    return {
        "primary_visible": False,  # panel read as leftover Visual region
        "instructions_nonblank": True,
        "instructions_font_px": SHALLOW_FALSE_PASS_FONT_PX,
        "has_media_chrome": True,
        "has_dual_instructions_slot": True,
        "fixture_cues_present": True,  # cues were present; chrome still wrong
    }

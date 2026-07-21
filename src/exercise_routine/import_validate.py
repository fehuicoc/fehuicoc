"""Import file gates — schema, size, extension, version (server authority)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_DIR / "contracts" / "exercise_routine_import.schema.json"

MAX_FILE_BYTES = 1_048_576
ALLOWED_EXTENSIONS = {".json"}
FORMAT_ID = "exercise-routine-coach"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _compatible_versions(schema: dict[str, Any]) -> set[str]:
    compat = schema.get("x_compatibility") or {}
    versions = compat.get("compatible_schema_versions") or ["1.0", "1.1"]
    return {str(v) for v in versions}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    document: dict[str, Any] | None = None
    preview: dict[str, Any] | None = None


def _extension_ok(filename: str | None) -> bool:
    if not filename:
        return False
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _optional_field_warnings(document: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    routine = document.get("routine") or {}
    optional_top = (
        "goal",
        "description",
        "level",
        "estimated_duration_minutes",
        "frequency",
        "equipment_required",
        "general_notes",
        "non_medical_warnings",
    )
    missing = [k for k in optional_top if k not in routine]
    if missing:
        warnings.append(
            "Optional routine fields absent (non-blocking): " + ", ".join(missing)
        )
    for session in routine.get("sessions") or []:
        for ex in session.get("exercises") or []:
            if "visual_ref" not in ex:
                warnings.append(
                    f"Exercise “{ex.get('name') or ex.get('id') or '?'}”: "
                    "visual_ref absent — placeholder will be used in session."
                )
                break
    return warnings


def _preview_exercise(ex: dict[str, Any]) -> dict[str, Any]:
    metric = ex.get("metric") or {}
    return {
        "id": ex.get("id"),
        "name": ex.get("name"),
        "order": ex.get("order"),
        "sets": ex.get("sets"),
        "metric_kind": metric.get("kind"),
        "reps": metric.get("reps"),
        "min_reps": metric.get("min_reps"),
        "max_reps": metric.get("max_reps"),
        "duration_seconds": metric.get("duration_seconds"),
        "rest_seconds": ex.get("rest_seconds"),
        "transition_seconds": ex.get("transition_seconds"),
        "laterality": ex.get("laterality"),
        "load": ex.get("load"),
    }


def _preview_from_document(document: dict[str, Any]) -> dict[str, Any]:
    routine = document.get("routine") or {}
    sessions = []
    for session in routine.get("sessions") or []:
        exercises = [_preview_exercise(ex) for ex in (session.get("exercises") or [])]
        blocks = []
        for block in session.get("blocks") or []:
            block_exercises = [
                _preview_exercise(ex) for ex in (block.get("exercises") or [])
            ]
            blocks.append(
                {
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "order": block.get("order"),
                    "type": block.get("type"),
                    "rounds": block.get("rounds"),
                    "exercise_count": len(block_exercises),
                    "exercises": block_exercises,
                }
            )
        exercise_count = len(exercises) or sum(
            int(b.get("exercise_count") or 0) for b in blocks
        )
        sessions.append(
            {
                "id": session.get("id"),
                "name": session.get("name"),
                "order": session.get("order"),
                "exercise_count": exercise_count,
                "block_count": len(blocks),
                "exercises": exercises,
                "blocks": blocks,
            }
        )
    live = routine.get("live_tracking") or {}
    return {
        "routine_id": routine.get("id"),
        "name": routine.get("name"),
        "schema_version": document.get("schema_version"),
        "session_count": len(sessions),
        "sessions": sessions,
        "live_tracking": {
            "countdown_before_start_seconds": live.get(
                "countdown_before_start_seconds"
            ),
            "allow_extend_rest": live.get("allow_extend_rest"),
            "rest_extension_increment_seconds": live.get(
                "rest_extension_increment_seconds"
            ),
            "display_preferences": live.get("display_preferences"),
        }
        if live
        else None,
        "persisted": False,
    }


def validate_bytes(
    content: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
    check_extension: bool = True,
) -> ValidationResult:
    """Validate upload bytes. Does not write to disk or library."""
    errors: list[str] = []
    warnings: list[str] = []

    if check_extension and not _extension_ok(filename):
        errors.append(
            "Disallowed file extension — only .json import files are accepted."
        )
        return ValidationResult(ok=False, errors=errors)

    if len(content) > MAX_FILE_BYTES:
        errors.append(
            f"File exceeds size limit of {MAX_FILE_BYTES} bytes "
            f"({len(content)} bytes received)."
        )
        return ValidationResult(ok=False, errors=errors)

    if content_type and "json" not in content_type.lower():
        warnings.append(
            f"Content-Type “{content_type}” is not application/json; "
            "continuing because extension/body gates passed."
        )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        errors.append("File is not valid UTF-8 text JSON.")
        return ValidationResult(ok=False, errors=errors)

    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"Malformed JSON — {exc.msg} (line {exc.lineno}).")
        return ValidationResult(ok=False, errors=errors)

    if not isinstance(document, dict):
        errors.append("Import root must be a JSON object.")
        return ValidationResult(ok=False, errors=errors)

    schema = _load_schema()
    version = str(document.get("schema_version") or "")
    compatible = _compatible_versions(schema)
    if version and version not in compatible:
        # Major outside 1.x or incompatible minor
        if not version.startswith("1."):
            errors.append(
                f"Incompatible schema_version “{version}” — "
                f"only majors 1.x are accepted ({', '.join(sorted(compatible))})."
            )
            return ValidationResult(ok=False, errors=errors)
        # Pattern may still pass schema; treat unknown 1.x as warning if schema ok
        warnings.append(
            f"schema_version “{version}” is not in the shipped compatibility list "
            f"({', '.join(sorted(compatible))}); validating against current schema."
        )

    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    if schema_errors:
        for err in schema_errors[:12]:
            path = ".".join(str(p) for p in err.path) or "(root)"
            errors.append(f"{path}: {err.message}")
        return ValidationResult(ok=False, errors=errors)

    if document.get("format_id") != FORMAT_ID:
        errors.append(f'format_id must be "{FORMAT_ID}".')
        return ValidationResult(ok=False, errors=errors)

    warnings.extend(_optional_field_warnings(document))
    preview = _preview_from_document(document)
    return ValidationResult(
        ok=True,
        errors=[],
        warnings=warnings,
        document=document,
        preview=preview,
    )


def validate_document(document: dict[str, Any]) -> ValidationResult:
    """Validate an already-parsed dict (no extension/size gates)."""
    raw = json.dumps(document).encode("utf-8")
    return validate_bytes(raw, filename="inline.json", check_extension=True)

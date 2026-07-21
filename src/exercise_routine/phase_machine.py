"""Guided session phase helpers — flat 1.0/1.1 + schema 1.2 block expanders."""

from __future__ import annotations

from typing import Any, Literal

PhaseKind = Literal["exercise", "rest", "transition", "complete", "countdown"]

# U-03 — fixed default transition; skippable in the UI
DEFAULT_TRANSITION_SECONDS = 5


def transition_seconds_for(ex: dict[str, Any]) -> int:
    """Honor per-exercise transition_seconds when present; else DEFAULT (AD-022)."""
    raw = ex.get("transition_seconds")
    if raw is None or raw == "":
        return DEFAULT_TRANSITION_SECONDS
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_TRANSITION_SECONDS


def format_load(load: dict[str, Any] | None) -> str | None:
    if not load:
        return None
    kind = load.get("kind")
    if kind == "bodyweight":
        return "Bodyweight"
    value = load.get("value")
    unit = load.get("unit") or ""
    if value is None:
        return kind
    text = f"{value} {unit}".strip()
    if load.get("per_hand"):
        text += " / hand"
    holding = load.get("holding_pattern")
    if holding:
        text += f" ({holding})"
    return text


def _side_sequence(ex: dict[str, Any]) -> list[str] | None:
    laterality = ex.get("laterality")
    seq = ex.get("side_sequence") or []
    if laterality == "both_sides_each_set":
        if seq:
            return [str(s) for s in seq]
        return ["left", "right"]
    metric_kind = ex.get("metric_kind") or ""
    if metric_kind in ("reps_per_side", "duration_per_side") and not seq:
        return ["left", "right"]
    if seq:
        return [str(s) for s in seq]
    return None


def _owns_done(ex: dict[str, Any], duration: int | None, reps: int | None) -> str:
    if duration is not None and duration > 0:
        return "duration"
    if reps is not None and reps > 0:
        return "reps_display_only"
    if ex.get("metric_kind") == "rep_range":
        return "reps_display_only"
    return "manual"


def _work_duration_reps(ex: dict[str, Any]) -> tuple[int | None, int | None]:
    duration = ex.get("duration_seconds")
    reps = ex.get("reps")
    try:
        duration_i = int(duration) if duration is not None and int(duration) > 0 else None
    except (TypeError, ValueError):
        duration_i = None
    try:
        reps_i = int(reps) if reps is not None and int(reps) > 0 else None
    except (TypeError, ValueError):
        reps_i = None
    if ex.get("metric_kind") == "rep_range" and reps_i is None:
        max_reps = ex.get("max_reps")
        try:
            reps_i = int(max_reps) if max_reps is not None else None
        except (TypeError, ValueError):
            reps_i = None
    return duration_i, reps_i


def _base_step(
    *,
    kind: str,
    ex: dict[str, Any],
    ex_idx: int,
    set_num: int,
    sets_total: int,
    name: str,
    duration: int | None,
    reps: int | None,
    instructions: str,
    side: str | None = None,
    block_meta: dict[str, Any] | None = None,
    round_num: int | None = None,
    rounds_total: int | None = None,
) -> dict[str, Any]:
    meta = block_meta or {}
    step: dict[str, Any] = {
        "kind": kind,
        "exercise_index": ex_idx,
        "exercise_id": ex.get("id"),
        "set": set_num,
        "sets_total": sets_total,
        "name": name,
        "duration_seconds": duration,
        "reps": reps,
        "min_reps": ex.get("min_reps"),
        "max_reps": ex.get("max_reps"),
        "metric_kind": ex.get("metric_kind"),
        "instructions": instructions,
        "visual_url": ex.get("visual_url") or None,
        "owns_done": _owns_done(ex, duration, reps)
        if kind == "exercise"
        else ("duration" if duration else "manual"),
        "laterality": ex.get("laterality"),
        "side": side,
        "load": ex.get("load"),
        "load_display": format_load(ex.get("load")),
        "tempo": ex.get("tempo"),
        "block_id": meta.get("block_id"),
        "block_name": meta.get("block_name"),
        "block_index": meta.get("block_index"),
        "block_total": meta.get("block_total"),
        "block_type": meta.get("block_type"),
        "round": round_num,
        "rounds_total": rounds_total,
    }
    return step


def _append_work_sides(
    steps: list[dict[str, Any]],
    *,
    ex: dict[str, Any],
    ex_idx: int,
    set_num: int,
    sets_total: int,
    block_meta: dict[str, Any] | None = None,
    round_num: int | None = None,
    rounds_total: int | None = None,
) -> None:
    """Emit work step(s). both_sides_each_set → left then right before any rest."""
    duration, reps = _work_duration_reps(ex)
    sides = _side_sequence(ex)
    name = ex.get("name") or f"Exercise {ex_idx + 1}"
    instructions = ex.get("instructions") or ""
    if sides:
        for side in sides:
            steps.append(
                _base_step(
                    kind="exercise",
                    ex=ex,
                    ex_idx=ex_idx,
                    set_num=set_num,
                    sets_total=sets_total,
                    name=f"{name} ({side})",
                    duration=duration,
                    reps=reps,
                    instructions=instructions,
                    side=side,
                    block_meta=block_meta,
                    round_num=round_num,
                    rounds_total=rounds_total,
                )
            )
    else:
        steps.append(
            _base_step(
                kind="exercise",
                ex=ex,
                ex_idx=ex_idx,
                set_num=set_num,
                sets_total=sets_total,
                name=name,
                duration=duration,
                reps=reps,
                instructions=instructions,
                side=None,
                block_meta=block_meta,
                round_num=round_num,
                rounds_total=rounds_total,
            )
        )


def _append_rest(
    steps: list[dict[str, Any]],
    *,
    seconds: int,
    ex: dict[str, Any],
    ex_idx: int,
    set_num: int,
    sets_total: int,
    block_meta: dict[str, Any] | None = None,
    round_num: int | None = None,
    rounds_total: int | None = None,
) -> None:
    if seconds <= 0:
        return
    steps.append(
        _base_step(
            kind="rest",
            ex=ex,
            ex_idx=ex_idx,
            set_num=set_num,
            sets_total=sets_total,
            name="Rest",
            duration=seconds,
            reps=None,
            instructions="Catch your breath. Next step follows.",
            block_meta=block_meta,
            round_num=round_num,
            rounds_total=rounds_total,
        )
    )


def _append_transition(
    steps: list[dict[str, Any]],
    *,
    seconds: int,
    ex: dict[str, Any],
    ex_idx: int,
    set_num: int,
    sets_total: int,
    block_meta: dict[str, Any] | None = None,
    round_num: int | None = None,
    rounds_total: int | None = None,
    name: str = "Transition",
) -> None:
    if seconds < 0:
        return
    if seconds == 0:
        return
    steps.append(
        _base_step(
            kind="transition",
            ex=ex,
            ex_idx=ex_idx,
            set_num=set_num,
            sets_total=sets_total,
            name=name,
            duration=seconds,
            reps=None,
            instructions="Get ready for the next step.",
            block_meta=block_meta,
            round_num=round_num,
            rounds_total=rounds_total,
        )
    )


def _annotate_next(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    next_name = None
    for i in range(len(steps) - 1, -1, -1):
        steps[i]["next_name"] = next_name
        if steps[i].get("kind") == "exercise":
            next_name = steps[i].get("name")
    return steps


def build_timeline_flat(exercises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand ordered flat exercises into exercise / rest / transition steps."""
    steps: list[dict[str, Any]] = []
    for ex_idx, ex in enumerate(exercises):
        sets = max(1, int(ex.get("sets") or 1))
        rest_seconds = max(0, int(ex.get("rest_seconds") or 0))
        transition_s = transition_seconds_for(ex)
        for set_num in range(1, sets + 1):
            is_last = ex_idx == len(exercises) - 1 and set_num == sets
            _append_work_sides(
                steps,
                ex=ex,
                ex_idx=ex_idx,
                set_num=set_num,
                sets_total=sets,
            )
            # Rest after both sides when bilateral (never between sides)
            if rest_seconds > 0 and not is_last:
                _append_rest(
                    steps,
                    seconds=rest_seconds,
                    ex=ex,
                    ex_idx=ex_idx,
                    set_num=set_num,
                    sets_total=sets,
                )
            if not is_last:
                _append_transition(
                    steps,
                    seconds=transition_s,
                    ex=ex,
                    ex_idx=ex_idx,
                    set_num=set_num,
                    sets_total=sets,
                )
    return _annotate_next(steps)


def _expand_circuit(
    steps: list[dict[str, Any]],
    block: dict[str, Any],
    block_meta: dict[str, Any],
    *,
    is_last_block: bool,
) -> None:
    exercises = list(block.get("exercises") or [])
    rounds = max(1, int(block.get("rounds") or 1))
    rest_between = int(block.get("rest_between_rounds_seconds") or 0)
    for round_num in range(1, rounds + 1):
        for ex_idx, ex in enumerate(exercises):
            sets = max(1, int(ex.get("sets") or 1))
            for set_num in range(1, sets + 1):
                _append_work_sides(
                    steps,
                    ex=ex,
                    ex_idx=ex_idx,
                    set_num=set_num,
                    sets_total=sets,
                    block_meta=block_meta,
                    round_num=round_num,
                    rounds_total=rounds,
                )
                rest_s = max(0, int(ex.get("rest_seconds") or 0))
                is_last_in_round = ex_idx == len(exercises) - 1 and set_num == sets
                if rest_s > 0 and not is_last_in_round:
                    _append_rest(
                        steps,
                        seconds=rest_s,
                        ex=ex,
                        ex_idx=ex_idx,
                        set_num=set_num,
                        sets_total=sets,
                        block_meta=block_meta,
                        round_num=round_num,
                        rounds_total=rounds,
                    )
                trans = transition_seconds_for(ex)
                if not is_last_in_round and trans > 0:
                    _append_transition(
                        steps,
                        seconds=trans,
                        ex=ex,
                        ex_idx=ex_idx,
                        set_num=set_num,
                        sets_total=sets,
                        block_meta=block_meta,
                        round_num=round_num,
                        rounds_total=rounds,
                    )
        if round_num < rounds and rest_between > 0:
            last_ex = exercises[-1] if exercises else {}
            _append_rest(
                steps,
                seconds=rest_between,
                ex=last_ex,
                ex_idx=max(0, len(exercises) - 1),
                set_num=1,
                sets_total=1,
                block_meta=block_meta,
                round_num=round_num,
                rounds_total=rounds,
            )
    _append_block_transition(steps, block, block_meta, is_last_block=is_last_block)


def _expand_straight(
    steps: list[dict[str, Any]],
    block: dict[str, Any],
    block_meta: dict[str, Any],
    *,
    is_last_block: bool,
) -> None:
    exercises = list(block.get("exercises") or [])
    for ex_idx, ex in enumerate(exercises):
        sets = max(1, int(ex.get("sets") or 1))
        rest_seconds = max(0, int(ex.get("rest_seconds") or 0))
        transition_s = transition_seconds_for(ex)
        for set_num in range(1, sets + 1):
            is_last_ex_set = ex_idx == len(exercises) - 1 and set_num == sets
            _append_work_sides(
                steps,
                ex=ex,
                ex_idx=ex_idx,
                set_num=set_num,
                sets_total=sets,
                block_meta=block_meta,
                round_num=1,
                rounds_total=1,
            )
            if rest_seconds > 0 and not (is_last_ex_set and is_last_block):
                # Keep rest between sets even on last block; skip only final after last set
                if not is_last_ex_set:
                    _append_rest(
                        steps,
                        seconds=rest_seconds,
                        ex=ex,
                        ex_idx=ex_idx,
                        set_num=set_num,
                        sets_total=sets,
                        block_meta=block_meta,
                        round_num=1,
                        rounds_total=1,
                    )
                elif not is_last_block:
                    _append_rest(
                        steps,
                        seconds=rest_seconds,
                        ex=ex,
                        ex_idx=ex_idx,
                        set_num=set_num,
                        sets_total=sets,
                        block_meta=block_meta,
                        round_num=1,
                        rounds_total=1,
                    )
            if not is_last_ex_set and transition_s > 0:
                _append_transition(
                    steps,
                    seconds=transition_s,
                    ex=ex,
                    ex_idx=ex_idx,
                    set_num=set_num,
                    sets_total=sets,
                    block_meta=block_meta,
                    round_num=1,
                    rounds_total=1,
                )
    _append_block_transition(steps, block, block_meta, is_last_block=is_last_block)


def _expand_paired(
    steps: list[dict[str, Any]],
    block: dict[str, Any],
    block_meta: dict[str, Any],
    *,
    is_last_block: bool,
) -> None:
    """Round-wise A then B (not all sets of A then B)."""
    exercises = list(block.get("exercises") or [])
    if len(exercises) < 2:
        _expand_straight(steps, block, block_meta, is_last_block=is_last_block)
        return
    a, b = exercises[0], exercises[1]
    rounds = max(
        1,
        int(block.get("rounds") or 0)
        or int(a.get("sets") or 1)
        or int(b.get("sets") or 1),
    )
    rest_between = block.get("rest_between_rounds_seconds")
    for round_num in range(1, rounds + 1):
        _append_work_sides(
            steps,
            ex=a,
            ex_idx=0,
            set_num=round_num,
            sets_total=rounds,
            block_meta=block_meta,
            round_num=round_num,
            rounds_total=rounds,
        )
        a_rest = max(0, int(a.get("rest_seconds") or 0))
        if a_rest > 0:
            _append_rest(
                steps,
                seconds=a_rest,
                ex=a,
                ex_idx=0,
                set_num=round_num,
                sets_total=rounds,
                block_meta=block_meta,
                round_num=round_num,
                rounds_total=rounds,
            )
        a_trans = transition_seconds_for(a)
        if a_trans > 0:
            _append_transition(
                steps,
                seconds=a_trans,
                ex=a,
                ex_idx=0,
                set_num=round_num,
                sets_total=rounds,
                block_meta=block_meta,
                round_num=round_num,
                rounds_total=rounds,
            )
        _append_work_sides(
            steps,
            ex=b,
            ex_idx=1,
            set_num=round_num,
            sets_total=rounds,
            block_meta=block_meta,
            round_num=round_num,
            rounds_total=rounds,
        )
        if round_num < rounds:
            if rest_between is not None:
                between = max(0, int(rest_between))
            else:
                between = max(0, int(b.get("rest_seconds") or 0))
            if between > 0:
                _append_rest(
                    steps,
                    seconds=between,
                    ex=b,
                    ex_idx=1,
                    set_num=round_num,
                    sets_total=rounds,
                    block_meta=block_meta,
                    round_num=round_num,
                    rounds_total=rounds,
                )
            b_trans = transition_seconds_for(b)
            if b_trans > 0:
                _append_transition(
                    steps,
                    seconds=b_trans,
                    ex=b,
                    ex_idx=1,
                    set_num=round_num,
                    sets_total=rounds,
                    block_meta=block_meta,
                    round_num=round_num,
                    rounds_total=rounds,
                )
        elif not is_last_block:
            # Final B rest before next block when not last block
            b_rest = max(0, int(b.get("rest_seconds") or 0))
            if b_rest > 0 and rest_between is None:
                _append_rest(
                    steps,
                    seconds=b_rest,
                    ex=b,
                    ex_idx=1,
                    set_num=round_num,
                    sets_total=rounds,
                    block_meta=block_meta,
                    round_num=round_num,
                    rounds_total=rounds,
                )
    _append_block_transition(steps, block, block_meta, is_last_block=is_last_block)


def _append_block_transition(
    steps: list[dict[str, Any]],
    block: dict[str, Any],
    block_meta: dict[str, Any],
    *,
    is_last_block: bool,
) -> None:
    if is_last_block:
        return
    raw = block.get("transition_after_block_seconds")
    if raw is None:
        return
    seconds = max(0, int(raw))
    if seconds <= 0:
        return
    exercises = list(block.get("exercises") or [])
    ex = exercises[-1] if exercises else {"name": block.get("name")}
    _append_transition(
        steps,
        seconds=seconds,
        ex=ex,
        ex_idx=max(0, len(exercises) - 1),
        set_num=1,
        sets_total=1,
        block_meta=block_meta,
        name="Block transition",
    )


def build_timeline_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    ordered = sorted(blocks, key=lambda b: int(b.get("order") or 0))
    total = len(ordered)
    for b_idx, block in enumerate(ordered):
        block_meta = {
            "block_id": block.get("id"),
            "block_name": block.get("name"),
            "block_index": b_idx + 1,
            "block_total": total,
            "block_type": block.get("type"),
        }
        is_last = b_idx == total - 1
        btype = block.get("type") or "sequence"
        if btype == "circuit":
            _expand_circuit(steps, block, block_meta, is_last_block=is_last)
        elif btype == "paired_sets":
            _expand_paired(steps, block, block_meta, is_last_block=is_last)
        elif btype in ("straight_sets", "straight_sets_bilateral", "sequence"):
            _expand_straight(steps, block, block_meta, is_last_block=is_last)
        else:
            _expand_straight(steps, block, block_meta, is_last_block=is_last)
    return _annotate_next(steps)


def build_timeline(routine: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand blocks (1.2) or flat exercises (1.0/1.1) into timeline steps."""
    blocks = routine.get("blocks") or []
    if blocks:
        return build_timeline_blocks(blocks)
    return build_timeline_flat(routine.get("exercises") or [])


def progress_caption(step_index: int, total: int, ended_early: bool = False) -> str:
    if total <= 0:
        return "No steps"
    if ended_early:
        return f"Ended early · completed {step_index} of {total} steps"
    if step_index >= total:
        return f"Complete · {total} of {total} steps"
    return f"Step {step_index + 1} of {total}"

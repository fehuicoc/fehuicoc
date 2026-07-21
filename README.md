# Exercise Routine Coach

Import-first personal guided workout coach — upload a ChatGPT-compatible `.json` routine (schema **1.0 / 1.1** flat `exercises[]`, or **1.2** `blocks[]`), preview and confirm into your browser library, optionally edit, then run a single guided session engine (exercise / rest / transition).

English UI. Not medical advice.

## Purpose

Guide an operator through imported workout sessions with timers, progress strip (block / round / set / side / load / next), optional pre-start countdown, and extend-rest — phone-first option_1 layout without a sidebar.

## Setup / run locally

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn exercise_routine.app:app --reload --app-dir src --port 8765
```

Open http://127.0.0.1:8765/ (Import is the home page)

Health check: http://127.0.0.1:8765/health

## Flow

1. **Import** (primary) — select or drop a `.json` file (≤ 1 MiB). Preview sessions, blocks, and exercises before anything is saved. Cancel clears the preview; Confirm upserts into My routines.
2. **My routines** — open imported or manually built routines; start a session (multi-day routines ask which day/session to run).
3. **Build** (secondary) — create or edit a named routine with ordered exercises (duration and/or reps, rest, sets, instructions, optional visual URL). Block authoring UI is out of scope for schema 1.2.
4. **Session** — guided timers with Pause / Continue / Skip / Back / Restart / End; glanceable progress strip; countdown and extend rest when `live_tracking` says so.

Authority fixture for 1.2: `tests/fixtures/francisco_semana6_dia1_webapp_v2.json`  
Example flat import: `examples/chatgpt_compatible_routine.json`

## Testing

```powershell
python -m pytest -q
```

## Storage

Routines persist in browser `localStorage` (`er_coach_routines_v1`). Import preview is ephemeral (`sessionStorage` `er_import_preview_v1`) and is not recovered after a hard reload. No enterprise identity.

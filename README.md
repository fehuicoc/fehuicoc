# Exercise Routine Coach

Static web app (no Python / FastAPI / Uvicorn). Import JSON routines, store them in `localStorage`, and run guided sessions in the browser. Deployable on Netlify.

Compatible import schemas: **1.0 / 1.1** (`exercises[]`) and **1.2** (`blocks[]`).

## Setup

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:8765/

## Production build

```powershell
npm run build
```

Output: `dist/` (configured in `vite.config.js` and `netlify.toml`).

Preview locally:

```powershell
npm run preview
```

## Netlify

- Build command: `npm run build`
- Publish directory: `dist`
- See `netlify.toml` for pretty-path redirects (`/library` to `library.html`, etc.)

## Flow

1. **Import** — choose or drop a `.json` file (max 1 MiB). Preview is ephemeral (`sessionStorage`).
2. **Confirm** — saves to **My routines** (`localStorage` key `er_coach_routines_v1`).
3. **Session** — timers for exercise / rest / transition; Pause, Continue, Skip, Back, Restart, End; final summary.

Sample files under `public/examples/` and `public/fixtures/` (including Francisco schema 1.2).

## Notes

- No backend and no `/api/*` calls.
- Import validation runs in the browser (JSON Schema + adapter).

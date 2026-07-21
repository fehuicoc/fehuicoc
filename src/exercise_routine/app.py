"""Exercise Routine Coach FastAPI entry (MOD-ER-APP + MOD-ER-IMPORT routes)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from exercise_routine.health import router as health_router
from exercise_routine.import_adapter import adapt_import_document
from exercise_routine.import_validate import MAX_FILE_BYTES, validate_bytes
from exercise_routine.phase_machine import DEFAULT_TRANSITION_SECONDS

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Exercise Routine Coach",
        description="Import-first personal guided workout coach",
        version="0.2.0",
    )
    app.include_router(health_router)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "import.html",
            {
                "request": request,
                "page": "import",
                "title": "Import routine",
                "max_file_bytes": MAX_FILE_BYTES,
            },
        )

    @app.get("/import", response_class=HTMLResponse)
    def import_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "import.html",
            {
                "request": request,
                "page": "import",
                "title": "Import routine",
                "max_file_bytes": MAX_FILE_BYTES,
            },
        )

    @app.post("/api/import/preview")
    async def import_preview(
        request: Request,
        file: UploadFile | None = File(None),
    ) -> JSONResponse:
        """Server-authoritative validate + ephemeral preview (no library persist)."""
        filename: str | None = None
        content: bytes
        content_type: str | None = None

        if file is not None and file.filename:
            filename = file.filename
            content = await file.read()
            content_type = file.content_type
        else:
            content_type = request.headers.get("content-type")
            body = await request.body()
            if not body:
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "errors": ["No file or JSON body provided."],
                        "warnings": [],
                        "preview": None,
                        "canonical": None,
                    },
                )
            # Raw JSON body — treat as .json for extension gate
            filename = "upload.json"
            content = body

        result = validate_bytes(
            content, filename=filename, content_type=content_type
        )
        if not result.ok:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "preview": None,
                    "canonical": None,
                    "persisted": False,
                },
            )

        canonical = adapt_import_document(result.document or {})
        return JSONResponse(
            {
                "ok": True,
                "errors": [],
                "warnings": result.warnings,
                "preview": result.preview,
                "canonical": canonical,
                "persisted": False,
            }
        )

    @app.get("/session", response_class=HTMLResponse)
    def session_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "session.html",
            {
                "request": request,
                "page": "session",
                "title": "Guided session",
                "transition_default": DEFAULT_TRANSITION_SECONDS,
            },
        )

    @app.get("/library", response_class=HTMLResponse)
    def library_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "library.html",
            {"request": request, "page": "library", "title": "My routines"},
        )

    @app.get("/author", response_class=HTMLResponse)
    def author_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "author.html",
            {"request": request, "page": "author", "title": "Build routine"},
        )

    return app


app = create_app()

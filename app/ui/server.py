"""UI module that mounts Jinja2 templates + static assets onto the FastAPI app.

The UI is intentionally minimal: four pages (home, run, results, compare),
all server-rendered, with HTMX driving partial updates and Plotly.js
rendering charts. No build step, no Node toolchain, no SPA layer.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.benchmark.compare import compare_cpu_vs_gpu
from app.core.metadata import project_version
from app.core.system_info import collect_system_info
from app.storage.filesystem import list_runs, load_manifest, load_trace
from app.storage.manifests import BackendIdentifier

UI_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = UI_DIR / "templates"
STATIC_DIR = UI_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def mount_ui(app: FastAPI) -> None:
    """Attach the UI to ``app``.

    Routes added:

    - ``/``                       home (system info + CTAs)
    - ``/run``                    run-an-experiment page
    - ``/results``                list of past runs
    - ``/results/{run_id}``       single-run drill-in
    - ``/compare``                CPU vs GPU comparison page
    - ``/static/...``             static assets

    The UI is purely client-side from the API perspective: it consumes the
    same HTTP API exposed under ``/api`` and ``/health`` without backdoors.
    """
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def _home(request: Request) -> HTMLResponse:
        info = collect_system_info()
        return templates.TemplateResponse(  # type: ignore[no-any-return]
            request,
            "index.html",
            {
                "system_info": info.to_dict(),
                "project_version": project_version(),
                "has_gpu": bool(info.gpus),
                "backends": list(BackendIdentifier),
            },
        )

    @app.get("/run", response_class=HTMLResponse, include_in_schema=False)
    def _run(request: Request) -> HTMLResponse:
        info = collect_system_info()
        return templates.TemplateResponse(  # type: ignore[no-any-return]
            request,
            "run.html",
            {
                "has_gpu": bool(info.gpus),
                "backends": list(BackendIdentifier),
            },
        )

    @app.get("/results", response_class=HTMLResponse, include_in_schema=False)
    def _results(request: Request) -> HTMLResponse:
        runs = list_runs()
        return templates.TemplateResponse(  # type: ignore[no-any-return]
            request, "results.html", {"runs": runs}
        )

    @app.get("/results/{run_id}", response_class=HTMLResponse, include_in_schema=False)
    def _result_detail(request: Request, run_id: str) -> HTMLResponse:
        try:
            manifest = load_manifest(run_id)
            trace = load_trace(run_id)
        except FileNotFoundError:
            return HTMLResponse(f"unknown run {run_id}", status_code=404)
        return templates.TemplateResponse(  # type: ignore[no-any-return]
            request,
            "result_detail.html",
            {
                "manifest": manifest,
                "trace_records": [r.model_dump(mode="json") for r in trace.records],
            },
        )

    @app.get("/compare", response_class=HTMLResponse, include_in_schema=False)
    def _compare(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(  # type: ignore[no-any-return]
            request, "compare.html", {"report": compare_cpu_vs_gpu()}
        )

"""FastAPI application entry point.

Routes are organized as:

- ``/health``                 health + capability discovery
- ``/api/runs/h2``            POST: start an H2 VQE
- ``/api/runs/lih``           POST: start a LiH VQE
- ``/api/runs``               GET: list past runs
- ``/api/runs/{id}``          GET: manifest for one run
- ``/api/runs/{id}/trace``    GET: full iteration trace
- ``/api/runs/{id}/stream``   GET: SSE stream of live iterations
- ``/api/comparison``         GET: CPU-vs-GPU comparison report
- ``/`` (and below)           UI (Jinja2 + HTMX + Tailwind + Plotly)
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, results, run
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.metadata import project_version


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    log = get_logger("api")

    app = FastAPI(
        title="cudaq-molecular-simulation-blueprint",
        version=project_version(),
        description=(
            "Hybrid quantum-classical molecular simulation reference "
            "implementation using NVIDIA CUDA-Q. Provider-agnostic by "
            "design; Akamai-specific deployment lives under infra/."
        ),
    )

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health.router)
    app.include_router(run.router, prefix="/api")
    app.include_router(results.router, prefix="/api")
    app.include_router(results.compare_router, prefix="/api")

    # UI is mounted lazily so the API container can run headless without it.
    try:
        from app.ui.server import mount_ui

        mount_ui(app)
        log.info("ui.mounted")
    except Exception as exc:
        log.warning("ui.mount_failed", error=str(exc))

    return app


app = create_app()

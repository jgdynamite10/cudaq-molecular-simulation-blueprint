"""Filesystem-based persistence of run manifests and traces.

Each run lives in its own directory under ``results/<run_id>/``. We keep the
data flat so it can be inspected with ``cat``, archived as a tarball, or
shipped alongside the blog post without any database hydration.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.storage.manifests import IterationTrace, RunManifest
from app.storage.serializers import read_json, write_json

MANIFEST_FILENAME = "manifest.json"
TRACE_FILENAME = "trace.json"


def new_run_id() -> str:
    """Return a sortable, human-readable run id."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:6]
    return f"{timestamp}-{suffix}"


def run_dir(run_id: str) -> Path:
    return get_settings().results_dir / run_id


def save_manifest(manifest: RunManifest) -> Path:
    """Persist ``manifest`` to ``results/<run_id>/manifest.json``."""
    path = run_dir(manifest.run_id) / MANIFEST_FILENAME
    write_json(path, manifest)
    return path


def save_trace(trace: IterationTrace) -> Path:
    """Persist ``trace`` to ``results/<run_id>/trace.json``."""
    path = run_dir(trace.run_id) / TRACE_FILENAME
    write_json(path, trace)
    return path


def load_manifest(run_id: str) -> RunManifest:
    path = run_dir(run_id) / MANIFEST_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"manifest not found for run {run_id}: {path}")
    return RunManifest.model_validate(read_json(path))


def load_trace(run_id: str) -> IterationTrace:
    path = run_dir(run_id) / TRACE_FILENAME
    if not path.exists():
        return IterationTrace(run_id=run_id, records=[])
    return IterationTrace.model_validate(read_json(path))


def list_runs() -> list[RunManifest]:
    """Return all manifests on disk, newest first."""
    base = get_settings().results_dir
    if not base.exists():
        return []
    manifests: list[RunManifest] = []
    for entry in sorted(base.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        manifest_path = entry / MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        try:
            manifests.append(RunManifest.model_validate(read_json(manifest_path)))
        except (ValueError, OSError):
            continue
    return manifests

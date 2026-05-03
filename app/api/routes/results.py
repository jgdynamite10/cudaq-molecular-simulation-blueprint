"""Endpoints that read finished run artifacts and stream live ones."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_coordinator
from app.api.schemas import CompareResponse, RunSummary
from app.benchmark.compare import compare_cpu_vs_gpu
from app.storage.filesystem import list_runs, load_manifest, load_trace
from app.storage.manifests import RunManifest

router = APIRouter(prefix="/runs", tags=["results"])

compare_router = APIRouter(prefix="/comparison", tags=["results"])


def _to_summary(m: RunManifest) -> RunSummary:
    r = m.result
    return RunSummary(
        run_id=m.run_id,
        molecule=m.molecule.name,
        backend=m.backend,
        target_string=m.target_string,
        status=m.status,
        started_at=m.created_at,
        completed_at=m.completed_at,
        energy=r.energy if r else None,
        iterations=r.iterations if r else None,
        wall_time_seconds=r.wall_time_seconds if r else None,
        error_vs_reference_hartree=r.error_vs_reference_hartree if r else None,
        chemical_accuracy_reached=r.chemical_accuracy_reached if r else None,
    )


@router.get("", response_model=list[RunSummary])
def list_all() -> list[RunSummary]:
    return [_to_summary(m) for m in list_runs()]


@router.get("/{run_id}", response_model=RunManifest)
def get_run(run_id: str) -> RunManifest:
    try:
        return load_manifest(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{run_id}/trace")
def get_trace(run_id: str) -> dict[str, object]:
    trace = load_trace(run_id)
    return {
        "run_id": trace.run_id,
        "records": [r.model_dump(mode="json") for r in trace.records],
    }


@router.get("/{run_id}/stream")
async def stream_run(run_id: str) -> EventSourceResponse:
    coordinator = get_coordinator()
    try:
        queue = await coordinator.queue_for(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown run {run_id}") from exc

    async def event_source() -> AsyncIterator[dict[str, str]]:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=30.0)
            except TimeoutError:
                yield {"event": "ping", "data": json.dumps({"ts": "alive"})}
                continue
            if payload is None:
                active = await coordinator.status(run_id)
                final = {
                    "run_id": run_id,
                    "error": active.error if active else None,
                }
                yield {"event": "completed", "data": json.dumps(final)}
                return
            yield {"event": "iteration", "data": json.dumps(payload)}

    return EventSourceResponse(event_source())


@compare_router.get("", response_model=CompareResponse)
def comparison() -> CompareResponse:
    return CompareResponse(**compare_cpu_vs_gpu())

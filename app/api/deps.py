"""Run coordinator: in-memory bookkeeping for live VQE jobs.

The coordinator is responsible for:

- spawning a VQE run in a worker thread so the event loop stays responsive,
- buffering per-iteration events to a per-run queue so the SSE stream can
  read them without polling the filesystem,
- persisting the final manifest and trace once the run completes.

The coordinator allocates the ``run_id`` up front and passes it into the
experiment, so the API can return the id to the client immediately and the
client can subscribe to the iteration stream without race conditions.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.storage.filesystem import new_run_id, save_manifest, save_trace
from app.storage.manifests import (
    IterationRecord,
    IterationTrace,
    RunManifest,
)

log = get_logger("coordinator")

# Type of the callable the coordinator hands the on_iteration hook to.
ExperimentRunner = Callable[
    [str, Callable[[IterationRecord], None]],
    tuple[RunManifest, IterationTrace],
]


@dataclass(slots=True)
class _ActiveRun:
    run_id: str
    queue: asyncio.Queue[dict[str, Any] | None]
    task: asyncio.Task[None] | None = None
    manifest: RunManifest | None = None
    trace: IterationTrace | None = None
    finished: bool = False
    error: str | None = None


class RunCoordinator:
    """Tracks active and recently completed VQE runs in memory."""

    def __init__(self) -> None:
        self._runs: dict[str, _ActiveRun] = {}
        self._lock = asyncio.Lock()

    async def spawn(self, experiment: ExperimentRunner) -> str:
        """Allocate a run id, start the experiment in a worker thread, return the id."""
        loop = asyncio.get_running_loop()
        run_id = new_run_id()
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        active = _ActiveRun(run_id=run_id, queue=queue)
        async with self._lock:
            self._runs[run_id] = active

        def on_iteration(record: IterationRecord) -> None:
            payload = {
                "iteration": record.iteration,
                "energy": record.energy,
                "elapsed_seconds": record.elapsed_seconds,
            }
            loop.call_soon_threadsafe(queue.put_nowait, payload)

        async def _driver() -> None:
            try:
                manifest, trace = await asyncio.to_thread(experiment, run_id, on_iteration)
                async with self._lock:
                    active.manifest = manifest
                    active.trace = trace
                save_manifest(manifest)
                save_trace(trace)
                log.info("coordinator.run_completed", run_id=run_id)
            except Exception as exc:
                log.error("coordinator.run_failed", run_id=run_id, error=str(exc))
                async with self._lock:
                    active.error = f"{type(exc).__name__}: {exc}"
            finally:
                async with self._lock:
                    active.finished = True
                loop.call_soon_threadsafe(queue.put_nowait, None)

        active.task = asyncio.create_task(_driver(), name=f"vqe-{run_id}")
        return run_id

    async def queue_for(self, run_id: str) -> asyncio.Queue[dict[str, Any] | None]:
        async with self._lock:
            active = self._runs.get(run_id)
        if active is None:
            raise KeyError(run_id)
        return active.queue

    async def status(self, run_id: str) -> _ActiveRun | None:
        async with self._lock:
            return self._runs.get(run_id)

    async def join(self, run_id: str, timeout: float | None = None) -> None:
        active = await self.status(run_id)
        if active is None or active.task is None:
            return
        try:
            if timeout is None:
                await active.task
            else:
                await asyncio.wait_for(asyncio.shield(active.task), timeout=timeout)
        except TimeoutError:
            return


_coordinator: RunCoordinator | None = None


def get_coordinator() -> RunCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = RunCoordinator()
    return _coordinator


# Awaitable type alias used by route handlers.
SpawnAwaitable = Awaitable[str]

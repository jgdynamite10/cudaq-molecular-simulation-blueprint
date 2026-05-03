"""VQE optimization driver with built-in trace capture.

Uses :func:`scipy.optimize.minimize` (COBYLA) so we get a real per-evaluation
trace for free, which is what the UI plots and what the benchmark harness
analyzes. CUDA-Q's built-in :func:`cudaq.vqe` is more compact but does not
expose iteration-level data, so we deliberately pick the SciPy path here.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.optimize import OptimizeResult, minimize

from app.storage.manifests import IterationRecord


@dataclass
class TracingCost:
    """Cost function wrapper that records every CUDA-Q ``observe`` call."""

    kernel: Any
    hamiltonian: Any
    kernel_args: tuple = field(default_factory=tuple)
    records: list[IterationRecord] = field(default_factory=list)
    _t0: float | None = field(default=None, init=False, repr=False)

    def __call__(self, theta: np.ndarray) -> float:
        import cudaq

        if self._t0 is None:
            self._t0 = time.perf_counter()
        params = list(theta)
        energy_obj = cudaq.observe(self.kernel, self.hamiltonian, params, *self.kernel_args)
        energy = float(energy_obj.expectation())
        elapsed = time.perf_counter() - self._t0
        self.records.append(
            IterationRecord(
                iteration=len(self.records),
                energy=energy,
                elapsed_seconds=elapsed,
                parameters=params,
            )
        )
        return energy


@dataclass(slots=True)
class OptimizationOutcome:
    """Result of one VQE optimization run."""

    energy: float
    parameters: list[float]
    iterations: int
    function_evaluations: int
    converged: bool
    wall_time_seconds: float
    raw: OptimizeResult


def run_cobyla(
    cost: TracingCost,
    initial_parameters: np.ndarray,
    *,
    max_iterations: int = 200,
    rhobeg: float = 0.5,
    tolerance: float = 1e-6,
    on_iteration: Callable[[IterationRecord], None] | None = None,
) -> OptimizationOutcome:
    """Run a COBYLA optimization driven by ``cost``.

    ``on_iteration`` is invoked with the most recent :class:`IterationRecord`
    after each cost evaluation. The API server uses this hook to push
    server-sent events for live UI updates.
    """
    last_seen = 0

    def _scipy_callback(_xk: np.ndarray) -> None:
        nonlocal last_seen
        if on_iteration is None:
            return
        for record in cost.records[last_seen:]:
            on_iteration(record)
        last_seen = len(cost.records)

    start = time.perf_counter()
    result: OptimizeResult = minimize(
        cost,
        initial_parameters,
        method="COBYLA",
        callback=_scipy_callback,
        options={"maxiter": max_iterations, "rhobeg": rhobeg, "tol": tolerance, "disp": False},
    )
    elapsed = time.perf_counter() - start

    if on_iteration is not None and last_seen < len(cost.records):
        for record in cost.records[last_seen:]:
            on_iteration(record)

    return OptimizationOutcome(
        energy=float(result.fun),
        parameters=[float(x) for x in result.x],
        iterations=int(getattr(result, "nit", len(cost.records))),
        function_evaluations=int(getattr(result, "nfev", len(cost.records))),
        converged=bool(getattr(result, "success", False)),
        wall_time_seconds=elapsed,
        raw=result,
    )

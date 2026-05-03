"""CPU vs GPU comparison report.

Reads every manifest under the configured ``results/`` directory, groups by
``(experiment, backend)``, computes mean and standard error for the metrics
the blog post quotes, and emits a structured report.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any

from app.benchmark.metrics import summarize_run
from app.storage.filesystem import list_runs, load_trace


def _stderr(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values) / math.sqrt(len(values))


def compare_cpu_vs_gpu() -> dict[str, Any]:
    """Build a structured CPU-vs-GPU comparison from on-disk runs.

    Returns a dict with one entry per molecule, containing per-backend
    aggregates (n, mean, stderr) for wall time, time per evaluation,
    iterations, error vs reference, and the GPU/CPU speedup factor.
    """
    runs = list_runs()
    grouped: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for manifest in runs:
        if manifest.result is None:
            continue
        trace = load_trace(manifest.run_id)
        m = summarize_run(manifest, trace)
        grouped[(m.molecule, m.backend)].append(m)

    report: dict[str, Any] = {"by_molecule": {}}
    for molecule in sorted({mol for mol, _ in grouped}):
        per_backend: dict[str, dict[str, Any]] = {}
        for (mol, backend), metrics_list in grouped.items():
            if mol != molecule:
                continue
            wall_times = [m.wall_time_seconds for m in metrics_list]
            per_eval = [m.time_per_evaluation_ms for m in metrics_list]
            iters = [m.iterations for m in metrics_list]
            errors = [
                abs(m.error_vs_reference_hartree)
                for m in metrics_list
                if m.error_vs_reference_hartree is not None
            ]
            per_backend[backend] = {
                "n": len(metrics_list),
                "wall_time_seconds": {
                    "mean": statistics.fmean(wall_times),
                    "stderr": _stderr(wall_times),
                    "values": wall_times,
                },
                "time_per_evaluation_ms": {
                    "mean": statistics.fmean(per_eval),
                    "stderr": _stderr(per_eval),
                },
                "iterations": {
                    "mean": statistics.fmean(iters),
                    "stderr": _stderr([float(v) for v in iters]),
                },
                "error_hartree": {
                    "mean": statistics.fmean(errors) if errors else None,
                    "stderr": _stderr(errors) if errors else 0.0,
                },
                "qubit_count": metrics_list[0].qubit_count,
                "parameter_count": metrics_list[0].parameter_count,
                "target_strings": sorted({m.target_string for m in metrics_list}),
            }

        speedups: dict[str, float] = {}
        if "cpu" in per_backend:
            cpu_mean = per_backend["cpu"]["wall_time_seconds"]["mean"]
            for backend, stats in per_backend.items():
                if backend == "cpu":
                    continue
                gpu_mean = stats["wall_time_seconds"]["mean"]
                if gpu_mean > 0:
                    speedups[f"cpu_over_{backend}_wall_time"] = cpu_mean / gpu_mean

        report["by_molecule"][molecule] = {
            "backends": per_backend,
            "speedups": speedups,
        }

    report["totals"] = {
        "molecules": list(report["by_molecule"].keys()),
        "total_runs": sum(len(v) for v in grouped.values()),
    }
    return report

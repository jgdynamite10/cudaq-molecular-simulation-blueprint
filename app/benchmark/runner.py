"""Benchmark suite runner.

Sweeps a list of ``(experiment, backend, seed)`` configurations, runs them
in series (we want clean GPU/CPU isolation, not interleaved), and persists
each run as a regular manifest + trace. Downstream comparison tooling reads
those directly off disk.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from app.core.logging import get_logger
from app.quantum.h2_vqe import run_h2
from app.quantum.lih_vqe import run_lih
from app.storage.filesystem import save_manifest, save_trace
from app.storage.manifests import (
    BackendIdentifier,
    IterationRecord,
    IterationTrace,
    RunManifest,
)

ExperimentName = Literal["h2", "lih"]

log = get_logger("benchmark")


@dataclass(slots=True)
class BenchmarkSpec:
    """One row of the benchmark suite."""

    experiment: ExperimentName
    backend: BackendIdentifier
    seed: int = 42
    max_iterations: int = 200
    bond_distance: float | None = None
    label: str | None = None


def run_one(
    spec: BenchmarkSpec,
    on_iteration: Callable[[IterationRecord], None] | None = None,
) -> tuple[RunManifest, IterationTrace]:
    """Execute a single benchmark configuration."""
    common_kwargs = {
        "backend_id": spec.backend,
        "seed": spec.seed,
        "max_iterations": spec.max_iterations,
        "on_iteration": on_iteration,
    }
    if spec.experiment == "h2":
        bond = spec.bond_distance if spec.bond_distance is not None else 0.7414
        return run_h2(bond_distance=bond, **common_kwargs)
    if spec.experiment == "lih":
        bond = spec.bond_distance if spec.bond_distance is not None else 1.5957
        return run_lih(bond_distance=bond, **common_kwargs)
    raise ValueError(f"unknown experiment: {spec.experiment}")


def run_benchmark_suite(
    specs: list[BenchmarkSpec],
    *,
    on_iteration: Callable[[IterationRecord], None] | None = None,
) -> list[RunManifest]:
    """Run a list of benchmark specs and persist each as a regular run."""
    manifests: list[RunManifest] = []
    for spec in specs:
        log.info(
            "benchmark.spec_start",
            experiment=spec.experiment,
            backend=spec.backend.value,
            seed=spec.seed,
            label=spec.label,
        )
        manifest, trace = run_one(spec, on_iteration=on_iteration)
        save_manifest(manifest)
        save_trace(trace)
        manifests.append(manifest)
        log.info(
            "benchmark.spec_done",
            experiment=spec.experiment,
            backend=spec.backend.value,
            run_id=manifest.run_id,
            energy=manifest.result.energy if manifest.result else None,
            wall_time=manifest.result.wall_time_seconds if manifest.result else None,
        )
    return manifests


def default_blog_suite(seeds: tuple[int, ...] = (42, 43, 44, 45, 46)) -> list[BenchmarkSpec]:
    """The exact suite of runs that produces the blog-ready charts.

    For each backend we sweep multiple seeds so we can quote mean ± stderr.
    """
    suite: list[BenchmarkSpec] = []
    backends_h2 = [BackendIdentifier.CPU, BackendIdentifier.GPU_FP32, BackendIdentifier.GPU_FP64]
    backends_lih = [BackendIdentifier.CPU, BackendIdentifier.GPU_FP64]
    for backend in backends_h2:
        for seed in seeds:
            suite.append(
                BenchmarkSpec(
                    experiment="h2",
                    backend=backend,
                    seed=seed,
                    max_iterations=200,
                    label=f"h2/{backend.value}/seed{seed}",
                )
            )
    for backend in backends_lih:
        for seed in seeds:
            suite.append(
                BenchmarkSpec(
                    experiment="lih",
                    backend=backend,
                    seed=seed,
                    max_iterations=500,
                    label=f"lih/{backend.value}/seed{seed}",
                )
            )
    return suite

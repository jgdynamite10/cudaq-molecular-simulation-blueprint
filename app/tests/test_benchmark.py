"""Benchmark metrics + compare tests using synthetic manifests."""

from __future__ import annotations

from datetime import UTC, datetime

from app.benchmark.compare import compare_cpu_vs_gpu
from app.benchmark.metrics import summarize_run
from app.storage.filesystem import save_manifest, save_trace
from app.storage.manifests import (
    BackendIdentifier,
    IterationRecord,
    IterationTrace,
    Molecule,
    MoleculeSpec,
    OptimizerSpec,
    RunManifest,
    RunResult,
    RunStatus,
)


def _make_manifest(
    *,
    run_id: str,
    backend: BackendIdentifier,
    target: str,
    molecule: Molecule = Molecule.H2,
    energy: float = -1.137,
    wall_time: float = 1.0,
    n_iter: int = 30,
) -> tuple[RunManifest, IterationTrace]:
    geometry = (
        [("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.7414))]
        if molecule == Molecule.H2
        else [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 1.5957))]
    )
    manifest = RunManifest(
        run_id=run_id,
        project_version="0.1.0",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=RunStatus.COMPLETED,
        backend=backend,
        target_string=target,
        seed=42,
        molecule=MoleculeSpec(name=molecule, geometry=geometry),
        optimizer=OptimizerSpec(name="cobyla", max_iterations=200),
        qubit_count=4 if molecule == Molecule.H2 else 10,
        parameter_count=3 if molecule == Molecule.H2 else 24,
        system_info={"platform": "test"},
        result=RunResult(
            energy=energy,
            iterations=n_iter,
            parameters=[0.1] * (3 if molecule == Molecule.H2 else 24),
            wall_time_seconds=wall_time,
            converged=True,
            reference_energy=-1.137270 if molecule == Molecule.H2 else -7.882362,
            error_vs_reference_hartree=energy
            - (-1.137270 if molecule == Molecule.H2 else -7.882362),
            chemical_accuracy_reached=True,
        ),
    )
    trace = IterationTrace(
        run_id=run_id,
        records=[
            IterationRecord(
                iteration=i,
                energy=energy + 0.01 * (n_iter - i),
                elapsed_seconds=wall_time * (i + 1) / n_iter,
                parameters=[0.1] * (3 if molecule == Molecule.H2 else 24),
            )
            for i in range(n_iter)
        ],
    )
    return manifest, trace


def test_summarize_run_computes_per_eval_time() -> None:
    manifest, trace = _make_manifest(
        run_id="r1", backend=BackendIdentifier.CPU, target="qpp-cpu", wall_time=2.0, n_iter=10
    )
    metrics = summarize_run(manifest, trace)
    assert metrics.function_evaluations == 10
    assert metrics.time_per_evaluation_ms == 200.0
    assert metrics.qubit_count == 4
    assert metrics.target_string == "qpp-cpu"


def test_default_blog_suite_uses_bumped_lih_iterations() -> None:
    from app.benchmark.runner import default_blog_suite

    suite = default_blog_suite(seeds=(42, 43, 44))
    h2_specs = [s for s in suite if s.experiment == "h2"]
    lih_specs = [s for s in suite if s.experiment == "lih"]
    assert len(h2_specs) == 9, "3 seeds x 3 backends for H2"
    assert len(lih_specs) == 6, "3 seeds x 2 backends for LiH"
    assert all(s.max_iterations == 200 for s in h2_specs), "H2 budget unchanged"
    assert all(s.max_iterations == 1500 for s in lih_specs), (
        "LiH bumped from 300 (Phase 7e) to 1500 so COBYLA can converge to chemical accuracy"
    )


def test_compare_groups_by_molecule_and_backend() -> None:
    cpu_manifest, cpu_trace = _make_manifest(
        run_id="r-cpu", backend=BackendIdentifier.CPU, target="qpp-cpu", wall_time=4.0, n_iter=40
    )
    save_manifest(cpu_manifest)
    save_trace(cpu_trace)

    gpu_manifest, gpu_trace = _make_manifest(
        run_id="r-gpu",
        backend=BackendIdentifier.GPU_FP64,
        target="nvidia:fp64",
        wall_time=1.0,
        n_iter=40,
    )
    save_manifest(gpu_manifest)
    save_trace(gpu_trace)

    report = compare_cpu_vs_gpu()
    assert "h2" in report["by_molecule"]
    h2 = report["by_molecule"]["h2"]
    assert "cpu" in h2["backends"]
    assert "gpu_fp64" in h2["backends"]
    speedup = h2["speedups"]["cpu_over_gpu_fp64_wall_time"]
    assert 3.5 < speedup < 4.5

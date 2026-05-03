"""Per-run benchmark metrics derived from a manifest + trace.

These are the numbers we plot in the UI and quote in the blog post.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.storage.manifests import IterationTrace, RunManifest


@dataclass(slots=True)
class RunMetrics:
    """Numbers derived from one ``(manifest, trace)`` pair."""

    run_id: str
    backend: str
    target_string: str
    molecule: str
    qubit_count: int
    parameter_count: int
    iterations: int
    function_evaluations: int
    wall_time_seconds: float
    time_per_evaluation_ms: float
    final_energy: float
    reference_energy: float | None
    error_vs_reference_hartree: float | None
    chemical_accuracy_reached: bool | None
    convergence_iterations: int | None = None
    notes: dict[str, object] = field(default_factory=dict)


def summarize_run(manifest: RunManifest, trace: IterationTrace) -> RunMetrics:
    """Build a :class:`RunMetrics` from a manifest + trace pair."""
    if manifest.result is None:
        raise ValueError(f"manifest {manifest.run_id} has no result yet")

    result = manifest.result
    fn_evals = max(len(trace.records), 1)
    time_per_eval_ms = (result.wall_time_seconds / fn_evals) * 1000.0

    return RunMetrics(
        run_id=manifest.run_id,
        backend=manifest.backend.value,
        target_string=manifest.target_string,
        molecule=manifest.molecule.name.value,
        qubit_count=manifest.qubit_count,
        parameter_count=manifest.parameter_count,
        iterations=result.iterations,
        function_evaluations=fn_evals,
        wall_time_seconds=result.wall_time_seconds,
        time_per_evaluation_ms=time_per_eval_ms,
        final_energy=result.energy,
        reference_energy=result.reference_energy,
        error_vs_reference_hartree=result.error_vs_reference_hartree,
        chemical_accuracy_reached=result.chemical_accuracy_reached,
        convergence_iterations=_first_chemical_accuracy_iteration(trace, result.reference_energy),
        notes=manifest.notes,
    )


def _first_chemical_accuracy_iteration(
    trace: IterationTrace, reference_energy: float | None
) -> int | None:
    """Iteration index where ``|energy - reference| < chemical accuracy``."""
    from app.quantum.reference_data import CHEMICAL_ACCURACY_HARTREE

    if reference_energy is None or not trace.records:
        return None
    for record in trace.records:
        if abs(record.energy - reference_energy) < CHEMICAL_ACCURACY_HARTREE:
            return record.iteration
    return None

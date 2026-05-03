"""H2 VQE experiment.

H2 / STO-3G is a 4-qubit / 3-parameter UCCSD problem. It converges to chemical
accuracy in well under a second on either backend. We use it both as the
"hello world" of the project and as the CI smoke test that proves the CPU
path is healthy.
"""

from __future__ import annotations

from collections.abc import Callable

from app.quantum.chemistry import H2_DEFAULT_BOND_DISTANCE, build_h2
from app.quantum.experiment import run_vqe
from app.storage.manifests import (
    BackendIdentifier,
    IterationRecord,
    IterationTrace,
    RunManifest,
)


def run_h2(
    *,
    backend_id: BackendIdentifier = BackendIdentifier.CPU,
    bond_distance: float = H2_DEFAULT_BOND_DISTANCE,
    basis: str = "sto-3g",
    seed: int = 42,
    max_iterations: int = 200,
    tolerance: float = 1e-6,
    initial_parameters: list[float] | None = None,
    on_iteration: Callable[[IterationRecord], None] | None = None,
    run_id: str | None = None,
) -> tuple[RunManifest, IterationTrace]:
    """Run the H2 VQE experiment with the given backend + options."""
    molecule = build_h2(bond_distance=bond_distance, basis=basis)
    return run_vqe(
        molecule=molecule,
        backend_id=backend_id,
        seed=seed,
        max_iterations=max_iterations,
        tolerance=tolerance,
        initial_parameters=initial_parameters,
        on_iteration=on_iteration,
        notes={"experiment": "h2_vqe"},
        run_id=run_id,
    )

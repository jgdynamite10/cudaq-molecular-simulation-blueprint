"""LiH VQE experiment.

LiH / STO-3G with the default (2 electron, 5 orbital) active space. The
Hamiltonian carries the active-space restriction, but the current UCCSD
ansatz path instantiates against the full molecule: 12 qubits /
92 parameters. A properly active-space-restricted ansatz would be
10 qubits / ~24 parameters; aligning the two is on the v0.2 follow-up
list. This is the workload that makes the CPU-vs-GPU comparison
meaningful: small enough to run on CPU as a baseline (~30 min per seed),
large enough that the GPU statevector simulator pulls ahead noticeably
(1.665x on Blackwell FP64).
"""

from __future__ import annotations

from collections.abc import Callable

from app.quantum.chemistry import LIH_DEFAULT_BOND_DISTANCE, build_lih
from app.quantum.experiment import run_vqe
from app.storage.manifests import (
    BackendIdentifier,
    IterationRecord,
    IterationTrace,
    RunManifest,
)


def run_lih(
    *,
    backend_id: BackendIdentifier = BackendIdentifier.GPU_FP64,
    bond_distance: float = LIH_DEFAULT_BOND_DISTANCE,
    basis: str = "sto-3g",
    n_core_orbitals: int | None = 1,
    n_active_orbitals: int | None = 5,
    seed: int = 42,
    max_iterations: int = 500,
    tolerance: float = 1e-6,
    initial_parameters: list[float] | None = None,
    on_iteration: Callable[[IterationRecord], None] | None = None,
    run_id: str | None = None,
) -> tuple[RunManifest, IterationTrace]:
    """Run the LiH VQE experiment with the given backend + options."""
    molecule = build_lih(
        bond_distance=bond_distance,
        basis=basis,
        n_core_orbitals=n_core_orbitals,
        n_active_orbitals=n_active_orbitals,
    )
    return run_vqe(
        molecule=molecule,
        backend_id=backend_id,
        seed=seed,
        max_iterations=max_iterations,
        tolerance=tolerance,
        initial_parameters=initial_parameters,
        on_iteration=on_iteration,
        notes={"experiment": "lih_vqe"},
        run_id=run_id,
    )

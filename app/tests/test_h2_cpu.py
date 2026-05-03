"""End-to-end CPU H2 VQE test.

Skipped when CUDA-Q is unavailable. When CUDA-Q is installed, the run must
converge to within chemical accuracy of the published H2/STO-3G FCI energy.
"""

from __future__ import annotations

import pytest

from app.tests.conftest import requires_cudaq


@requires_cudaq
@pytest.mark.slow
def test_h2_cpu_converges_to_chemical_accuracy() -> None:
    from app.quantum.h2_vqe import run_h2
    from app.quantum.reference_data import CHEMICAL_ACCURACY_HARTREE
    from app.storage.manifests import BackendIdentifier

    manifest, trace = run_h2(
        backend_id=BackendIdentifier.CPU,
        bond_distance=0.7414,
        seed=42,
        max_iterations=200,
    )

    assert manifest.result is not None
    result = manifest.result
    assert result.reference_energy is not None
    assert result.error_vs_reference_hartree is not None
    assert abs(result.error_vs_reference_hartree) < CHEMICAL_ACCURACY_HARTREE, (
        f"H2 CPU run did not reach chemical accuracy: "
        f"E={result.energy:.6f} ref={result.reference_energy:.6f} "
        f"err={result.error_vs_reference_hartree:+.2e} Ha"
    )
    assert result.chemical_accuracy_reached is True
    assert manifest.qubit_count == 4
    assert len(trace.records) > 0

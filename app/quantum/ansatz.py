"""UCCSD ansatz construction backed by CUDA-Q's built-in kernel.

We expose a single :func:`make_uccsd_kernel` factory that returns a CUDA-Q
kernel along with its parameter count. The kernel signature is fixed so the
optimizer-side cost function does not need to know about chemistry details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class UccsdAnsatz:
    """A built UCCSD ansatz ready to be passed to :func:`cudaq.observe`."""

    kernel: Any
    qubit_count: int
    electron_count: int
    parameter_count: int


def make_uccsd_kernel(qubit_count: int, electron_count: int) -> UccsdAnsatz:
    """Build the standard UCCSD ansatz on top of a Hartree-Fock reference.

    Returns a kernel whose signature is::

        kernel(thetas: list[float], electron_count: int, qubit_count: int) -> None

    The integer dimensions are passed in explicitly because CUDA-Q kernels do
    not support closing over Python ints from the enclosing scope.
    """
    import cudaq

    # Gate names like `x` and helpers like `qvector` are NOT importable from
    # the cudaq module - they are resolved by the kernel's AST bridge at
    # decoration time. We use bare names inside the kernel body.

    parameter_count = int(cudaq.kernels.uccsd_num_parameters(electron_count, qubit_count))

    @cudaq.kernel
    def kernel(thetas: list[float], n_electrons: int, n_qubits: int) -> None:
        qubits = cudaq.qvector(n_qubits)
        for i in range(n_electrons):
            x(qubits[i])  # noqa: F821 - resolved by @cudaq.kernel AST bridge
        cudaq.kernels.uccsd(qubits, thetas, n_electrons, n_qubits)

    return UccsdAnsatz(
        kernel=kernel,
        qubit_count=qubit_count,
        electron_count=electron_count,
        parameter_count=parameter_count,
    )

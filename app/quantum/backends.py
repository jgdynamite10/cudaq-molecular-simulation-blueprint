"""Backend abstraction over CUDA-Q simulator targets.

The blueprint intentionally exposes a small, named set of backends rather than
arbitrary CUDA-Q target strings. This is what keeps the core provider-agnostic:
a backend identifier is just a configuration choice, and the
target-string-to-CUDA-Q mapping is the only place that talks to the runtime.

Mapping in v1:

- ``cpu``      -> CUDA-Q ``qpp-cpu`` target (OpenMP CPU statevector).
- ``gpu_fp32`` -> CUDA-Q ``nvidia`` target, single precision (cuStateVec).
- ``gpu_fp64`` -> CUDA-Q ``nvidia`` target, double precision (cuStateVec).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.storage.manifests import BackendIdentifier

if TYPE_CHECKING:
    import cudaq  # noqa: F401


@dataclass(frozen=True, slots=True)
class BackendConfig:
    """Concrete CUDA-Q target settings for a logical backend identifier."""

    identifier: BackendIdentifier
    target: str
    target_option: str | None
    description: str

    def target_string(self) -> str:
        """Human-readable identifier persisted in run manifests."""
        if self.target_option:
            return f"{self.target}:{self.target_option}"
        return self.target


BACKEND_CONFIGS: dict[BackendIdentifier, BackendConfig] = {
    BackendIdentifier.CPU: BackendConfig(
        identifier=BackendIdentifier.CPU,
        target="qpp-cpu",
        target_option=None,
        description="OpenMP-parallel CPU statevector simulator.",
    ),
    BackendIdentifier.GPU_FP32: BackendConfig(
        identifier=BackendIdentifier.GPU_FP32,
        target="nvidia",
        target_option="fp32",
        description="cuStateVec single-precision GPU statevector simulator.",
    ),
    BackendIdentifier.GPU_FP64: BackendConfig(
        identifier=BackendIdentifier.GPU_FP64,
        target="nvidia",
        target_option="fp64",
        description="cuStateVec double-precision GPU statevector simulator.",
    ),
}


def get_backend_config(backend: BackendIdentifier) -> BackendConfig:
    return BACKEND_CONFIGS[backend]


def select_backend(backend: BackendIdentifier) -> BackendConfig:
    """Set the active CUDA-Q target globally.

    CUDA-Q maintains a process-wide target. This function is a thin wrapper
    around :func:`cudaq.set_target` so callers don't import ``cudaq``
    everywhere.
    """
    import cudaq  # imported lazily so the rest of the app stays importable on hosts without CUDA-Q

    config = get_backend_config(backend)
    if config.target_option is not None:
        cudaq.set_target(config.target, option=config.target_option)
    else:
        cudaq.set_target(config.target)
    return config


@contextmanager
def backend(backend_id: BackendIdentifier) -> Iterator[BackendConfig]:
    """Context manager that selects a backend and restores ``qpp-cpu`` on exit.

    CUDA-Q has no public "get current target" API, so we cannot perfectly
    restore the prior target. Restoring ``qpp-cpu`` is the safe default
    because it does not require GPU drivers and never raises.
    """
    config = select_backend(backend_id)
    try:
        yield config
    finally:
        with suppress(Exception):
            select_backend(BackendIdentifier.CPU)

"""Pydantic schemas for run manifests and per-iteration traces.

Manifests are the durable, JSON-serializable record of every experiment. They
capture *enough* information to fully reproduce a result on a new machine.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BackendIdentifier(StrEnum):
    """Logical backend identifiers exposed to users.

    The mapping to CUDA-Q target strings lives in :mod:`app.quantum.backends`.
    """

    CPU = "cpu"
    GPU_FP32 = "gpu_fp32"
    GPU_FP64 = "gpu_fp64"


class Molecule(StrEnum):
    """Supported molecules in v1."""

    H2 = "h2"
    LIH = "lih"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MoleculeSpec(BaseModel):
    """Concrete molecule specification embedded in a manifest."""

    model_config = ConfigDict(frozen=True)

    name: Molecule
    geometry: list[tuple[str, tuple[float, float, float]]]
    basis: str = "sto-3g"
    charge: int = 0
    multiplicity: int = 1
    active_electrons: int | None = None
    active_orbitals: int | None = None


class OptimizerSpec(BaseModel):
    """Optimizer configuration embedded in a manifest."""

    model_config = ConfigDict(frozen=True)

    name: str = "cobyla"
    max_iterations: int = 200
    tolerance: float | None = None
    initial_parameters: list[float] | None = None


class IterationRecord(BaseModel):
    """A single VQE iteration: parameters in, expectation value out."""

    model_config = ConfigDict(frozen=True)

    iteration: int
    energy: float
    elapsed_seconds: float
    parameters: list[float] | None = None


class IterationTrace(BaseModel):
    """Ordered list of per-iteration records for one VQE run."""

    run_id: str
    records: list[IterationRecord] = Field(default_factory=list)


class RunResult(BaseModel):
    """The final outcome of a VQE run."""

    model_config = ConfigDict(frozen=True)

    energy: float
    iterations: int
    parameters: list[float]
    wall_time_seconds: float
    converged: bool
    reference_energy: float | None = None
    error_vs_reference_hartree: float | None = None
    chemical_accuracy_reached: bool | None = None


class RunManifest(BaseModel):
    """Top-level manifest written for every experiment run.

    Stored at ``results/<run_id>/manifest.json`` alongside the iteration trace.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    schema_version: str = "1.0"
    run_id: str
    project_name: str = "cudaq-molecular-simulation-blueprint"
    project_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: RunStatus = RunStatus.PENDING

    backend: BackendIdentifier
    target_string: str
    seed: int

    molecule: MoleculeSpec
    optimizer: OptimizerSpec
    qubit_count: int
    parameter_count: int

    system_info: dict[str, Any]

    result: RunResult | None = None
    error: str | None = None

    notes: dict[str, Any] = Field(default_factory=dict)

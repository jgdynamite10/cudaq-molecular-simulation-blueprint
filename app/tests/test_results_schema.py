"""Manifest + trace round-trip tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.storage.filesystem import (
    list_runs,
    load_manifest,
    load_trace,
    new_run_id,
    save_manifest,
    save_trace,
)
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


def _make_manifest() -> RunManifest:
    return RunManifest(
        run_id=new_run_id(),
        project_version="0.1.0",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        status=RunStatus.COMPLETED,
        backend=BackendIdentifier.CPU,
        target_string="qpp-cpu",
        seed=42,
        molecule=MoleculeSpec(
            name=Molecule.H2,
            geometry=[("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.7414))],
        ),
        optimizer=OptimizerSpec(name="cobyla", max_iterations=200),
        qubit_count=4,
        parameter_count=3,
        system_info={"platform": "test"},
        result=RunResult(
            energy=-1.137,
            iterations=10,
            parameters=[0.1, 0.2, 0.3],
            wall_time_seconds=0.42,
            converged=True,
            reference_energy=-1.137270,
            error_vs_reference_hartree=2.7e-4,
            chemical_accuracy_reached=True,
        ),
    )


def test_round_trip_manifest(tmp_path: Path) -> None:
    manifest = _make_manifest()
    path = save_manifest(manifest)
    assert path.exists()
    loaded = load_manifest(manifest.run_id)
    assert loaded.run_id == manifest.run_id
    assert loaded.backend == BackendIdentifier.CPU
    assert loaded.result is not None
    assert loaded.result.chemical_accuracy_reached is True


def test_round_trip_trace() -> None:
    run_id = new_run_id()
    trace = IterationTrace(
        run_id=run_id,
        records=[
            IterationRecord(iteration=0, energy=-1.0, elapsed_seconds=0.01, parameters=[0.0]),
            IterationRecord(iteration=1, energy=-1.1, elapsed_seconds=0.02, parameters=[0.1]),
        ],
    )
    save_trace(trace)
    loaded = load_trace(run_id)
    assert len(loaded.records) == 2
    assert loaded.records[1].energy == -1.1


def test_list_runs_returns_newest_first() -> None:
    m1 = _make_manifest()
    save_manifest(m1)
    m2 = _make_manifest()
    save_manifest(m2)
    runs = list_runs()
    assert len(runs) >= 2
    assert runs[0].run_id >= runs[-1].run_id


def test_manifest_serialization_is_valid_json(tmp_path: Path) -> None:
    manifest = _make_manifest()
    path = save_manifest(manifest)
    with path.open() as fp:
        data = json.load(fp)
    assert data["backend"] == "cpu"
    assert data["target_string"] == "qpp-cpu"
    assert "system_info" in data

"""``cudaq-bp`` command-line entry point.

Subcommands:

- ``run h2``      Run an H2 VQE experiment.
- ``run lih``     Run an LiH VQE experiment.
- ``results list``     List previous runs.
- ``results show <id>`` Print a manifest.
- ``bench compare``    Generate a CPU vs GPU comparison report.
- ``info``        Print system + GPU detection summary.
"""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.system_info import collect_system_info
from app.storage.filesystem import (
    list_runs,
    load_manifest,
    load_trace,
    save_manifest,
    save_trace,
)
from app.storage.manifests import BackendIdentifier

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="cudaq-molecular-simulation-blueprint - hybrid quantum-classical VQE on CPU or GPU.",
)
run_app = typer.Typer(help="Run an experiment.", no_args_is_help=True)
results_app = typer.Typer(help="Inspect past runs.", no_args_is_help=True)
bench_app = typer.Typer(help="Benchmark utilities.", no_args_is_help=True)

app.add_typer(run_app, name="run")
app.add_typer(results_app, name="results")
app.add_typer(bench_app, name="bench")

console = Console()
log = get_logger("cli")


def _parse_backend(value: str) -> BackendIdentifier:
    aliases = {
        "cpu": BackendIdentifier.CPU,
        "qpp-cpu": BackendIdentifier.CPU,
        "gpu": BackendIdentifier.GPU_FP64,
        "gpu_fp32": BackendIdentifier.GPU_FP32,
        "nvidia": BackendIdentifier.GPU_FP32,
        "gpu_fp64": BackendIdentifier.GPU_FP64,
        "nvidia-fp64": BackendIdentifier.GPU_FP64,
    }
    key = value.strip().lower()
    if key not in aliases:
        raise typer.BadParameter(f"unknown backend '{value}'. Valid: {', '.join(aliases)}")
    return aliases[key]


def _summarize(manifest, trace) -> None:  # type: ignore[no-untyped-def]
    table = Table(title=f"Run {manifest.run_id}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("backend", manifest.backend.value)
    table.add_row("target", manifest.target_string)
    table.add_row("molecule", manifest.molecule.name.value)
    table.add_row("qubits", str(manifest.qubit_count))
    table.add_row("parameters", str(manifest.parameter_count))
    if manifest.result is not None:
        r = manifest.result
        table.add_row("energy [Ha]", f"{r.energy:.6f}")
        if r.reference_energy is not None:
            table.add_row("reference [Ha]", f"{r.reference_energy:.6f}")
            table.add_row("error [Ha]", f"{r.error_vs_reference_hartree:+.2e}")
            table.add_row(
                "chemical accuracy",
                "yes" if r.chemical_accuracy_reached else "no",
            )
        table.add_row("iterations", str(r.iterations))
        table.add_row("wall time [s]", f"{r.wall_time_seconds:.3f}")
    table.add_row("function evaluations", str(len(trace.records)))
    console.print(table)


@app.callback()
def _root(
    log_level: str = typer.Option(None, "--log-level", help="Override CUDAQ_BP_LOG_LEVEL."),
) -> None:
    settings = get_settings()
    configure_logging(level=log_level or settings.log_level)


@app.command("info")
def info() -> None:
    """Print system + GPU detection summary."""
    info = collect_system_info()
    console.print(Panel.fit(json.dumps(info.to_dict(), indent=2), title="system info"))


@run_app.command("h2")
def run_h2_cmd(
    backend: str = typer.Option("cpu", "--backend", "-b", help="cpu | gpu_fp32 | gpu_fp64"),
    bond_distance: float = typer.Option(0.7414, "--bond-distance", help="H-H distance in Angstrom"),
    seed: int = typer.Option(42, "--seed"),
    max_iterations: int = typer.Option(200, "--max-iterations"),
) -> None:
    """Run the H2 VQE experiment."""
    from app.quantum.h2_vqe import run_h2  # imported lazily to avoid cudaq import cost

    backend_id = _parse_backend(backend)
    log.info("h2_run.start", backend=backend_id.value, seed=seed)
    manifest, trace = run_h2(
        backend_id=backend_id,
        bond_distance=bond_distance,
        seed=seed,
        max_iterations=max_iterations,
    )
    save_manifest(manifest)
    save_trace(trace)
    log.info("h2_run.completed", run_id=manifest.run_id)
    _summarize(manifest, trace)


@run_app.command("lih")
def run_lih_cmd(
    backend: str = typer.Option("gpu_fp64", "--backend", "-b", help="cpu | gpu_fp32 | gpu_fp64"),
    bond_distance: float = typer.Option(
        1.5957, "--bond-distance", help="Li-H distance in Angstrom"
    ),
    n_core_orbitals: int | None = typer.Option(
        1, "--core-orbitals", help="Number of frozen core orbitals; pass 0 to disable"
    ),
    n_active_orbitals: int | None = typer.Option(
        5, "--active-orbitals", help="Number of active spatial orbitals"
    ),
    seed: int = typer.Option(42, "--seed"),
    max_iterations: int = typer.Option(500, "--max-iterations"),
) -> None:
    """Run the LiH VQE experiment."""
    from app.quantum.lih_vqe import run_lih  # imported lazily

    backend_id = _parse_backend(backend)
    core = n_core_orbitals if (n_core_orbitals and n_core_orbitals > 0) else None
    active = n_active_orbitals if (n_active_orbitals and n_active_orbitals > 0) else None
    log.info("lih_run.start", backend=backend_id.value, seed=seed)
    manifest, trace = run_lih(
        backend_id=backend_id,
        bond_distance=bond_distance,
        n_core_orbitals=core,
        n_active_orbitals=active,
        seed=seed,
        max_iterations=max_iterations,
    )
    save_manifest(manifest)
    save_trace(trace)
    log.info("lih_run.completed", run_id=manifest.run_id)
    _summarize(manifest, trace)


@results_app.command("list")
def results_list() -> None:
    """List all runs in the configured results directory."""
    runs = list_runs()
    if not runs:
        console.print("[yellow]No runs found in results directory.[/yellow]")
        return
    table = Table(title=f"{len(runs)} runs")
    table.add_column("run_id")
    table.add_column("molecule")
    table.add_column("backend")
    table.add_column("status")
    table.add_column("energy")
    table.add_column("iters")
    table.add_column("wall (s)")
    for m in runs:
        e = f"{m.result.energy:.4f}" if m.result else "-"
        it = str(m.result.iterations) if m.result else "-"
        wt = f"{m.result.wall_time_seconds:.2f}" if m.result else "-"
        table.add_row(m.run_id, m.molecule.name.value, m.backend.value, m.status.value, e, it, wt)
    console.print(table)


@results_app.command("show")
def results_show(run_id: str = typer.Argument(...)) -> None:
    """Print the manifest for a single run."""
    manifest = load_manifest(run_id)
    trace = load_trace(run_id)
    _summarize(manifest, trace)


@bench_app.command("compare")
def bench_compare(
    output: str = typer.Option(
        "results/blog/cpu_vs_gpu.json",
        "--output",
        "-o",
        help="Output path for the comparison report.",
    ),
) -> None:
    """Generate a CPU vs GPU comparison report from existing runs."""
    from app.benchmark.compare import compare_cpu_vs_gpu  # imported lazily

    report = compare_cpu_vs_gpu()
    from pathlib import Path

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    console.print(f"[green]Wrote[/green] {path}")


if __name__ == "__main__":  # pragma: no cover
    app()

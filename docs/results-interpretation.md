# Results interpretation

## What the charts show

The `/compare` page (and the JSON written by `cudaq-bp bench compare`) renders
two views per molecule:

1. **Wall time per run** - mean ± standard error across seeds, per backend.
2. **Absolute error vs reference** - on a log scale, one bar per backend.

Both views are derived from the per-run manifests, which already contain
the fields. There is no derived "secret sauce" - the JSON is the chart.

## What the numbers mean

| field                          | meaning                                                              |
|--------------------------------|----------------------------------------------------------------------|
| `wall_time_seconds`            | total time the optimizer ran on that backend, end to end             |
| `time_per_evaluation_ms`       | wall_time / function_evaluations - per-statevector throughput proxy  |
| `iterations`                   | outer COBYLA iterations until termination                            |
| `error_vs_reference_hartree`   | `final_energy - reference_energy` (Hartree)                          |
| `chemical_accuracy_reached`    | `\|error\| < 1.6 mHa`                                                 |

`speedups` in the comparison report quote the ratio of CPU mean wall time
to each non-CPU backend's mean wall time, e.g. `cpu_over_gpu_fp64_wall_time`.

## What the numbers do NOT mean

This project is built around very specific framing. The charts are evidence
of a hybrid quantum-classical workflow being practical *today on GPU
infrastructure*, not evidence of any of the following:

- **Quantum advantage.** None of these workloads are at quantum-advantage
  scale. STO-3G H2 has a 4×4 Hamiltonian; the FCI energy can be computed
  in microseconds in literally any way. We are using H2 as a *correctness*
  smoke test, not as a benchmark target.
- **GPU vs QPU.** This project does not run on a QPU. The "QPU" in the
  blog title is a future-state stand-in; today, we simulate quantum circuits
  classically (which is what the entire industry does for practical work).
- **NVIDIA vs other vendors.** No comparison against other GPU vendors,
  cloud providers, or CPU architectures is published here. The CPU path
  uses CUDA-Q's own `qpp-cpu` so the only thing changing between backends is
  the simulator target string.
- **Akamai vs other clouds.** This project does not run on other clouds for
  v1 and makes no claim about cross-cloud performance.

## Reading the bond-distance results

The bond distance matters: VQE is a function minimizer of energy *at a fixed
geometry*. Picking a geometry far from equilibrium will give a higher
energy - that's not a bug. The reference energy in the manifest is matched
against the same geometry, so the *error* column is the apples-to-apples
quantity to compare.

## Reading active-space results

For LiH the default active space is `(2 active electrons, 5 active
orbitals)` with the lithium 1s frozen as core. The reported energy converges
to the **CASCI(2e,5o) energy**, not to full FCI. The reference table in
`app/quantum/reference_data.py` reflects this, so chemical accuracy is
measured against the right target.

If you pass `--core-orbitals 0 --active-orbitals 0`, you get full LiH (12
qubits, more parameters, no active-space approximation), and the manifest
will reference full FCI instead.

## Sample size and noise

Each run is deterministic for a given seed (COBYLA is seeded; CUDA-Q
statevector simulation is deterministic). The "noise" reflected in
`stderr` columns therefore comes from optimizer-initial-condition variance
across different seeds, not stochastic shot noise. We deliberately use
`shots=0` (i.e. exact statevector observable) for this study; shot-based
runs would introduce another axis of variance that's outside the v1 scope.

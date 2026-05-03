# Experiment methodology

## Why H2 and LiH

These two molecules give us a credible CPU-vs-GPU story without making
unsupportable claims:

- **H2 / STO-3G** is the textbook 4-qubit / ~3-parameter UCCSD problem.
  Both backends should converge to chemical accuracy in well under a second.
  H2 is the smoke test that proves the pipeline is correct end-to-end.
- **LiH / STO-3G** with the default (2 electron / 5 orbital) active space is
  a 10-qubit / ~24-parameter problem. The CPU statevector simulator is
  noticeably slower than the GPU here; on a single Blackwell, the ratio is
  large enough to be visible in plots, but small enough that the CPU run is
  still feasible as a baseline (no waiting tens of minutes).

We deliberately do **not** include molecules where CPU simulation becomes
intractable (BeH2, H2O, larger). That would force us to compare GPU runs
against extrapolations rather than measured CPU baselines, which is not what
this project is for.

## Method choices

| concern             | choice                                | why                                                 |
|---------------------|----------------------------------------|----------------------------------------------------|
| basis set           | STO-3G                                 | minimal, reproducible across QC papers              |
| Hamiltonian builder | `cudaq.chemistry.create_molecular_hamiltonian` | first-class CUDA-Q API; uses OpenFermion under the hood |
| ansatz              | UCCSD via `cudaq.kernels.uccsd`        | physically motivated for chemistry                  |
| reference state     | Hartree-Fock                           | standard initial state                              |
| optimizer           | COBYLA (SciPy)                         | gradient-free, exposes a real per-eval trace        |
| convergence test    | `\|E_VQE - E_FCI\| < 1.6e-3 Ha`         | chemical accuracy threshold                         |
| RNG seed            | configurable (default 42)              | stamped into every manifest for reproducibility     |
| seeds per backend   | 5 (default in `default_blog_suite`)    | mean +/- standard error in the comparison           |

## What is measured

For every run we record:

- **wall_time_seconds** - end-to-end time of the optimizer.
- **iterations** - number of outer COBYLA iterations.
- **function_evaluations** - number of `cudaq.observe` calls.
- **time_per_evaluation_ms** - wall_time / function_evaluations.
- **final_energy** - the optimizer's `result.fun`.
- **error_vs_reference_hartree** - `final_energy - E_reference`, where
  the reference comes from `app/quantum/reference_data.py` (published FCI
  values for the chosen geometry).
- **chemical_accuracy_reached** - `|error| < 1.6 mHa`.

The trace also stores every evaluation's `(iteration, energy,
elapsed_seconds, parameters)` so the UI can render convergence curves and the
benchmark harness can compute time-to-convergence.

## Reference values

`app/quantum/reference_data.py` ships with published reference energies
keyed by `(molecule, basis, bond_distance, active_space)`. Bond distance is
matched within 0.01 Å so minor user perturbations still find the correct
reference.

| molecule | basis  | R (Å)  | active space | method     | E (Ha)        |
|----------|--------|--------|--------------|------------|---------------|
| H2       | STO-3G | 0.7414 | full         | FCI        | -1.137270     |
| H2       | STO-3G | 0.7474 | full         | FCI        | -1.137275     |
| LiH      | STO-3G | 1.5957 | full         | FCI        | -7.882362     |
| LiH      | STO-3G | 1.5957 | (2e, 5o)     | CASCI      | -7.862500     |

If a user picks an unusual geometry, the reference is `None` and only the
absolute energy is reported (no error column).

## Running the canonical suite

```bash
# CPU only - works everywhere
cudaq-bp run h2 --backend cpu

# CPU + GPU on the Blackwell host (after Akamai bootstrap)
cudaq-bp run h2  --backend gpu_fp64
cudaq-bp run lih --backend gpu_fp64

# Multi-seed sweep that drives the blog charts
python -m app.benchmark.runner  # or write your own driver script
cudaq-bp bench compare           # writes results/blog/cpu_vs_gpu.json
```

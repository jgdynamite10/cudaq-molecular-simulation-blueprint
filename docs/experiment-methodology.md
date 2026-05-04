# Experiment methodology

## Why H2 and LiH

These two molecules give us a credible CPU-vs-GPU story without making
unsupportable claims:

- **H2 / STO-3G** is the textbook 4-qubit / 3-parameter UCCSD problem.
  Both backends converge to chemical accuracy in seconds to tens of seconds
  in this implementation; on the Blackwell host used for the multi-seed
  bench, H2 finishes in ~13–18 s wall time per run depending on backend
  and precision. H2 is the smoke test that proves the pipeline is correct
  end-to-end.
- **LiH / STO-3G** with the default (2 electron / 5 orbital) active space.
  In theory the active space corresponds to a 10-qubit / ~24-parameter
  problem, but the current LiH ansatz is instantiated against the full
  molecule (n_qubits=12, n_electrons=4) before the active-space
  Hamiltonian is applied, so the actual circuit recorded in every multi-seed
  manifest is **12 qubits / 92 UCCSD parameters**. Closing that gap (a
  properly active-space-restricted ansatz of 10 qubits / ~24 parameters) is
  on the v0.2 follow-up list. The CPU statevector simulator is noticeably
  slower than the GPU here: CPU runs take ~30 minutes per seed (1500
  iterations of COBYLA), GPU FP64 runs take ~18 minutes. The CPU baseline
  remains feasible &mdash; you can leave it running over a coffee &mdash;
  but it is now long enough to expose meaningful GPU wall-time savings
  rather than being a sub-second curiosity.

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
| seeds per backend   | 3 (default in `default_blog_suite`; H2 budget 200 iter, LiH 1500 iter) | mean +/- standard error in the comparison; LiH was bumped from 300 to 1500 after the v0.1.0 trace inspection showed COBYLA was still descending steadily at iter 300 |

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

`app/quantum/reference_data.py` ships with reference energies keyed by
`(molecule, basis, bond_distance, active_space)`. Bond distance is matched
within 0.01 Å so minor user perturbations still find the correct
reference.

The LiH references were recomputed via PySCF on 2026-05-04 (RHF + CASCI on
the equilibrium geometry) so any reader with `pip install pyscf` can
reproduce them locally. The earlier shipped LiH (2e, 5o) value of
-7.862500 Ha was effectively the HF energy and was off by ~19.7 mHa; it
has been replaced.

| molecule | basis  | R (Å)  | active space | method                            | E (Ha)        |
|----------|--------|--------|--------------|-----------------------------------|---------------|
| H2       | STO-3G | 0.7414 | full         | FCI                               | -1.137270     |
| H2       | STO-3G | 0.7474 | full         | FCI                               | -1.137275     |
| LiH      | STO-3G | 1.5957 | full         | FCI (pyscf 2026-05-04)            | -7.882391     |
| LiH      | STO-3G | 1.5957 | (2e, 5o)     | CASCI(2e,5o) (pyscf 2026-05-04)   | -7.882164     |

The CASCI(2e,5o) and full-FCI minima for LiH/STO-3G at this geometry are
only 0.227 mHa apart, so the (2e, 5o) active space already captures
essentially all of the FCI correlation. Any error larger than ~1 mHa
against CASCI(2e,5o) in this active space is therefore optimizer / ansatz
residual rather than active-space frozen-core error.

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

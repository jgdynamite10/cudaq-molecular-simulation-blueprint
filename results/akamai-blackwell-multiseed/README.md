# Akamai Blackwell multi-seed bench results (2026-05-04)

This directory contains the lightweight, committed summary of the
multi-seed re-bench described in the project README and blog post. The
full per-run manifests + traces (~45 MiB) are not in the repository.

## Files

| file | description |
|---|---|
| [`SUMMARY.csv`](SUMMARY.csv) | One row per run (15 rows). Columns: `run_id`, `molecule`, `backend`, `seed`, `qubits`, `parameters`, `iterations`, `wall_seconds`, `energy_hartree`, `reference_method`, `reference_hartree`, `error_mhartree`, `chemical_accuracy_reached`. |
| [`comparison.json`](comparison.json) | Aggregates: mean ± stderr per backend group, GPU/CPU speedups, host fingerprint, reference recomputation note. |

## Run conditions

- 3 RNG seeds per backend (42, 43, 44)
- 5 backend/molecule combinations
- 15 runs total
- Hardware: Akamai Cloud `g3-gpu-rtxpro6000-blackwell-1` in `id-cgk` (Jakarta)
- GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition, 96 GB VRAM
- Driver: `nvidia-open-580.159.03` (max-supported CUDA 13.0 per `nvidia-smi`)
- Container: `cuda-quantum-cu13` wheels on top of `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04`

## How references are computed

The `reference_hartree` column was recomputed with PySCF on 2026-05-04
(`pyscf.scf.RHF` + `pyscf.mcscf.CASCI`) so anyone with `pip install
pyscf` can reproduce it locally:

```python
from pyscf import gto, scf, mcscf

mol = gto.M(atom="Li 0 0 0; H 0 0 1.5957", basis="sto-3g")
mf = scf.RHF(mol).run()

# Active-space (2e, 5o) reference used in error_mhartree
e_casci_2e5o = mcscf.CASCI(mf, 5, 2).kernel()[0]
# -> -7.882164 Ha

# Full FCI (for comparison)
e_fci = mcscf.CASCI(mf, mol.nao, mol.nelectron).kernel()[0]
# -> -7.882391 Ha
```

The legacy "literature estimate" of -7.862500 Ha that shipped in v0.1.0
was effectively the HF energy and was approximately 19.7 mHa above the
true CASCI(2e, 5o) minimum. It has been replaced.

## Important caveats

- **No LiH run reaches chemical accuracy** of either CASCI(2e,5o) or full
  FCI in this bench. The two converged seeds (42, 43) sit ~6 mHa above
  CASCI(2e,5o); seed 44 lands in a separate basin ~126 mHa above. The
  remaining ~6 mHa gap is **optimizer / ansatz-overparametrization
  residual**, not active-space frozen-core error: the (2e,5o) → full FCI
  gap is only 0.227 mHa at this geometry.
- **All 9 H2 runs reach chemical accuracy** (\|err\| < 1.6 mHa).
- The full per-run trace (`trace.json`, 200–615 KiB each) is not
  committed; if you need it, re-run the bench (`uv run cudaq-bp bench
  run-suite --seeds 42,43,44`) or ask the maintainer for the bench
  tarball.

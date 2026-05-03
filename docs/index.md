# cudaq-molecular-simulation-blueprint

> Hybrid quantum-classical molecular simulation reference using NVIDIA
> CUDA-Q and cuQuantum, validated end-to-end on Akamai Cloud NVIDIA RTX
> PRO 6000 Blackwell GPUs.

This site is the long-form companion to the
[GitHub repository](https://github.com/jgdynamite/cudaq-molecular-simulation-blueprint).
It supports the technical blog post **"Why GPUs Matter to Quantum Before
QPUs Do: Using CUDA-Q, cuQuantum, and Blackwell GPUs for Molecular
Simulation"** by making the hybrid quantum workflow concrete, runnable,
and reproducible.

## Validated on Blackwell (Jakarta, 2026-05-03)

A `g3-gpu-rtxpro6000-blackwell-1` VM in Akamai's `id-cgk` region, NVIDIA
driver `nvidia-open-580.159.03`, CUDA 13.0, 96 GB VRAM, 16 vCPU, 172 GB
system RAM. VM lifetime 1 h 17 min, billed cost **$3.84**.

| Run | Backend | Qubits | Wall (s) | Energy (Ha) | Error vs FCI |
|---|---|---:|---:|---:|---:|
| H2  | `qpp-cpu`     |  4 | **17.07** | -1.137270 | -1.75e-07 |
| H2  | `nvidia:fp64` |  4 |     19.19 | -1.137270 | -1.75e-07 |
| LiH | `qpp-cpu`     | 12 |    362.02 | -7.579105 | +2.83e-01 |
| LiH | `nvidia:fp64` | 12 | **211.68** | -7.579105 | +2.83e-01 |

H2 (4 qubits) GPU is 12% slower than CPU - host<->device transfer
dominates. LiH (12 qubits) GPU is **1.71x faster** than CPU on identical
COBYLA trajectories - this is the crossover the project sets out to
make concrete. See [Results interpretation](results-interpretation.md)
for the full discussion.

## Documentation

- [Project charter](project-charter.md) - what this project is and isn't
- [Architecture](architecture.md) - module boundaries and the CUDA-Q backend abstraction
- [Experiment methodology](experiment-methodology.md) - VQE setup, basis, ansatz, optimizer
- [Akamai deployment](akamai-deployment.md) - Terraform + Ansible walkthrough
- [Results interpretation](results-interpretation.md) - what the bench numbers do and don't say
- [Scope and non-goals](scope-and-non-goals.md) - explicit guardrails for v1
- [Blog support notes](blog-support-notes.md) - notes for the companion blog post

## Quick start

```bash
git clone https://github.com/jgdynamite/cudaq-molecular-simulation-blueprint.git
cd cudaq-molecular-simulation-blueprint
make container-build
make container-run-cpu       # H2 VQE on qpp-cpu (~15-20 s)
make serve                   # demo UI at http://localhost:8000
```

CUDA-Q's Python wheel ships only Linux x86_64/ARM64 binaries. On macOS or
any other platform without those wheels, use the Docker path above; the
container handles the Linux runtime transparently.

## Reproducibility

Every run produces a JSON manifest capturing CUDA-Q version, target string,
GPU model, driver version, OS, container digest, git SHA, RNG seed,
optimizer settings, basis set, geometry, and active space. CI reproduces
the H2 CPU result on every push, and the release workflow publishes the
canonical container image to
`ghcr.io/jgdynamite/cudaq-molecular-simulation-blueprint:<tag>` so any
reader can pull-and-run the exact bits used in the blog post.

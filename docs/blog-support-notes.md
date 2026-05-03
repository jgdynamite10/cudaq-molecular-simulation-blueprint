# Blog support notes

Companion notes for the technical blog post:
**"Why GPUs Matter to Quantum Before QPUs Do: Using CUDA-Q, cuQuantum, and
Blackwell GPUs for Molecular Simulation."**

## Recommended figure inventory

Generate these from the canonical multi-seed run on the Akamai Blackwell VM
once Phase 7 is complete:

1. **Architecture diagram** - the mermaid diagram in
   [`architecture.md`](architecture.md), exported as PNG.
2. **Hybrid pipeline sequence diagram** - the second mermaid diagram in
   [`architecture.md`](architecture.md).
3. **Convergence curve, H2 CPU vs GPU FP64** - both lines on one Plotly
   chart with the FCI reference dashed in. Screenshot from `/run` after a
   live run.
4. **Convergence curve, LiH GPU FP64** - same layout, GPU only.
5. **Bar chart: wall time per backend, H2** - from `/compare`.
6. **Bar chart: wall time per backend, LiH** - from `/compare`.
7. **Bar chart: error vs reference (log scale), per backend** - from
   `/compare` (already in the UI).
8. **Side-by-side screenshot** of `/results` showing the run table with
   CPU and GPU runs interleaved.
9. **Manifest snippet** - paste of one `manifest.json` showing CUDA-Q
   version, GPU model, driver, seed, etc., for the "this is reproducible"
   beat in the post.

## Talking points the project supports

These are claims you can defend with the artifacts produced by this repo.
None of them are quantum-advantage claims.

- "Practical quantum work today is hybrid: CPU does the chemistry
  preprocessing, the GPU runs the statevector simulator, the QPU is a future
  optional stage. The same code in this repo runs on CPU and on GPU; only
  the target string changes."
- "On a single Blackwell GPU, the same VQE code runs LiH measurably faster
  than the CPU baseline." Quote the speedup factor from
  `results/blog/cpu_vs_gpu.json`.
- "The workload is small enough to be honest. We are not extrapolating; the
  CPU baseline actually finishes."
- "Akamai Cloud can host a modern Blackwell-class scientific workload with
  off-the-shelf Terraform + Ansible. Single VM, single GPU, single Docker
  container."
- "The application is provider-agnostic. The same image runs locally on a
  laptop in CPU mode and on the Blackwell VM in GPU mode."

## Things to NOT claim

These are explicit non-goals. Do not let the blog post drift into them.

- "Quantum advantage" or any synonym.
- "Akamai is a quantum cloud" / "Akamai is the quantum cloud."
- "Benchmark against H100 / B200 / other clouds." Cross-provider comparisons
  are out of scope. The benchmark in this repo is `qpp-cpu` vs `nvidia` on
  the *same VM*.
- Any unsupported claim about NVIDIA roadmap, future Blackwell variants, or
  upcoming CUDA-Q features.

## Suggested post structure

1. **Hook**: hybrid is the practical reality. (Cite what real teams ship.)
2. **What is hybrid here?** Pipeline diagram.
3. **The workloads**: H2 and LiH at STO-3G with UCCSD-VQE.
4. **Show, don't tell**: live convergence curve screenshots; the `/run` page
   is built for this.
5. **CPU vs GPU baseline on the same VM**: bar charts, mean ± stderr.
6. **Reproducibility**: paste a manifest, point at the public repo.
7. **Akamai Blackwell as the substrate**: brief deployment story; the same
   image runs locally on a laptop in CPU mode.
8. **What's next**: enlarge active spaces, multi-GPU, LKE - explicit v2
   territory.

## Pre-publish review checklist

- [ ] Every chart in the post has a one-line "n=5 seeds" footnote where it
      summarizes runs.
- [ ] Every quoted speedup matches the value in `results/blog/cpu_vs_gpu.json`.
- [ ] The "not a quantum advantage claim" sentence is in the post.
- [ ] The repo is public and the README quick-start works on a clean machine.
- [ ] The `infra/` directory contains nothing internal/unsupported about
      Akamai.
- [ ] No NVIDIA, Akamai, or quantum-vendor logos used without proper
      attribution / permission.

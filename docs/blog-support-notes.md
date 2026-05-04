# Blog support notes

Companion notes for the technical blog post:
**"Why GPUs Matter to Quantum Before QPUs Do: Using CUDA-Q, cuQuantum, and
Blackwell GPUs for Molecular Simulation."**

## Recommended figure inventory

Four screenshots from the multi-seed bench already live in `docs/images/`
and are embedded in both the README and the blog draft:

1. `01-home.png` - home page with the Akamai Blackwell host fingerprint
   visible.
2. `02-compare.png` - `/compare` view: wall time per backend and error vs
   reference per backend.
3. `03-results-list.png` - `/results` table with all 15 multi-seed runs
   interleaved (3 H2 CPU, 3 H2 FP32, 3 H2 FP64, 3 LiH CPU, 3 LiH FP64).
4. `04-result-lih-gpu.png` - one LiH GPU run detail page showing the full
   1500-iteration COBYLA convergence curve.

If you want additional figures for a longer post, generate them from the
canonical multi-seed run:

5. **Architecture diagram** - the mermaid diagram in
   [`architecture.md`](architecture.md), exported as PNG.
6. **Hybrid pipeline sequence diagram** - the second mermaid diagram in
   [`architecture.md`](architecture.md).
7. **Convergence curve, H2 CPU vs GPU FP64** - both lines on one Plotly
   chart with the FCI reference dashed in. Screenshot from `/run` after a
   live run.
8. **Manifest snippet** - paste of one `manifest.json` showing CUDA-Q
   version, GPU model, driver, seed, etc., for the "this is reproducible"
   beat in the post.

## Talking points the project supports

These are claims you can defend with the artifacts produced by this repo.
None of them are quantum-advantage claims.

- "Practical quantum work today is hybrid: CPU does the chemistry
  preprocessing, the GPU runs the statevector simulator, the QPU is a future
  optional stage. The same code in this repo runs on CPU and on GPU; only
  the target string changes."
- "On a single Blackwell GPU, the same VQE code runs LiH ~1.665x faster than
  the CPU baseline (n=3 seeds, stderr ~0.4% relative)." Numbers come from
  the committed `results/akamai-blackwell-multiseed/SUMMARY.csv` and
  `comparison.json` in the repository.
- "The workload is small enough to be honest. We are not extrapolating; the
  CPU baseline actually finishes."
- "No LiH run reaches chemical accuracy in this bench, even at 1500 COBYLA
  iterations. The converged seeds 42 and 43 sit ~6 mHa above the
  PySCF-computed CASCI(2e,5o) reference, and seed 44 lands ~126 mHa above
  in a separate basin. This is honest about the optimizer / over-
  parametrization residual rather than papering over it."
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

- [ ] Every chart in the post has a one-line "n=3 seeds" footnote where it
      summarizes runs (the multi-seed bench used 3 RNG seeds per backend).
- [ ] Every quoted speedup matches the value in
      `results/akamai-blackwell-multiseed/comparison.json`.
- [ ] No old v0.1.0 single-seed numbers remain in the blog draft
      (1.71x speedup, 300-iteration LiH cap, -7.579105 Ha,
      +0.283 Ha residual, $3.84 cost, 1 h 17 min VM lifetime,
      stored CASCI value -7.862500).
- [ ] Cost language distinguishes bench compute time (~2 h 27 min) from
      total billed VM lifetime (~3 h 35 min) and notes the Jakarta
      regional uplift ($3.00/hr vs the $2.50/hr base SKU rate).
- [ ] Reference values quoted are the PySCF-recomputed ones from
      `app/quantum/reference_data.py` (LiH FCI -7.882391 Ha,
      CASCI(2e,5o) -7.882164 Ha), not the legacy literature estimate.
- [ ] The "not a quantum advantage claim" sentence is in the post.
- [ ] The "not a positioning of Akamai as a dedicated quantum cloud"
      sentence is in the post.
- [ ] The repo is public and the README quick-start works on a clean machine.
- [ ] The `infra/` directory contains nothing internal/unsupported about
      Akamai.
- [ ] No NVIDIA, Akamai, or quantum-vendor logos used without proper
      attribution / permission.

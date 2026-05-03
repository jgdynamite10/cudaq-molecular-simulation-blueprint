# Scope and non-goals

## Non-goals for v1

1. Multi-GPU orchestration.
2. Multi-node distributed simulation.
3. LKE deployment as the primary path.
4. Akamai Functions / EdgeWorkers in the core execution path.
5. Full web dashboard or commercial-style frontend.
6. Cross-provider comparison benchmarks.

## Engineering style

1. Production-style Python with type hints.
2. Clear module boundaries.
3. CLI-first, API-second.
4. Containerized runtime.
5. Minimal but useful documentation.
6. No internal Akamai content, no non-public data, no unsupported claims.

## Recommended implementation shape

1. Start with a single Akamai GPU VM rather than Kubernetes.
2. Use Docker as the primary runtime model.
3. Keep the core workload portable and isolate Akamai-specific deployment
   logic under `infra/`.
4. Support `qpp-cpu` for local/public reproducibility and `nvidia` for GPU
   acceleration.
5. Build a minimal technical demonstration UI only; enough to run H2/LiH
   experiments, choose backend, and inspect results and charts.

## Scope guardrails

1. Do not build a full web product.
2. Do not add Kubernetes as the primary deployment target in v1.
3. Do not add Akamai EdgeWorkers/Functions to the simulation path.
4. Do not create unsupported claims about Akamai, NVIDIA, or quantum
   advantage.
5. Do not over-engineer for scale before scientific correctness and
   reproducibility are working.
6. Keep the codebase readable and public-repo ready.
7. Prefer documentation and reproducibility over flashy UX.
8. Use vendor-neutral core abstractions and isolate Akamai-specific deployment
   logic under `infra/`.
9. Keep the UI minimal and technical; it exists to run experiments, inspect
   results, and generate blog-ready screenshots.

#!/usr/bin/env bash
# Run a minimal GPU + CUDA-Q smoke test inside the running container.

set -euo pipefail

container_name="${CONTAINER:-cudaq-blueprint}"

if ! docker ps --format '{{.Names}}' | grep -qx "${container_name}"; then
    echo "container ${container_name} is not running" >&2
    exit 1
fi

echo "==> nvidia-smi"
docker exec "${container_name}" nvidia-smi || true

echo
echo "==> CUDA-Q version"
docker exec "${container_name}" python -c "import cudaq; print(cudaq.__version__)"

echo
echo "==> nvidia target smoke test"
docker exec "${container_name}" python - <<'PY'
import cudaq

cudaq.set_target("nvidia", option="fp64")

@cudaq.kernel
def ghz(n: int):
    q = cudaq.qvector(n)
    cudaq.h(q[0])
    for i in range(n - 1):
        cudaq.x.ctrl(q[i], q[i + 1])
    cudaq.mz(q)

counts = cudaq.sample(ghz, 12)
print("GHZ counts:", dict(counts.items()))
PY

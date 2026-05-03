#!/usr/bin/env bash
# Run the H2 VQE experiment on the nvidia-fp64 backend (requires --gpus all host).
set -euo pipefail
docker compose -f containers/docker-compose.yml --profile gpu run --rm app-gpu cli run h2 --backend gpu_fp64 "$@"

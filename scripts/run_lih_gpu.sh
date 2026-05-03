#!/usr/bin/env bash
# Run the LiH VQE experiment on the nvidia-fp64 backend.
set -euo pipefail
docker compose -f containers/docker-compose.yml --profile gpu run --rm app-gpu cli run lih --backend gpu_fp64 "$@"

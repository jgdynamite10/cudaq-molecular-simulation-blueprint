#!/usr/bin/env bash
# Run the H2 VQE experiment on the qpp-cpu backend (in the local container).
set -euo pipefail
docker compose -f containers/docker-compose.yml run --rm app cli run h2 --backend cpu "$@"

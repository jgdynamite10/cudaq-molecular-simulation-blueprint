#!/usr/bin/env bash
# Container entrypoint for cudaq-molecular-simulation-blueprint.
#
# MODE selectors (passed as `docker run ... <mode>`):
#
#   api           Start the FastAPI app + UI on $CUDAQ_BP_API_PORT (default).
#   cli ...       Run the cudaq-bp CLI with the remaining args.
#   bench ...     Run the benchmark suite via the CLI.
#   shell|bash    Drop into bash for debugging.
#   verify-gpu    Print nvidia-smi + a quick CUDA-Q smoke test.
#
# Any unknown mode is passed through to the python interpreter.

set -euo pipefail

mode="${1:-api}"
shift || true

case "$mode" in
    api)
        exec uvicorn app.api.main:app \
            --host "${CUDAQ_BP_API_HOST:-0.0.0.0}" \
            --port "${CUDAQ_BP_API_PORT:-8000}" \
            "$@"
        ;;
    cli)
        exec cudaq-bp "$@"
        ;;
    bench)
        exec cudaq-bp bench compare "$@"
        ;;
    shell|bash)
        exec /bin/bash -l "$@"
        ;;
    verify-gpu)
        echo "--- nvidia-smi ---"
        nvidia-smi || echo "(nvidia-smi unavailable; container is running CPU-only)"
        echo
        echo "--- python -c 'import cudaq' ---"
        python -c "import cudaq, sys; print('cudaq', cudaq.__version__); cudaq.set_target('qpp-cpu'); print('qpp-cpu OK')"
        ;;
    *)
        exec python "$mode" "$@"
        ;;
esac

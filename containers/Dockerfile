# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Multi-stage Dockerfile for cudaq-molecular-simulation-blueprint.
#
# Base image: nvidia/cuda 12.6 runtime + cuDNN on Ubuntu 22.04. This is the
# standard supported environment for CUDA-Q wheels (cuda-quantum-cu12).
#
# - The image runs in CPU-only mode by default (no GPU access required).
# - When started with `--gpus all` (Compose `gpu` profile, or
#   nvidia-container-toolkit on the host), the same image targets cuStateVec
#   and uses the GPU for statevector simulation.
# -----------------------------------------------------------------------------

ARG BASE_IMAGE=nvidia/cuda:12.6.3-cudnn-runtime-ubuntu22.04
ARG PYTHON_VERSION=3.11

# --- Builder stage: build a virtualenv with all dependencies ----------------
FROM ${BASE_IMAGE} AS builder

ARG PYTHON_VERSION
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip \
        build-essential \
        gcc-11 \
        g++-11 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 110 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 110

WORKDIR /app

# Create virtualenv and install our project + cudaq.
RUN python${PYTHON_VERSION} -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY pyproject.toml README.md LICENSE ./
COPY app ./app

# CUDA-Q wheel compatible with CUDA 12.x; pulls cuda-quantum-cu12 transitively.
RUN pip install --upgrade pip \
    && pip install ".[chemistry]" || pip install . \
    && pip install --no-deps cuda-quantum-cu12==0.14.0 || true

# --- Runtime stage ---------------------------------------------------------
FROM ${BASE_IMAGE} AS runtime

ARG PYTHON_VERSION
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    CUDAQ_BP_LOG_LEVEL=INFO \
    CUDAQ_BP_RESULTS_DIR=/data/results \
    CUDAQ_BP_API_HOST=0.0.0.0 \
    CUDAQ_BP_API_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        ca-certificates \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin --user-group cudaq

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=cudaq:cudaq pyproject.toml README.md LICENSE ./
COPY --chown=cudaq:cudaq app ./app
COPY --chown=cudaq:cudaq containers/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && mkdir -p /data/results && chown -R cudaq:cudaq /data

USER cudaq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=20s \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["api"]

.DEFAULT_GOAL := help

PYTHON ?= python3
UV ?= uv
DOCKER ?= docker
COMPOSE ?= docker compose
COMPOSE_FILE := containers/docker-compose.yml

IMAGE_NAME ?= cudaq-molecular-simulation-blueprint
IMAGE_TAG ?= dev

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^[a-zA-Z0-9_.-]+:.*##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

.PHONY: setup
setup:  ## Create .venv, install dev deps via uv (preferred) or pip
	@if command -v $(UV) >/dev/null 2>&1; then \
		$(UV) sync --extra dev; \
	else \
		echo "uv not found, falling back to venv + pip"; \
		$(PYTHON) -m venv .venv; \
		. .venv/bin/activate && pip install -U pip && pip install -e ".[dev]"; \
	fi

.PHONY: lock
lock:  ## Refresh uv.lock
	$(UV) lock

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

.PHONY: lint
lint:  ## ruff check
	$(UV) run ruff check app

.PHONY: format
format:  ## ruff format
	$(UV) run ruff format app
	$(UV) run ruff check --fix app

.PHONY: typecheck
typecheck:  ## mypy
	$(UV) run mypy app

.PHONY: test
test:  ## pytest (CPU-only)
	$(UV) run pytest -m "not gpu"

.PHONY: test-gpu
test-gpu:  ## pytest including GPU tests (requires NVIDIA GPU)
	$(UV) run pytest

.PHONY: cov
cov:  ## pytest with coverage
	$(UV) run pytest -m "not gpu" --cov=app --cov-report=term-missing --cov-report=xml

.PHONY: ci
ci: lint typecheck test  ## All quality gates

# ---------------------------------------------------------------------------
# Run experiments locally
# ---------------------------------------------------------------------------

.PHONY: run-cpu-h2
run-cpu-h2:  ## Run H2 VQE on the qpp-cpu backend
	$(UV) run cudaq-bp run h2 --backend cpu

.PHONY: run-cpu-lih
run-cpu-lih:  ## Run LiH VQE on the qpp-cpu backend (slow)
	$(UV) run cudaq-bp run lih --backend cpu

.PHONY: run-gpu-h2
run-gpu-h2:  ## Run H2 VQE on the nvidia backend (requires Linux+GPU)
	$(UV) run cudaq-bp run h2 --backend gpu_fp64

.PHONY: run-gpu-lih
run-gpu-lih:  ## Run LiH VQE on the nvidia backend
	$(UV) run cudaq-bp run lih --backend gpu_fp64

.PHONY: bench
bench:  ## Generate the CPU vs GPU comparison report from results/
	$(UV) run cudaq-bp bench compare

# ---------------------------------------------------------------------------
# UI / API
# ---------------------------------------------------------------------------

.PHONY: serve
serve:  ## Run the FastAPI app + UI locally on :8000
	$(UV) run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

.PHONY: container-build
container-build:  ## Build the Docker image
	$(DOCKER) build -t $(IMAGE_NAME):$(IMAGE_TAG) -f containers/Dockerfile .

.PHONY: container-run-cpu
container-run-cpu:  ## Run the container in CPU-only mode
	$(COMPOSE) -f $(COMPOSE_FILE) up app

.PHONY: container-run-gpu
container-run-gpu:  ## Run the container with NVIDIA GPU access
	$(COMPOSE) -f $(COMPOSE_FILE) --profile gpu up app-gpu

.PHONY: container-down
container-down:  ## Stop running containers
	$(COMPOSE) -f $(COMPOSE_FILE) down

# ---------------------------------------------------------------------------
# Akamai infra (does NOT run terraform apply by default)
# ---------------------------------------------------------------------------

.PHONY: akamai-init
akamai-init:  ## terraform init for Akamai
	cd infra/terraform/akamai && terraform init

.PHONY: akamai-plan
akamai-plan:  ## terraform plan for Akamai (read-only, safe)
	cd infra/terraform/akamai && terraform plan

.PHONY: akamai-apply
akamai-apply:  ## terraform apply (provisions a real GPU VM, costs money)
	cd infra/terraform/akamai && terraform apply

.PHONY: akamai-destroy
akamai-destroy:  ## terraform destroy (tears down the GPU VM)
	cd infra/terraform/akamai && terraform destroy

.PHONY: akamai-bootstrap
akamai-bootstrap:  ## After apply, install drivers + docker + app via Ansible
	bash scripts/bootstrap_host.sh

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

.PHONY: clean
clean:  ## Remove caches, build artifacts
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -prune -exec rm -rf {} +

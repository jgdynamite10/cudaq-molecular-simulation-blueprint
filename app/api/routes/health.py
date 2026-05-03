"""Health and capability discovery endpoint."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.core.metadata import project_version
from app.core.system_info import collect_system_info, has_nvidia_gpu
from app.storage.manifests import BackendIdentifier

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    info = collect_system_info()
    backends = [BackendIdentifier.CPU]
    if has_nvidia_gpu():
        backends.extend([BackendIdentifier.GPU_FP32, BackendIdentifier.GPU_FP64])
    return HealthResponse(
        project_version=project_version(),
        cudaq_version=info.cudaq_version,
        gpus=[asdict(gpu) for gpu in info.gpus],
        backends_available=backends,
    )

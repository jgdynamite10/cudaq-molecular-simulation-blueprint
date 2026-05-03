"""Capture host + software environment details for run manifests.

Every result file embeds the output of :func:`collect_system_info` so the run
can be traced back to the exact CUDA-Q version, GPU, driver, OS, and Python
interpreter that produced it.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from importlib import metadata as importlib_metadata
from typing import Any


@dataclass(slots=True)
class GpuInfo:
    name: str
    uuid: str | None
    driver_version: str | None
    cuda_version: str | None
    memory_total_mib: int | None


@dataclass(slots=True)
class SystemInfo:
    python_version: str
    platform: str
    machine: str
    processor: str
    cpu_count: int | None
    cudaq_version: str | None
    gpus: list[GpuInfo] = field(default_factory=list)
    git_sha: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_pkg_version(name: str) -> str | None:
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def _git_sha() -> str | None:
    if shutil.which("git") is None:
        return None
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _query_nvidia_smi() -> list[GpuInfo]:
    """Query nvidia-smi for GPU info. Returns [] if no GPU / no nvidia-smi."""
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return []

    query = "name,uuid,driver_version,memory.total"
    try:
        out = subprocess.run(
            [
                nvidia_smi,
                f"--query-gpu={query}",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []

    cuda_version = _query_cuda_version_via_smi()

    gpus: list[GpuInfo] = []
    for line in out.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        name, uuid, driver, mem = parts[:4]
        try:
            mem_int = int(mem)
        except ValueError:
            mem_int = None
        gpus.append(
            GpuInfo(
                name=name,
                uuid=uuid or None,
                driver_version=driver or None,
                cuda_version=cuda_version,
                memory_total_mib=mem_int,
            )
        )
    return gpus


def _query_cuda_version_via_smi() -> str | None:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return None
    try:
        out = subprocess.run(
            [nvidia_smi],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    for line in out.stdout.splitlines():
        line_stripped = line.strip()
        if "CUDA Version" in line_stripped:
            return line_stripped.split("CUDA Version:")[-1].strip().rstrip("|").strip()
    return None


def collect_system_info() -> SystemInfo:
    """Snapshot the current host and Python environment."""
    return SystemInfo(
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor() or platform.machine(),
        cpu_count=__import__("os").cpu_count(),
        cudaq_version=_safe_pkg_version("cudaq") or _safe_pkg_version("cuda-quantum"),
        gpus=_query_nvidia_smi(),
        git_sha=_git_sha(),
    )


def has_nvidia_gpu() -> bool:
    """Return True if nvidia-smi reports at least one GPU."""
    return bool(_query_nvidia_smi())

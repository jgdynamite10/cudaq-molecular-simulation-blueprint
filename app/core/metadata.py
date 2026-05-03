"""Lightweight project metadata helpers."""

from __future__ import annotations

from importlib import metadata as importlib_metadata


def project_name() -> str:
    return "cudaq-molecular-simulation-blueprint"


def project_version() -> str:
    try:
        return importlib_metadata.version(project_name())
    except importlib_metadata.PackageNotFoundError:
        return "0.1.0"

"""Shared pytest fixtures."""

from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from pathlib import Path

import pytest

CUDAQ_AVAILABLE = importlib.util.find_spec("cudaq") is not None


def _has_cudaq() -> bool:
    return CUDAQ_AVAILABLE


@pytest.fixture(autouse=True)
def _isolated_results_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Redirect ``results/`` to a temp dir for the duration of each test."""
    monkeypatch.setenv("CUDAQ_BP_RESULTS_DIR", str(tmp_path))
    from app.core import config as config_module

    config_module._settings = None  # type: ignore[attr-defined]
    yield tmp_path
    config_module._settings = None  # type: ignore[attr-defined]


def requires_cudaq(func):  # type: ignore[no-untyped-def]
    """Decorator: skip the test when CUDA-Q is not importable."""
    return pytest.mark.skipif(
        not _has_cudaq(),
        reason="CUDA-Q is not installed in this environment",
    )(func)

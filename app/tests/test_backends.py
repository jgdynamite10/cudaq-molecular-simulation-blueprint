"""Backend identifier mapping tests (no CUDA-Q required)."""

from __future__ import annotations

import pytest

from app.quantum.backends import BACKEND_CONFIGS, get_backend_config
from app.storage.manifests import BackendIdentifier


@pytest.mark.parametrize(
    ("identifier", "expected_target", "expected_option"),
    [
        (BackendIdentifier.CPU, "qpp-cpu", None),
        (BackendIdentifier.GPU_FP32, "nvidia", "fp32"),
        (BackendIdentifier.GPU_FP64, "nvidia", "fp64"),
    ],
)
def test_backend_config_maps_to_correct_target(
    identifier: BackendIdentifier, expected_target: str, expected_option: str | None
) -> None:
    config = get_backend_config(identifier)
    assert config.target == expected_target
    assert config.target_option == expected_option


def test_target_string_round_trip() -> None:
    cpu = get_backend_config(BackendIdentifier.CPU)
    gpu64 = get_backend_config(BackendIdentifier.GPU_FP64)
    assert cpu.target_string() == "qpp-cpu"
    assert gpu64.target_string() == "nvidia:fp64"


def test_all_identifiers_have_a_config() -> None:
    for ident in BackendIdentifier:
        assert ident in BACKEND_CONFIGS, f"missing config for {ident}"

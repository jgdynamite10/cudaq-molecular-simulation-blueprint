"""Regression tests for the openfermion DATA_DIRECTORY workaround.

CUDA-Q's chemistry pipeline ultimately calls openfermion's MolecularData
save() which writes an HDF5 cache to a package-relative path. In our
container that path is root-owned while the runtime user is non-root,
so the call raises PermissionError. We monkey-patch DATA_DIRECTORY to a
writable scratch dir at import time. These tests verify the helper
behaves correctly.
"""

from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("openfermion.chem.molecular_data")

from app.quantum import chemistry


def _reset_module_state() -> None:
    import openfermion.chem.molecular_data as ofmd

    if hasattr(ofmd, chemistry._OPENFERMION_PATCH_FLAG):
        delattr(ofmd, chemistry._OPENFERMION_PATCH_FLAG)


def test_returns_writable_directory(tmp_path, monkeypatch):
    """When the package directory is unwritable, the helper redirects to /tmp."""
    _reset_module_state()
    import openfermion.chem.molecular_data as ofmd

    fake_unwritable = tmp_path / "ro"
    fake_unwritable.mkdir(mode=0o500)
    monkeypatch.setattr(ofmd, "DATA_DIRECTORY", str(fake_unwritable))

    result = chemistry.ensure_openfermion_data_dir_writable()

    assert result is not None
    assert os.access(result, os.W_OK), f"{result} is not writable"
    assert result == ofmd.DATA_DIRECTORY
    assert str(fake_unwritable) != ofmd.DATA_DIRECTORY


def test_leaves_writable_directory_alone(tmp_path, monkeypatch):
    """When DATA_DIRECTORY is already writable the helper is a no-op."""
    _reset_module_state()
    import openfermion.chem.molecular_data as ofmd

    fake_writable = tmp_path / "rw"
    fake_writable.mkdir()
    monkeypatch.setattr(ofmd, "DATA_DIRECTORY", str(fake_writable))

    result = chemistry.ensure_openfermion_data_dir_writable()

    assert result == str(fake_writable)
    assert str(fake_writable) == ofmd.DATA_DIRECTORY


def test_is_idempotent(tmp_path, monkeypatch):
    """Calling twice does not re-patch."""
    _reset_module_state()
    import openfermion.chem.molecular_data as ofmd

    fake_unwritable = tmp_path / "ro"
    fake_unwritable.mkdir(mode=0o500)
    monkeypatch.setattr(ofmd, "DATA_DIRECTORY", str(fake_unwritable))

    first = chemistry.ensure_openfermion_data_dir_writable()
    second = chemistry.ensure_openfermion_data_dir_writable()

    assert first == second
    assert getattr(ofmd, chemistry._OPENFERMION_PATCH_FLAG, False) is True


def test_scratch_dir_lives_under_tmpdir(tmp_path, monkeypatch):
    """The scratch directory is created under tempfile.gettempdir()."""
    _reset_module_state()
    import openfermion.chem.molecular_data as ofmd

    fake_unwritable = tmp_path / "ro"
    fake_unwritable.mkdir(mode=0o500)
    monkeypatch.setattr(ofmd, "DATA_DIRECTORY", str(fake_unwritable))

    result = chemistry.ensure_openfermion_data_dir_writable()

    assert result is not None
    assert result.startswith(tempfile.gettempdir())

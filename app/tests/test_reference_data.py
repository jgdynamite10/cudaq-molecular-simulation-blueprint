"""Reference energy lookup tests."""

from __future__ import annotations

from app.quantum.reference_data import (
    CHEMICAL_ACCURACY_HARTREE,
    REFERENCES,
    lookup_reference,
)


def test_chemical_accuracy_threshold_is_standard() -> None:
    assert CHEMICAL_ACCURACY_HARTREE == 1.6e-3


def test_h2_reference_present() -> None:
    ref = lookup_reference("h2", "sto-3g", 0.7414, None)
    assert ref is not None
    assert -1.14 < ref.energy_hartree < -1.13


def test_lih_full_reference_present() -> None:
    ref = lookup_reference("lih", "sto-3g", 1.5957, None)
    assert ref is not None
    assert -7.89 < ref.energy_hartree < -7.87


def test_lih_active_space_reference_present() -> None:
    ref = lookup_reference("lih", "sto-3g", 1.5957, (2, 5))
    assert ref is not None
    assert ref.method.startswith("CASCI(2e,5o)")
    assert -7.89 < ref.energy_hartree < -7.87


def test_lih_active_space_value_close_to_full_fci() -> None:
    """The (2e,5o) active space captures essentially all FCI correlation.

    Recomputed via PySCF on 2026-05-04: CASCI(2e,5o) = -7.882164 Ha,
    full FCI = -7.882391 Ha, gap = 0.227 mHa. This regression test pins
    that the stored values reflect the actual chemistry rather than a
    legacy literature estimate.
    """
    cas = lookup_reference("lih", "sto-3g", 1.5957, (2, 5))
    full = lookup_reference("lih", "sto-3g", 1.5957, None)
    assert cas is not None
    assert full is not None
    gap_mha = abs(cas.energy_hartree - full.energy_hartree) * 1000
    assert gap_mha < 1.0, (
        f"CASCI(2e,5o) - FCI gap is {gap_mha:.3f} mHa; "
        "if this exceeds 1 mHa, the stored value has drifted from PySCF"
    )


def test_unknown_geometry_returns_none() -> None:
    assert lookup_reference("h2", "sto-3g", 99.0, None) is None
    assert lookup_reference("co2", "sto-3g", 1.16, None) is None


def test_geometry_tolerance_within_001_angstrom() -> None:
    ref = lookup_reference("h2", "sto-3g", 0.7415, None)
    assert ref is not None


def test_references_dict_is_nonempty() -> None:
    assert len(REFERENCES) >= 4

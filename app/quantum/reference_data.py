"""Reference energies for validating VQE convergence.

These are computed/published numbers used to compute "error vs reference"
in run manifests. Quoted to 6 decimal places (Hartree). All values were
recomputed with PySCF on 2026-05-04 (RHF + CASCI on the equilibrium
geometry) so the stored references match what a reader can reproduce
locally with ``pyscf`` at any time.

Sources:

- H2 / STO-3G FCI at the experimental bond length R = 0.7414 Å:
  -1.137270 Ha. Reproducible by any FCI program; appears throughout the
  quantum chemistry literature.
- LiH / STO-3G full FCI at R = 1.5957 Å (equilibrium): -7.882391 Ha,
  computed via ``pyscf.mcscf.CASCI(mf, mol.nao, mol.nelectron)``.
- LiH / STO-3G with a (2 electron, 5 orbital) active space at R = 1.5957 Å:
  -7.882164 Ha, computed via ``pyscf.mcscf.CASCI(mf, 5, 2)``.

Note on the LiH (2e, 5o) value: an earlier "literature estimate" of
-7.862500 Ha that shipped in the v0.1.0 of this file was effectively the
HF energy and was approximately 19.7 mHa above the true CASCI(2e, 5o)
minimum. The recomputed PySCF value above is correct and is what
post-v0.1.1 manifests are scored against. The recomputed value also
shows that the (2e, 5o) active space captures essentially all of the
full-FCI correlation: the gap between the active-space CASCI and full
FCI is only 0.227 mHa for LiH/STO-3G at this geometry, so there is no
material "frozen-core" residual in the (2e, 5o) calculation; any
remaining error vs CASCI(2e, 5o) is optimizer / ansatz residual rather
than an active-space limitation.

CHEMICAL_ACCURACY_HARTREE is the standard 1.6 mHa threshold used to
decide whether a VQE run "reached chemical accuracy".
"""

from __future__ import annotations

from dataclasses import dataclass

CHEMICAL_ACCURACY_HARTREE: float = 1.6e-3


@dataclass(frozen=True, slots=True)
class ReferenceEnergy:
    """A published reference energy for a specific molecule + geometry + method."""

    molecule: str
    basis: str
    bond_distance_angstrom: float
    method: str
    energy_hartree: float
    note: str = ""


# Keys are tuples of (molecule, basis, bond_distance, active_space_or_None)
# active_space is encoded as (n_electrons, n_orbitals) or None for full
REFERENCES: dict[tuple[str, str, float, tuple[int, int] | None], ReferenceEnergy] = {
    ("h2", "sto-3g", 0.7414, None): ReferenceEnergy(
        molecule="h2",
        basis="sto-3g",
        bond_distance_angstrom=0.7414,
        method="FCI",
        energy_hartree=-1.137270,
        note="Standard reference at experimental H2 bond length.",
    ),
    ("h2", "sto-3g", 0.7474, None): ReferenceEnergy(
        molecule="h2",
        basis="sto-3g",
        bond_distance_angstrom=0.7474,
        method="FCI",
        energy_hartree=-1.137275,
        note="Common alternative bond length used in CUDA-Q docs.",
    ),
    ("lih", "sto-3g", 1.5957, None): ReferenceEnergy(
        molecule="lih",
        basis="sto-3g",
        bond_distance_angstrom=1.5957,
        method="FCI (pyscf 2026-05-04)",
        energy_hartree=-7.882391,
        note="Full FCI at equilibrium geometry, computed via pyscf CASCI on all orbitals.",
    ),
    ("lih", "sto-3g", 1.5957, (2, 5)): ReferenceEnergy(
        molecule="lih",
        basis="sto-3g",
        bond_distance_angstrom=1.5957,
        method="CASCI(2e,5o) (pyscf 2026-05-04)",
        energy_hartree=-7.882164,
        note=(
            "(2 active electrons, 5 active orbitals); freeze 1s of Li. "
            "Computed via pyscf.mcscf.CASCI(mf, 5, 2) on the RHF reference. "
            "Gap to full FCI at this geometry is only 0.227 mHa, so the "
            "active space captures essentially all of the FCI correlation."
        ),
    ),
}


def lookup_reference(
    molecule: str,
    basis: str,
    bond_distance: float,
    active_space: tuple[int, int] | None = None,
) -> ReferenceEnergy | None:
    """Return the published reference energy for the closest matching geometry.

    The bond distance is matched within 0.01 Å to handle minor user
    perturbations without forcing exact equality.
    """
    for (m, b, r, a), ref in REFERENCES.items():
        if m == molecule and b == basis and a == active_space and abs(r - bond_distance) < 0.01:
            return ref
    return None

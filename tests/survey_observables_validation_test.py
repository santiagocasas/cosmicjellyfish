"""Unit tests for the historical survey-observable reference formulas.

These tests are cosmology-free: they exercise the reference implementations in
``scripts/validation/survey_observable_reference.py`` against analytic identities. The
full old-vs-new comparison for DESI, Rubin and SKAO is run by
``scripts/validation/validate_survey_observables.py`` and recorded in
``docs/SURVEY_VALIDATION_ROADMAP.md``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = REPO_ROOT / "scripts" / "validation" / "survey_observable_reference.py"


def _load_reference():
    sys.path.insert(0, str(REFERENCE_PATH.parent))
    spec = importlib.util.spec_from_file_location("survey_observable_reference", REFERENCE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference = _load_reference()


class _DummyCosmo:
    """Minimal cosmology stub with the methods the reference formulas use."""

    def __init__(self, h=0.67):
        self.cosmopars = {"h": h}

    @staticmethod
    def angdist(z):
        return 3000.0 * z / (1.0 + z)

    @staticmethod
    def comoving(z):
        return 3000.0 * z

    @staticmethod
    def Hubble(z):
        return 70.0

    @staticmethod
    def sigma8_of_z(z):
        return 0.8

    @staticmethod
    def f_growthrate(z, k=None):
        return np.full_like(np.asarray(k, dtype=float), 0.5) if k is not None else 0.5

    @staticmethod
    def matpow(z, k):
        return np.asarray(k, dtype=float) + 1.0

    @staticmethod
    def nonwiggle_pow(z, k):
        return np.asarray(k, dtype=float) + 1.0


def _table():
    return {
        "area": 100.0,
        "zmin": np.array([0.0, 0.5]),
        "zmax": np.array([0.5, 1.0]),
        "dndz": np.array([1000.0, 500.0]),
        "bias": np.array([1.0, 2.0]),
    }


def test_spectro_table_parsing_requires_historical_checkout():
    """Parsing a historical table needs the read-only checkout; skip when absent."""
    try:
        reference.historical_project_dir()
    except FileNotFoundError:
        pytest.skip("historical survey checkout not available")
    table = reference.load_spectro_table("DESI_BGS_GCsp.dat")
    assert table["area"] == pytest.approx(14000.0)
    assert len(table["dndz"]) == len(table["bias"]) == 5


def test_dn3_maps_to_mass_density_and_volume():
    """dn3 (per deg^2) times dz over the per-deg^2 volume gives Mpc^-3."""
    cosmo = _DummyCosmo()
    table = _table()
    density = reference.reference_n_density(table, cosmo)
    volume = reference.reference_volume_survey(table, cosmo)
    dz = table["zmax"] - table["zmin"]
    recovered = density * volume / table["area"]
    assert np.allclose(recovered, table["dndz"] * dz)


def test_im_analytic_limits():
    assert reference.reference_omega_hi(0.0) == pytest.approx(4.0e-4)
    assert reference.reference_b_hi(0.0) == pytest.approx(0.9)
    assert reference.reference_theta_b(0.0, 15.0) == pytest.approx(1.22 * 0.21 / 15.0)


def test_pgg_reduces_to_kaiser_matter_power_without_rsd_smearing():
    """With FoG and de-wiggling off and no AP distortion the paper form is plain Kaiser."""
    cosmo = _DummyCosmo()
    k = np.array([0.01, 0.05, 0.1])
    mu = 0.5
    bias = 1.5
    pgg = reference.reference_pgg(
        z=1.0,
        k=k,
        mu=mu,
        cosmo=cosmo,
        fiducial_cosmo=cosmo,
        bias=bias,
        sigma_p=0.0,
        sigma_v=0.0,
        dz_err=0.0,
        sigma8_norm=False,
    )
    f = cosmo.f_growthrate(1.0, k)
    expected = (bias + f * mu**2) ** 2 * cosmo.matpow(1.0, k)
    assert np.allclose(pgg, expected)


def test_pgg_sigma8_normalisation_cancels():
    """The (b sigma8, f sigma8) form with P/sigma8^2 equals the plain Kaiser form."""
    cosmo = _DummyCosmo()
    k = np.array([0.02, 0.08])
    kwargs = dict(
        z=0.7,
        k=k,
        mu=0.3,
        cosmo=cosmo,
        fiducial_cosmo=cosmo,
        bias=1.2,
        sigma_p=0.0,
        sigma_v=0.0,
        dz_err=0.0,
    )
    plain = reference.reference_pgg(**kwargs, sigma8_norm=False)
    normalised = reference.reference_pgg(**kwargs, sigma8_norm=True)
    assert np.allclose(plain, normalised)


def test_noise_power_is_positive_and_scales_with_time():
    cosmo = _DummyCosmo()
    k = np.array([0.01, 0.05])
    mu = np.array([0.0, 0.5])
    base = reference.reference_p_noise_21(
        1.0,
        k,
        mu,
        cosmo=cosmo,
        tsys=100.0,
        fsky=0.5,
        t_tot=1000.0,
        n_dish=10,
        dish_diameter=15.0,
    )
    longer = reference.reference_p_noise_21(
        1.0,
        k,
        mu,
        cosmo=cosmo,
        tsys=100.0,
        fsky=0.5,
        t_tot=2000.0,
        n_dish=10,
        dish_diameter=15.0,
    )
    assert np.all(base > 0)
    assert np.allclose(longer, base / 2.0)


def test_fig1_reference_table_layout():
    """The historical Fig. 1 table has the documented nine columns and k range."""
    try:
        path = reference.historical_project_dir() / "data-for-fig1.dat"
    except FileNotFoundError:
        pytest.skip("historical survey checkout is not available")
    if not path.exists():
        pytest.skip("data-for-fig1.dat is not available")

    table = np.loadtxt(path)
    assert table.shape[1] == 9
    assert np.all(np.diff(table[:, 0]) > 0)
    assert table[0, 0] == pytest.approx(1.0e-4)
    assert table[-1, 0] == pytest.approx(10.0)
    assert np.all(table[:, 1:7] >= 0)
    assert np.all(table[:, 7] > 0)  # constant brightness temperature
    assert np.all(table[:, 8] > 0)  # thermal noise power

"""Coverage tests for the Hu-Sawicki f(R) boosts (no frahi_class, EE2 or e-MANTIS needed).

``MGfit_Winther`` is tested as a black box (it is a verbatim copy of Sefa76/photometric_fofR),
``modified_gravity.fr_boost_nonlinear`` against light fakes of the CLASS runs.
"""

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from cosmicjellyfish.cosmology import cosmology, modified_gravity
from cosmicjellyfish.cosmology.f_r_emulators.MGfit_Winther import (
    kazuya_correktion,
    pofk_enhancement,
    pofk_enhancement_linear,
)

K_H = np.array([0.05, 0.5, 2.0, 8.0])  # k [h/Mpc]

# ---------------------------------------------------------------------------
# MGfit_Winther: nonlinear fitting formula
# ---------------------------------------------------------------------------


def test_pofk_enhancement_regression_values():
    np.testing.assert_allclose(
        pofk_enhancement(0.5, 2e-6, K_H, hasBug=False),
        [1.00263682, 1.02296849, 1.04677497, 1.0739988],
        rtol=1e-6,
    )


def test_pofk_enhancement_has_bug_flag_changes_the_c1_parameter():
    fixed = pofk_enhancement(0.5, 1e-5, K_H, hasBug=False)
    buggy = pofk_enhancement(0.5, 1e-5, K_H, hasBug=True)
    assert np.max(np.abs(fixed - buggy)) > 1e-3
    assert np.all(np.isfinite(buggy))


@pytest.mark.parametrize("fR0", [2e-6, 7e-6, 2e-5, 8e-5])
def test_pofk_enhancement_covers_every_fR0_branch(fR0):
    # low (<5e-6), low-mid blend, mid-high blend, high (>5e-5)
    ratio = pofk_enhancement(0.5, fR0, K_H, hasBug=False)
    assert ratio.shape == K_H.shape
    assert np.all(np.isfinite(ratio))
    assert np.all(ratio >= 1.0)


def test_pofk_enhancement_grows_with_fR0_at_fixed_k_and_z():
    fR0 = np.geomspace(1e-7, 1e-4, 25)
    ratio = np.array([pofk_enhancement(0.5, f, 2.0, hasBug=False) for f in fR0])
    assert np.all(np.diff(ratio) >= -1e-12)


def test_pofk_enhancement_returns_closest_value_outside_fitted_range():
    # fR0 clamped to [1e-7, 1e-4] and k to kmax = 10 h/Mpc. The z clamp is not tested here: the
    # scale factor is computed before z is clamped (see the upstream-fix tests).
    np.testing.assert_array_equal(
        pofk_enhancement(0.5, 1e-9, K_H, hasBug=False),
        pofk_enhancement(0.5, 1e-7, K_H, hasBug=False),
    )
    np.testing.assert_array_equal(
        pofk_enhancement(0.5, 1e-2, K_H, hasBug=False),
        pofk_enhancement(0.5, 1e-4, K_H, hasBug=False),
    )
    np.testing.assert_array_equal(
        pofk_enhancement(0.5, 1e-5, 50.0, hasBug=False),
        pofk_enhancement(0.5, 1e-5, 10.0, hasBug=False),
    )


# ---------------------------------------------------------------------------
# MGfit_Winther: linear fitting formula and sigma8 correction
# ---------------------------------------------------------------------------


def test_pofk_enhancement_linear_regression_values():
    assert pofk_enhancement_linear(0, 1e-5, 0.1) == pytest.approx(1.0775032421, rel=1e-8)
    assert pofk_enhancement_linear(0, 1e-5, 1.0) == pytest.approx(1.4202120104, rel=1e-8)


def test_pofk_enhancement_linear_is_one_for_vanishing_k():
    assert pofk_enhancement_linear(0, 1e-5, 1e-12) == 1.0


def test_pofk_enhancement_linear_avoids_nan_at_effective_k_equal_one():
    # for fR0 = fR0_fid = 1e-5 the effective k equals the input k, and k = 1 is a 0/0 in the formula
    at_one = pofk_enhancement_linear(0, 1e-5, 1.0)
    assert np.isfinite(at_one)
    assert at_one == pytest.approx(pofk_enhancement_linear(0, 1e-5, 1.0001), rel=1e-3)


def test_pofk_enhancement_linear_returns_closest_value_outside_fitted_range():
    assert pofk_enhancement_linear(0, 1e-9, 0.1) == pofk_enhancement_linear(0, 1e-7, 0.1)
    assert pofk_enhancement_linear(0, 1e-2, 0.1) == pofk_enhancement_linear(0, 1e-3, 0.1)
    assert pofk_enhancement_linear(7, 1e-5, 0.1) == pofk_enhancement_linear(5, 1e-5, 0.1)
    assert pofk_enhancement_linear(-0.5, 1e-5, 0.1) == pofk_enhancement_linear(0, 1e-5, 0.1)
    assert pofk_enhancement_linear(0, 1e-5, 1e4) == pofk_enhancement_linear(0, 1e-5, 100.0)


def test_kazuya_correktion_value():
    assert kazuya_correktion(5.301) == pytest.approx(0.99282860, rel=1e-6)


# ---------------------------------------------------------------------------
# modified_gravity: e-MANTIS loader, boost settings
# ---------------------------------------------------------------------------


def test_emantis_loader_builds_cached_emulator_with_likelihood_options(monkeypatch):
    calls = []

    class FakeFofrBoost:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setitem(sys.modules, "emantis", SimpleNamespace(FofrBoost=FakeFofrBoost))
    modified_gravity._emantis.cache_clear()
    try:
        first = modified_gravity._emantis()
        assert modified_gravity._emantis() is first
        assert calls == [{"verbose": False, "extrapolate_aexp": False, "extrapolate_low_k": True}]
    finally:
        modified_gravity._emantis.cache_clear()


def test_fofR_boost_grid_settings_override_changes_the_boost_mask():
    h, lgfR0 = 0.67, 5.301
    k = np.array([0.01, 1.0, 10.0, 20.0, 40.0]) * h
    default = modified_gravity.fofR_boost_grid("winther2019", k, [0.5], lgfR0, h)
    narrow = modified_gravity.fofR_boost_grid(
        "winther2019", k, [0.5], lgfR0, h, settings={"k_max_h_by_Mpc": 15.0}
    )
    assert default[3, 0] > 1.0 and default[4, 0] > 1.0
    np.testing.assert_array_equal(narrow[3:, 0], 1.0)
    np.testing.assert_array_equal(narrow[:3], default[:3])


def test_fofR_helpers_accept_an_integer_lgfR0():
    h = 0.67
    k = np.array([0.1, 1.0]) * h
    np.testing.assert_allclose(
        modified_gravity.fofR_boost_grid("winther2019", k, [0.5], 6, h),
        modified_gravity.fofR_boost_grid("winther2019", k, [0.5], 6.0, h),
    )
    k_lin = np.geomspace(1e-3, 1.0, 50)
    pk_lin = k_lin / (1 + (k_lin / 0.02) ** 3)
    assert modified_gravity.sigma8_fofR(k_lin, pk_lin, h, 6) == pytest.approx(
        modified_gravity.sigma8_fofR(k_lin, pk_lin, h, 6.0)
    )


# ---------------------------------------------------------------------------
# modified_gravity.fr_boost_nonlinear against fakes of the CLASS runs
# ---------------------------------------------------------------------------

K_GRID = np.array([0.01, 0.1, 1.0])
Z_GRID = np.array([0.0, 1.0])
PK_GRID = np.arange(1.0, 7.0).reshape(3, 2)
BOOST = 1.0 + 0.1 * np.arange(6.0).reshape(3, 2)


class _FakeFrRun:
    def get_current_derived_parameters(self, names):
        assert names == ["A_s"]
        return {"A_s": 2.1e-9}


class _FakeLcdm:
    instances = []
    omega_m = 0.31  # = Omega0_cdm + Omega_b: no neutrinos

    def __init__(self):
        self.params = None
        self.computed = False
        self.cleaned = False
        self.emptied = False
        self.Omega_nu = 0.0
        _FakeLcdm.instances.append(self)

    def set(self, params):
        self.params = dict(params)

    def compute(self):
        self.computed = True

    def h(self):
        return 0.67

    def Omega0_cdm(self):
        return 0.26

    def Omega_b(self):
        return 0.05

    def Omega_m(self):
        return self.omega_m

    def sigma8(self):
        return 0.8

    def get_pk_and_k_and_z(self, nonlinear):
        assert nonlinear is False
        k = np.geomspace(1e-3, 5.0, 5)
        return np.outer(k, [1.0, 2.0]), k, np.array([1.0, 0.0])

    def struct_cleanup(self):
        self.cleaned = True

    def empty(self):
        self.emptied = True


def _fake_bc(
    nonlinear_conf=None,
    cb_prescription="neutrino_subtraction",
    with_lcdm_section=True,
    smg_in_yaml=False,
    husawicki_overrides=None,
    lcdm_overrides=None,
):
    """Fake boltzmann_code. With ``smg_in_yaml``, ``parameters_smg`` is fixed in the HuSawicki
    YAML section instead of coming from ``log10fR0`` in the cosmological parameters. The
    ``*_overrides`` arguments add inputs to the corresponding YAML section."""
    classpars = {
        "ACCURACY": {"accuracy_key": 1},
        "COSMO_SETTINGS": {"setting_key": 2},
        "HuSawicki": {"gravity_model": "hu_sawicki", **(husawicki_overrides or {})},
    }
    if with_lcdm_section:
        classpars["LCDM"] = {"lcdm_only_key": 3, **(lcdm_overrides or {})}
    if nonlinear_conf is not None:
        classpars["NONLINEAR"] = nonlinear_conf
    if smg_in_yaml:
        classpars["HuSawicki"]["parameters_smg"] = "-5.301, 0.0"

    def changebasis_class(cosmopars):
        out = {
            "h": cosmopars["h"],
            "Omega_cdm": 0.26,
            "sigma8": 0.85,
            "A_s": 9.9e-9,
            "ln10^{10}A_s": 3.0,
        }
        if not smg_in_yaml:
            out["parameters_smg"] = "-5.301, 0.0"
        return out

    cosmopars = {"h": 0.67}
    # as boltzmann_code.__init__ builds it for cosmo_model = 'HuSawicki'
    classcosmopars = {
        **classpars["ACCURACY"],
        **classpars["COSMO_SETTINGS"],
        **classpars["HuSawicki"],
        **changebasis_class(cosmopars),
    }
    return SimpleNamespace(
        boltzmann_classpars=classpars,
        classcosmopars=classcosmopars,
        cosmopars=cosmopars,
        nonlinear_model="winther2019",
        cb_prescription=cb_prescription,
        results=SimpleNamespace(),
        changebasis_class=changebasis_class,
    )


@pytest.fixture
def fr_fakes(monkeypatch):
    """Patch classy, the nonlinear-grid helpers and the boost; record what they are called with."""
    record = SimpleNamespace(grid_calls=[], subtraction_calls=[], boost_calls=[], sigma8_calls=[])
    _FakeLcdm.instances = []
    _FakeLcdm.omega_m = 0.31
    monkeypatch.setitem(sys.modules, "classy", SimpleNamespace(Class=_FakeLcdm))

    def fake_grid(lcdm, k, z, cb=False):
        record.grid_calls.append(cb)
        return (2.0 * PK_GRID if cb else PK_GRID), K_GRID, Z_GRID

    def fake_subtraction(lcdm, pk, k, z):
        record.subtraction_calls.append((pk, k, z))
        return 0.5 * pk

    def fake_boost_grid(model, k, z, lgfR0, h, **kwargs):
        record.boost_calls.append(
            {"model": model, "k": k, "z": z, "lgfR0": lgfR0, "h": h, **kwargs}
        )
        return BOOST

    def fake_sigma8(k, pk, h, lgfR0):
        record.sigma8_calls.append((k, pk, h, lgfR0))
        return 0.77

    monkeypatch.setattr(cosmology, "_class_nonlinear_pk_grid", fake_grid)
    monkeypatch.setattr(cosmology, "_class_cb_subtraction_grid", fake_subtraction)
    monkeypatch.setattr(modified_gravity, "fofR_boost_grid", fake_boost_grid)
    monkeypatch.setattr(modified_gravity, "sigma8_fofR", fake_sigma8)
    return record


def test_fr_boost_nonlinear_builds_lcdm_run_with_the_f_of_R_amplitude(fr_fakes):
    bc = _fake_bc()

    pk_nl, pk_cb_nl, k_nl, z_nl = modified_gravity.fr_boost_nonlinear(
        bc, _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    (lcdm,) = _FakeLcdm.instances
    assert lcdm.computed and lcdm.cleaned and lcdm.emptied
    params = lcdm.params
    assert (
        params["accuracy_key"] == 1 and params["setting_key"] == 2 and params["lcdm_only_key"] == 3
    )
    # the LCDM run takes A_s of the f(R) run, not the sigma8/A_s of the input basis
    assert params["A_s"] == pytest.approx(2.1e-9)
    assert "sigma8" not in params and "ln10^{10}A_s" not in params
    assert "parameters_smg" not in params
    assert params["non linear"] == "hmcode_2020"
    np.testing.assert_array_equal(k_nl, K_GRID)
    np.testing.assert_array_equal(z_nl, Z_GRID)
    np.testing.assert_allclose(pk_nl, PK_GRID * BOOST)


def test_fr_boost_nonlinear_passes_likelihood_inputs_to_the_boost(fr_fakes):
    bc = _fake_bc(
        nonlinear_conf={"lcdm_nonlinear": "halofit", "fofR_settings": {"k_max_h_by_Mpc": 30.0}},
    )
    bc.nonlinear_model = "emantis"

    modified_gravity.fr_boost_nonlinear(
        bc, _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    (lcdm,) = _FakeLcdm.instances
    assert lcdm.params["non linear"] == "halofit"
    (call,) = fr_fakes.boost_calls
    assert call["model"] == "emantis"
    assert call["lgfR0"] == pytest.approx(5.301)  # -log10fR0 from "parameters_smg"
    assert call["h"] == pytest.approx(0.67)
    assert call["Omega_m"] == pytest.approx(0.26 + 0.05 + 0.0)  # Omega0_cdm + Omega_b + Omega_nu
    assert call["sigma8_lcdm"] == pytest.approx(0.8)
    assert call["settings"] == {"k_max_h_by_Mpc": 30.0}


def test_fr_boost_nonlinear_reads_parameters_smg_from_the_husawicki_yaml_section(fr_fakes):
    bc = _fake_bc(smg_in_yaml=True)

    modified_gravity.fr_boost_nonlinear(
        bc, _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    (call,) = fr_fakes.boost_calls
    assert call["lgfR0"] == pytest.approx(5.301)
    (lcdm,) = _FakeLcdm.instances
    assert "parameters_smg" not in lcdm.params


def test_fr_boost_nonlinear_preserves_shared_husawicki_inputs(fr_fakes):
    # T_cmb and Omega_fld exist only in the HuSawicki section: the f(R) run uses them, so the
    # reference LCDM run must too. Its closure, however, comes from the LCDM section.
    bc = _fake_bc(
        husawicki_overrides={
            "T_cmb": 2.8,
            "N_ncdm": 3,
            "Omega_Lambda": 0.0,
            "Omega_fld": 0.0,
            "hs_field": "u",
            "qsa_only_smg": "yes",
            "kineticity_safe_smg": 0,
            "hubble_evolution": "no",
            "skip_stability_tests_smg": "yes",
            "hs_handoff_ic_smg": "slow",
        },
        lcdm_overrides={"Omega_Lambda": 0.7},
    )

    modified_gravity.fr_boost_nonlinear(
        bc, _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    (lcdm,) = _FakeLcdm.instances
    params = lcdm.params
    assert params["T_cmb"] == pytest.approx(2.8)
    assert params["N_ncdm"] == 3
    assert params["Omega_Lambda"] == pytest.approx(0.7)
    assert "Omega_fld" not in params
    for key in (
        "gravity_model",
        "parameters_smg",
        "Omega_smg",
        "qsa_only_smg",
        "kineticity_safe_smg",
        "hubble_evolution",
    ):
        assert key not in params


def test_fr_boost_nonlinear_stores_derived_sigma8_values(fr_fakes):
    bc = _fake_bc()

    modified_gravity.fr_boost_nonlinear(
        bc, _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    assert bc.results.lcdm_sigma8 == pytest.approx(0.8)
    assert bc.results.sigma8_fofR_kazuya == pytest.approx(0.77)
    k, pk, h, lgfR0 = fr_fakes.sigma8_calls[0]
    np.testing.assert_allclose(pk, k * 2.0)  # last redshift column of the linear LCDM P(k)
    assert h == pytest.approx(0.67) and lgfR0 == pytest.approx(5.301)


def test_fr_boost_nonlinear_without_neutrinos_reuses_total_matter_for_cb(fr_fakes):
    pk_nl, pk_cb_nl, _, _ = modified_gravity.fr_boost_nonlinear(
        _fake_bc(), _FakeFrRun(), np.array([0.01, 1.0]), np.array([0.0, 1.0])
    )

    assert fr_fakes.grid_calls == [False]
    assert fr_fakes.subtraction_calls == []
    np.testing.assert_array_equal(pk_cb_nl, pk_nl)


def test_fr_boost_nonlinear_neutrino_subtraction_for_cb(fr_fakes):
    _FakeLcdm.omega_m = 0.32  # f_nu = 1 - 0.31 / 0.32 > 0

    pk_nl, pk_cb_nl, _, _ = modified_gravity.fr_boost_nonlinear(
        _fake_bc(cb_prescription="neutrino_subtraction"),
        _FakeFrRun(),
        np.array([0.01, 1.0]),
        np.array([0.0, 1.0]),
    )

    assert fr_fakes.grid_calls == [False]
    assert len(fr_fakes.subtraction_calls) == 1
    np.testing.assert_allclose(pk_cb_nl, 0.5 * PK_GRID * BOOST)


def test_fr_boost_nonlinear_direct_cb_spectrum_for_other_prescriptions(fr_fakes):
    _FakeLcdm.omega_m = 0.32

    _, pk_cb_nl, _, _ = modified_gravity.fr_boost_nonlinear(
        _fake_bc(cb_prescription="class_cb"),
        _FakeFrRun(),
        np.array([0.01, 1.0]),
        np.array([0.0, 1.0]),
    )

    assert fr_fakes.grid_calls == [False, True]
    assert fr_fakes.subtraction_calls == []
    np.testing.assert_allclose(pk_cb_nl, 2.0 * PK_GRID * BOOST)

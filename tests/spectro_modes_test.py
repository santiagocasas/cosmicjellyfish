"""Tests for the GCspxIM observable and the joint auto + cross spectroscopic analysis."""

from __future__ import annotations

import warnings

import numpy as np
import pytest

from cosmicjellyfish.analysis.fisher_operations import marginalise
from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.LSSsurvey import spectro_modes as modes


def test_single_probes_keep_their_mode():
    assert modes.resolve_spectro_observables(["GCph", "WL"]) == (["GCph", "WL"], None)
    assert modes.resolve_spectro_observables(["GCsp"]) == (["GCsp"], "gg")
    assert modes.resolve_spectro_observables(["IM"]) == (["IM"], "II")


def test_cross_and_joint_selection():
    cross, mode = modes.resolve_spectro_observables(["GCspxIM"])
    assert mode == "Ig" and cross == ["GCsp", "IM", "GCspxIM"]
    # the flag and the explicit list ask for the same joint analysis
    flagged = modes.resolve_spectro_observables(["GCspxIM"], joint=True)
    listed = modes.resolve_spectro_observables(["GCsp", "GCspxIM", "IM"])
    assert flagged == listed == (["GCsp", "IM", "GCspxIM"], "joint")
    # non-spectroscopic probes are untouched
    assert modes.resolve_spectro_observables(["WL", "GCspxIM"])[0][0] == "WL"


def test_legacy_pair_is_a_deprecated_cross_alias():
    with pytest.warns(FutureWarning, match="cross-spectrum only"):
        resolved, mode = modes.resolve_spectro_observables(["GCsp", "IM"])
    assert mode == "Ig" and resolved == ["GCsp", "IM", "GCspxIM"]


def test_cross_with_a_single_auto_spectrum_is_rejected():
    for observables in (["GCsp", "GCspxIM"], ["IM", "GCspxIM"]):
        with pytest.raises(ValueError, match="GCspxIM"):
            modes.resolve_spectro_observables(observables)


def test_mode_lookup_prefers_the_stored_setting():
    assert modes.spectro_mode(["GCsp", "IM"]) == "Ig"
    assert modes.spectro_mode(["GCsp", "IM"], {"spectro_mode": "joint"}) == "joint"
    assert modes.spectrum_pair("II") == ["I", "I"]
    assert modes.spectrum_pair(None) is None


def _random_covariance(shape, rng):
    cov_ii = 1.0 + rng.random(shape)
    cov_gg = 1.0 + rng.random(shape)
    cov_ig = 0.5 * np.sqrt(cov_ii * cov_gg) * rng.random(shape)
    return cov_ii, cov_ig, cov_gg


def test_joint_trace_matches_explicit_matrix_products():
    rng = np.random.default_rng(1)
    shape = (3, 4)
    cov_ii, cov_ig, cov_gg = _random_covariance(shape, rng)
    d_ii = [rng.normal(size=shape) for _ in range(2)]
    d_ig = [rng.normal(size=shape) for _ in range(2)]
    d_gg = [rng.normal(size=shape) for _ in range(2)]
    kernel = modes.joint_gaussian_trace(cov_ii, cov_ig, cov_gg, d_ii, d_ig, d_gg)
    assert kernel.shape == (2, 2) + shape
    for ik in range(shape[0]):
        for jk in range(shape[1]):
            cov = np.array([[cov_ii[ik, jk], cov_ig[ik, jk]], [cov_ig[ik, jk], cov_gg[ik, jk]]])
            inv = np.linalg.inv(cov)
            dcov = [
                np.array([[d_ii[p][ik, jk], d_ig[p][ik, jk]], [d_ig[p][ik, jk], d_gg[p][ik, jk]]])
                for p in range(2)
            ]
            for p in range(2):
                for q in range(2):
                    expected = np.trace(inv @ dcov[p] @ inv @ dcov[q])
                    assert kernel[p, q, ik, jk] == pytest.approx(expected, rel=1e-12)


def test_joint_trace_reduces_to_the_sum_of_single_tracers_without_correlation():
    rng = np.random.default_rng(2)
    shape = (2, 5)
    cov_ii, _, cov_gg = _random_covariance(shape, rng)
    zero = np.zeros(shape)
    d_ii = [rng.normal(size=shape)]
    d_gg = [rng.normal(size=shape)]
    kernel = modes.joint_gaussian_trace(cov_ii, zero, cov_gg, d_ii, [zero], d_gg)
    expected = d_ii[0] ** 2 / cov_ii**2 + d_gg[0] ** 2 / cov_gg**2
    np.testing.assert_allclose(kernel[0, 0], expected, rtol=1e-12)


def test_joint_trace_rejects_a_singular_covariance():
    ones = np.ones((2, 2))
    with pytest.raises(ValueError, match="positive definite"):
        modes.joint_gaussian_trace(ones, ones, ones, [ones], [ones], [ones])


# ---------------------------------------------------------------------------
# end-to-end on a coarse grid (a few seconds each)
# ---------------------------------------------------------------------------
_FIDUCIAL = {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.822, "mnu": 0.06}
_FREE = dict.fromkeys(("Omegam", "h", "sigma8"), 0.002)


def _forecast(observables, tmp_path, **options):
    settings = {
        "code": "symbolic",
        "nonlinear": True,
        "feedback": 0,
        "derivatives": "3PT",
        "spectro_Pk_k_samples": 24,
        "spectro_Pk_mu_samples": 5,
        "survey_name_spectro": "DESI-ELG-SKAOPaper",
        "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        "results_dir": str(tmp_path),
        "outroot": "modes_" + "_".join(observables),
    }
    settings.update(options)
    fisher = FisherMatrix(
        options=settings,
        observables=list(observables),
        freepars=dict(_FREE),
        fiducialpars=dict(_FIDUCIAL),
        surveyName="SKAO",
        cosmoModel="LCDM",
    )
    result = fisher.compute()
    return fisher, marginalise(result, list(_FREE))


def _sigma(matrix):
    return np.sqrt(np.diag(np.linalg.inv(matrix.fisher_matrix)))


def test_cross_name_matches_the_legacy_pair_and_joint_flag_matches_the_list(tmp_path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        _, legacy = _forecast(("GCsp", "IM"), tmp_path)
    fisher, cross = _forecast(("GCspxIM",), tmp_path)
    assert fisher.settings["spectro_mode"] == "Ig"
    np.testing.assert_allclose(cross.fisher_matrix, legacy.fisher_matrix, rtol=1e-12)

    fisher, listed = _forecast(("GCsp", "GCspxIM", "IM"), tmp_path)
    assert fisher.settings["spectro_mode"] == "joint"
    _, flagged = _forecast(("GCspxIM",), tmp_path, spectro_joint=True)
    np.testing.assert_allclose(flagged.fisher_matrix, listed.fisher_matrix, rtol=1e-12)


def test_joint_analysis_is_symmetric_and_beats_each_auto_spectrum(tmp_path):
    _, galaxies = _forecast(("GCsp",), tmp_path)
    _, intensity = _forecast(("IM",), tmp_path)
    _, joint = _forecast(("GCsp", "GCspxIM", "IM"), tmp_path)
    matrix = joint.fisher_matrix
    np.testing.assert_allclose(matrix, matrix.T, rtol=1e-10)
    assert np.all(np.linalg.eigvalsh(matrix) > 0)
    assert np.all(_sigma(joint) < _sigma(galaxies))
    assert np.all(_sigma(joint) < _sigma(intensity))

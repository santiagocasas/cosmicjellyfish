"""Covariance paths for the migrated DESI and SKAO specifications."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("symbolic_pofk")

from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.LSSsurvey.spectro_cov import SpectroCov
from cosmicjellyfish.LSSsurvey.spectro_obs import ComputeGalSpectro

FIDUCIAL = {"Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "sigma8": 0.822}


def _covariance(survey, observables, extra_options=None, specifications=None):
    options = {"code": "symbolic", "nonlinear": True, "feedback": 0}
    options.update(extra_options or {})
    fisher = FisherMatrix(
        options=options,
        specifications=specifications or {},
        observables=observables,
        freepars={"Omegam": 0.01},
        fiducialpars=FIDUCIAL,
        surveyName=survey,
        cosmoModel="LCDM",
    )
    spectrum = ["I", "g"] if "IM" in observables and "GCsp" in observables else None
    if spectrum is None:
        spectrum = ["I", "I"] if "IM" in observables else ["g", "g"]
    obs = ComputeGalSpectro(
        cosmopars=fisher.fiducialcosmopars,
        fiducial_cosmopars=fisher.fiducialcosmopars,
        spectrobiaspars=fisher.Spectrobiaspars,
        spectrononlinearpars=fisher.Spectrononlinpars,
        IMbiaspars=fisher.IMbiaspars,
        PShotpars=fisher.PShotpars,
        configuration=fisher,
    )
    cov = SpectroCov(
        fisher.fiducialcosmopars,
        fiducial_specobs=obs,
        bias_samples=spectrum,
        configuration=fisher,
    )
    return cov, obs


def test_desi_elg_covariance_is_positive_inside_the_bins():
    cov, _ = _covariance("DESI", ["GCsp"], {"survey_name_spectro": "DESI-ELG-SKAOPaper"})
    assert len(cov.inter_z_bin_mids) == 11
    k, mu = np.meshgrid(np.array([0.02, 0.05]), np.array([0.0, 0.5, 1.0]))
    for index, z in enumerate(cov.inter_z_bin_mids):
        volume = cov.volume_survey(index)
        density = cov.n_density(z)
        veff = cov.veff(z, k, mu)
        assert np.isfinite(volume) and volume > 0.0
        assert np.isfinite(density) and density > 0.0
        assert np.all(np.isfinite(veff)) and np.all(veff > 0.0)
    # Outside the survey redshift range the effective volume is zero.
    assert np.all(cov.veff(2.0, k, mu) == 0.0)


def test_skao_im_volume_uses_the_im_sky_fraction():
    cov, _ = _covariance("SKAO", ["IM"])
    fsky_im = float(cov.config.specs["fsky_IM"])
    assert cov.fsky_volume == pytest.approx(fsky_im)
    for index in range(len(cov.inter_z_bin_mids)):
        assert cov.volume_survey(index) == pytest.approx(fsky_im * cov.d_volume(index))
    # The noise term and the volume must use the same footprint, otherwise the forecast
    # is neither IM-only nor spectroscopic.
    assert cov.fsky_volume == pytest.approx(float(cov.pk_obs.fsky_IM))


def test_skao_im_desi_cross_covariance_matches_the_overlap():
    cov, _ = _covariance(
        "SKAO",
        ["GCspxIM"],
        {
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
    )
    assert len(cov.inter_z_bin_mids) == 11
    # Without an explicit ``fsky_cross`` the overlap is approximated by the nested
    # footprint min(fsky_spectro, fsky_IM); the flag records that assumption.
    assert cov.fsky_cross_assumed_nested
    assert cov.fsky_volume == pytest.approx(
        min(cov.fsky_spectro, float(cov.config.specs["fsky_IM"]))
    )
    k, mu = np.meshgrid(np.array([0.02]), np.array([0.5]))
    for index, z in enumerate(cov.inter_z_bin_mids):
        assert cov.volume_survey(index) > 0.0
        # The cross-spectrum forecast uses veff_Ig, not the galaxy auto-spectrum veff.
        assert np.all(cov.veff_Ig(z, k, mu) > 0.0)


def test_cross_footprint_can_be_set_explicitly():
    cov, _ = _covariance(
        "SKAO",
        ["GCspxIM"],
        {
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
        specifications={"fsky_cross": 0.2},
    )
    assert not cov.fsky_cross_assumed_nested
    assert cov.fsky_volume == pytest.approx(0.2)


def test_cross_footprint_larger_than_the_nested_one_is_rejected():
    with pytest.raises(ValueError, match="fsky_cross"):
        _covariance(
            "SKAO",
            ["GCspxIM"],
            {
                "survey_name_spectro": "DESI-ELG-SKAOPaper",
                "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
            },
            specifications={"fsky_cross": 0.9},
        )


def test_changing_the_bias_model_needs_the_matching_bias_root():
    # the root is the key prefix of the active model, so 'linear_log' (keys lnbg_i) needs 'lnb'
    def build(specifications):
        return FisherMatrix(
            options={
                "code": "symbolic",
                "feedback": 0,
                "survey_name_spectro": "DESI-BGS-SKAOPaper",
            },
            specifications=specifications,
            observables=["GCsp"],
            freepars={"Omegam": 0.01},
            fiducialpars=FIDUCIAL,
            surveyName="DESI",
            cosmoModel="LCDM",
        )

    with pytest.raises(ValueError, match="sp_bias_root"):
        build({"sp_bias_model": "linear_log"})
    fisher = build({"sp_bias_model": "linear_log", "sp_bias_root": "lnb"})
    assert "lnbg_1" in fisher.Spectrobiaspars

import numpy as np
import pytest

import cosmicjellyfish.configs.config as cfg
from cosmicjellyfish.LSSsurvey.spectro_cov import SpectroCov, SpectroDerivs
from cosmicjellyfish.utilities.utils import physmath as upm


def test_spectro_cov_initialization(spectro_fisher_matrix):
    cosmoFM = spectro_fisher_matrix
    # reuse fiducial cosmological parameters subset for speed
    fiducialpars = dict(cosmoFM.fiducialcosmopars)
    spec_cov = SpectroCov(fiducialpars, configuration=cosmoFM)
    assert isinstance(spec_cov, SpectroCov)
    # basic attributes set
    assert np.isclose(
        spec_cov.fsky_spectro, cosmoFM.specs.get("fsky_spectro", spec_cov.fsky_spectro)
    )


def test_spectro_cov_volume_and_density(spectro_fisher_matrix):
    cosmoFM = spectro_fisher_matrix
    fiducialpars = dict(cosmoFM.fiducialcosmopars)
    spec_cov = SpectroCov(fiducialpars, configuration=cosmoFM)
    # pick first bin
    vol_bin0 = spec_cov.d_volume(0)
    assert vol_bin0 > 0
    survey_vol0 = spec_cov.volume_survey(0)
    assert np.isclose(survey_vol0, spec_cov.fsky_spectro * vol_bin0)
    # number density at mid of first bin
    z0 = spec_cov.global_z_bin_mids[0]
    nd = spec_cov.n_density(z0)
    assert nd >= 0


def test_spectro_cov_noise_and_noisy_pk(spectro_fisher_matrix):
    cosmoFM = spectro_fisher_matrix
    fiducialpars = dict(cosmoFM.fiducialcosmopars)
    spec_cov = SpectroCov(fiducialpars, configuration=cosmoFM)
    # simple k, mu arrays
    k = np.array([0.1])
    mu = np.array([0.5])
    z = float(spec_cov.global_z_bin_mids[0])
    # Only call the 21cm noise routine if the Intensity Mapping observable is present.
    # The default fixture uses only GCsp so ComputeGalSpectro does not define fsky_IM.
    if "IM" in spec_cov.pk_obs.observables:
        noise_21 = spec_cov.P_noise_21(z, k, mu)
        assert np.all(noise_21 >= 0)
    # galaxy shot noise branch in noisy_P_ij
    pnoisy_gg = spec_cov.noisy_P_ij(z, k, mu, si="g", sj="g")
    pnoisy_II = (
        spec_cov.noisy_P_ij(z, k, mu, si="I", sj="I")
        if "IM" in spec_cov.pk_obs.observables
        else None
    )
    assert np.all(pnoisy_gg > 0)
    if pnoisy_II is not None:
        assert np.all(pnoisy_II > 0)


def test_spectro_cov_effective_volumes_basic(spectro_fisher_matrix):
    cosmoFM = spectro_fisher_matrix
    fiducialpars = dict(cosmoFM.fiducialcosmopars)
    spec_cov = SpectroCov(fiducialpars, configuration=cosmoFM)
    k = np.array([0.1])
    mu = np.array([0.5])
    z = float(spec_cov.global_z_bin_mids[0])
    if spec_cov.pk_obs.observables == ["GCsp"]:
        # only galaxy clustering; veff uses n_density path indirectly
        veff_like = spec_cov.veff(z, k, mu)
        # ensure non-negative: coerce to numpy array
        veff_arr = np.array(veff_like, copy=False)
        assert np.all(veff_arr >= 0)
    # we always can call noisy_P_ij for gg and use it within a simple covariance style expression
    pnoisy = spec_cov.noisy_P_ij(z, k, mu, si="g", sj="g")
    assert pnoisy.shape == (1,)


def test_spectro_derivs_wrapper_minimal(spectro_fisher_matrix):
    cosmoFM = spectro_fisher_matrix
    fiducialpars = dict(cosmoFM.fiducialcosmopars)
    spec_cov = SpectroCov(fiducialpars, configuration=cosmoFM)
    # small meshes to keep fast
    kmesh = np.array([0.1])
    mumesh = np.array([0.0, 0.5])
    z_array = np.array(spec_cov.global_z_bin_mids[:1])  # just first bin
    deriv_engine = SpectroDerivs(
        z_array=z_array,
        pk_kmesh=kmesh,
        pk_mumesh=mumesh,
        fiducial_spectro_obj=spec_cov.pk_obs,
        bias_samples=["g", "g"],
        configuration=cosmoFM,
    )
    # provide simple freeparams for one cosmological parameter
    freeparams = {"Omegam": 0.01}
    derivs = deriv_engine.compute_derivs(freeparams=freeparams)
    assert isinstance(derivs, dict)
    # structure: parameter -> redshift index -> array
    if "Omegam" in derivs:
        first_par = derivs["Omegam"]
        assert 0 in first_par


def test_spectro_derivatives_remain_bound_to_context_a(spectro_fisher_matrix, monkeypatch):
    context_a = spectro_fisher_matrix
    spec_cov = SpectroCov(dict(context_a.fiducialcosmopars), configuration=context_a)
    deriv_engine = SpectroDerivs(
        z_array=np.array(spec_cov.global_z_bin_mids[:1]),
        pk_kmesh=np.array([0.1]),
        pk_mumesh=np.array([0.0, 0.5]),
        fiducial_spectro_obj=spec_cov.pk_obs,
        bias_samples=["g", "g"],
        configuration=context_a,
    )

    monkeypatch.setattr(cfg, "freeparams", {"wrong": 99.0})
    monkeypatch.setattr(cfg, "settings", {"feedback": 99, "derivatives": "UNKNOWN"})
    monkeypatch.setattr(cfg, "obs", ["UNKNOWN"])
    monkeypatch.setattr(cfg, "external", {"wrong": True})

    class CaptureProvider:
        def compute(self, request):
            assert request.configuration is context_a
            assert request.freeparams == dict(context_a.freeparams)
            assert request.observables_type == tuple(context_a.observables)
            assert request.external_settings == context_a.external
            assert request.method == context_a.settings["derivatives"]
            return {"spectro": "context-a"}

    # Omit freeparams here (rather than passing an explicit override) so this
    # test actually exercises the default-path wiring: compute_derivs() must
    # fall back to context_a.freeparams, not the monkeypatched global cfg.
    result = deriv_engine.compute_derivs(derivative_provider=CaptureProvider())

    assert result == {"spectro": "context-a"}


# ---------------------------------------------------------------------------
# shared galaxy / intensity-mapping bins (no cosmology needed)
# ---------------------------------------------------------------------------
class _BothProbes:
    observables = ["GCsp", "IM"]


def _two_grid_cov(gal_edges, im_edges, dnz):
    """A SpectroCov holding only the bin bookkeeping; a cubic shell stands in for the volume."""
    gal, im = np.asarray(gal_edges, float), np.asarray(im_edges, float)
    cov = object.__new__(SpectroCov)
    cov.pk_obs = _BothProbes()
    cov.z_bins, cov.z_bin_mids = gal, 0.5 * (gal[1:] + gal[:-1])
    cov.IM_z_bins, cov.IM_z_bin_mids = im, 0.5 * (im[1:] + im[:-1])
    cov.dnz, cov.dz_bins = np.asarray(dnz, float), np.diff(gal)
    cov.inter_z_bin_mids = np.intersect1d(cov.z_bin_mids, cov.IM_z_bin_mids)
    cov.fsky_volume = 1.0
    cov.volume_bin = lambda lo, hi: hi**3 - lo**3
    cov._set_shared_bins()
    return cov


def test_shared_bin_uses_its_own_interval_when_the_grids_differ_in_extent():
    # galaxy bins [0.8, 1.0], [1.0, 1.2]; IM bins [1.0, 1.2], [1.2, 1.4]: only [1.0, 1.2] is shared
    cov = _two_grid_cov([0.8, 1.0, 1.2], [1.0, 1.2, 1.4], dnz=[100.0, 200.0])
    assert list(cov.inter_z_bin_mids) == [1.1]
    assert cov.inter_bin_edges == [(1.0, 1.2)] and cov.inter_gal_index == [1]
    shell = 1.2**3 - 1.0**3  # not the volume of [0.8, 1.0], which the union of the edges gave
    assert np.isclose(cov.d_volume(0), shell)
    assert np.isclose(cov.volume_survey(0), shell)
    # the galaxy density is that of the [1.0, 1.2] galaxy bin (200), not of the first one (100)
    expected = upm.areasky() * 200.0 * 0.2 / shell
    assert np.isclose(cov.n_density(1.1), expected)


def test_identical_grids_keep_the_bin_order():
    edges = [0.6, 0.7, 0.8, 0.9]
    cov = _two_grid_cov(edges, edges, dnz=[1.0, 2.0, 3.0])
    assert cov.inter_gal_index == [0, 1, 2]
    assert cov.inter_bin_edges == [(0.6, 0.7), (0.7, 0.8), (0.8, 0.9)]
    for index, (lo, hi) in enumerate(cov.inter_bin_edges):
        assert np.isclose(cov.d_volume(index), hi**3 - lo**3)


def test_bins_with_a_shared_midpoint_but_different_edges_are_rejected():
    # [1.6, 1.7] and [1.5, 1.8] both have the midpoint 1.65 but are different intervals
    with pytest.raises(ValueError, match="share the midpoint"):
        _two_grid_cov([1.6, 1.7], [1.5, 1.8], dnz=[1.0])

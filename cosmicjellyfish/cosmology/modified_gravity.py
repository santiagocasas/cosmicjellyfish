"""Hu-Sawicki f(R) nonlinear boosts on a LCDM nonlinear power spectrum: P_NL^{f(R)} = B(k, z) x P_NL^{LCDM}.

Reproduces the f(R) part of the MontePython likelihood ``euclid_photometric_z_fofr``,
https://github.com/Sefa76/photometric_fofR/blob/main/codes/euclid_photometric_z_fofr/__init__.py
(used in Euclid Collaboration: Koyama et al. 2024, arXiv:2409.03524):

- ``'winther2019'``: block ``if self.use_fofR == 'Winther'`` (L. ~403). Winther+2019 fitting
  formula, ``f_r_emulators/MGfit_Winther.py`` (verbatim copy), ``hasBug = use_bug`` (False in the
  ``.data`` file).
- ``'emantis'``: block ``elif self.use_fofR == 'emantis'`` (L. ~554). e-MANTIS
  ``FofrBoost(Omega_m, sigma8_LCDM, -log10|f_R0|)``, with Omega_m and sigma8_LCDM clipped to the
  emulator range, and a 2D spline in (z, k).
- extrapolation: block 'Extrapolation for the Different boosts' (L. ~596-645). Power law in k
  above ``fofR_kmax`` and in z above ``fofR_zmax = 2``, fitted on the last 20 % of the range; boost
  clipped to [1, 2]; B = 1 outside ``k_min_h_by_Mpc < k/h < k_max_h_by_Mpc``.

Variable names follow the likelihood. Units: k in 1/Mpc unless stated (as in the likelihood).
Defaults are those of ``euclid_photometric_z_fofr.data``: ``use_bug = False``,
``fofR_interpolation_k_boost = 40``, ``fofR_interpolation_z_boost = 4``,
``k_min_h_by_Mpc = 0.001``, ``k_max_h_by_Mpc = 50``, ``z = linspace(0.001, 2.5, 200)``.
"""

from copy import deepcopy
from functools import lru_cache

import numpy as np
from scipy.integrate import simpson
from scipy.interpolate import RectBivariateSpline, interp1d
from scipy.optimize import curve_fit

from cosmicjellyfish.cosmology.f_r_emulators.MGfit_Winther import (
    kazuya_correktion,
    pofk_enhancement,
    pofk_enhancement_linear,
)

FR_BOOST_MODELS = ("winther2019", "emantis")

LKL_DEFAULTS = {
    "use_bug": False,
    "fofR_interpolation_k_boost": 40,
    "fofR_interpolation_z_boost": 4,
    "k_min_h_by_Mpc": 0.001,
    "k_max_h_by_Mpc": 50.0,
    "zmin": 0.001,
    "zmax": 2.5,
    "nzmax": 200,
}


@lru_cache(maxsize=1)
def _emantis():
    # as in the likelihood: high-z extrapolation done outside e-MANTIS (power law, below)
    from emantis import FofrBoost

    return FofrBoost(verbose=False, extrapolate_aexp=False, extrapolate_low_k=True)


def fofR_boost_function(model, lgfR0, h, Omega_m=None, sigma8_lcdm=None, settings=None):
    """(fofR_boost(k [1/Mpc], z), fofR_kmax [1/Mpc], fofR_zmax) as in the likelihood.

    lgfR0 = -log10|f_R0| (> 0). For 'emantis': Omega_m = Omega_cdm + Omega_b + Omega_nu and sigma8_lcdm of the
    LCDM cosmology with the same A_s (in the likelihood, the LCDM CLASS run).
    """
    s = {**LKL_DEFAULTS, **(settings or {})}
    f_R0 = np.power(10.0, -1 * lgfR0)
    if model == "winther2019":
        fofR_zmax = 2
        fofR_kmax = 10 * h  # In 1/Mpc

        def fofR_boost(k_l, z_l):
            return pofk_enhancement(z_l, f_R0, k_l / h, hasBug=s["use_bug"])

    elif model == "emantis":
        emantis = _emantis()
        # Keep the likelihood's bounds where the installed emulator supports them.
        omega_min, omega_max = emantis.emulation_range["omega_m"]
        sigma8_min, sigma8_max = emantis.emulation_range["sigma8_lcdm"]
        emantis_Omm = np.clip(Omega_m, max(0.24, omega_min), min(0.39, omega_max))
        emantis_s8 = np.clip(sigma8_lcdm, max(0.60, sigma8_min), min(1.00, sigma8_max))

        # Get e-mantis predictions for all z and k within emulator bounds
        fofR_kmax = emantis.kbins[-1] * h
        fofR_zmax = 2

        z_lkl = np.linspace(s["zmin"], s["zmax"], num=s["nzmax"])
        k_grid_emantis = np.geomspace(0.01, fofR_kmax, 100)
        z_grid_emantis = z_lkl[z_lkl <= fofR_zmax]

        B_grid_emantis = emantis.predict_boost(
            emantis_Omm, emantis_s8, lgfR0, 1 / (1 + z_grid_emantis), k_grid_emantis / h
        )
        interp_Boost = RectBivariateSpline(z_grid_emantis, k_grid_emantis, B_grid_emantis[:, 0, :])

        def fofR_boost(k, z):
            return interp_Boost(z, k)

    else:
        raise ValueError(f"Unknown f(R) boost model {model!r}; expected one of {FR_BOOST_MODELS}.")
    return fofR_boost, fofR_kmax, fofR_zmax


def boost_extrapolation(fofR_boost, fofR_kmax, fofR_zmax, settings=None):
    """Boost_extrapolation(k [1/Mpc], z) of the likelihood: power-law extrapolation beyond fofR_kmax and
    fofR_zmax, clipped to [1, 2]."""
    s = {**LKL_DEFAULTS, **(settings or {})}
    nk_b, nz_b = s["fofR_interpolation_k_boost"], s["fofR_interpolation_z_boost"]
    # Setup the grid on which we will do the fitting
    k_cut = np.geomspace(0.8 * fofR_kmax, fofR_kmax, 5)
    z_cut = np.linspace(0.8 * fofR_zmax, fofR_zmax, 5)
    k_long = np.geomspace(0.01, fofR_kmax, 5 * nk_b)
    z_long = np.linspace(0, fofR_zmax, 5 * nz_b)

    # linear extrapolation in log log
    logk_cut = np.log(k_cut)
    logz_cut = np.log(z_cut)
    # k extrapolation -> grid : k_cut, z_long
    logBoostk = np.ones((5, 5 * nz_b))
    k_power = []
    for iz, zi in enumerate(z_long):
        for ik, ki in enumerate(k_cut):
            logBoostk[ik, iz] = np.log(fofR_boost(ki, zi)).item()
        # fix boost at highest k to emulator value
        popt, _ = curve_fit(
            lambda x, gamma: logBoostk[-1, iz] + gamma * (x - logk_cut[-1]),
            logk_cut,
            logBoostk[:, iz],
        )
        k_power.append(popt[0])
    gammak_z = interp1d(z_long, k_power)

    # z extrapolation -> grid : k_long, z_cut
    logBoostz = np.ones((5 * nk_b, 5))
    z_power = []
    for ik, ki in enumerate(k_long):
        for iz, zi in enumerate(z_cut):
            logBoostz[ik, iz] = np.log(fofR_boost(ki, zi)).item()
        # fix boost at highest z to emulator value
        popt, _ = curve_fit(
            lambda x, gamma: logBoostz[ik, -1] + gamma * (x - logz_cut[-1]),
            logz_cut,
            logBoostz[ik, :],
        )
        z_power.append(popt[0])
    gammaz_k = interp1d(k_long, z_power)

    def Boost_extrapolation(k, z):
        return np.clip(
            fofR_boost(np.clip(k, 0.01, fofR_kmax), np.minimum(z, fofR_zmax))
            * (np.maximum(z, fofR_zmax) / fofR_zmax) ** gammaz_k(np.clip(k, 0.01, fofR_kmax))
            * (np.maximum(k, fofR_kmax) / fofR_kmax) ** gammak_z(np.minimum(z, fofR_zmax)),
            1,
            2,
        )

    return Boost_extrapolation


def fofR_boost_grid(model, k, z, lgfR0, h, Omega_m=None, sigma8_lcdm=None, settings=None):
    """Boost on the grid k [1/Mpc, ascending] x z, shape (len(k), len(z)); B = 1 outside
    k_min_h_by_Mpc < k/h < k_max_h_by_Mpc (pknn_mask of the likelihood)."""
    s = {**LKL_DEFAULTS, **(settings or {})}
    k = np.asarray(k, dtype=float)
    z = np.atleast_1d(np.asarray(z, dtype=float))
    fofR_boost, fofR_kmax, fofR_zmax = fofR_boost_function(model, lgfR0, h, Omega_m, sigma8_lcdm, s)
    Boost_extrapolation = boost_extrapolation(fofR_boost, fofR_kmax, fofR_zmax, s)
    kmin_in_inv_Mpc = s["k_min_h_by_Mpc"] * h
    kmax_in_inv_Mpc = s["k_max_h_by_Mpc"] * h
    pknn_mask = (k > kmin_in_inv_Mpc) & (k < kmax_in_inv_Mpc)
    boost = np.ones((len(k), len(z)))
    for index_z, z_value in enumerate(z):
        boost[pknn_mask, index_z] = np.ravel(Boost_extrapolation(k[pknn_mask], z_value))
    return boost


def sigma8_fofR(k, Pk, h, lgfR0):
    """get_sigma8_fofR of the likelihood (L. 274-308), verbatim: sigma8 of f(R) from the LINEAR LCDM spectrum at z = 0
    times the linear Winther enhancement (pofk_enhancement_linear), corrected by kazuya_correktion to match MGCAMB.
    k [1/Mpc], Pk [Mpc^3] at z = 0, lgfR0 = -log10|f_R0|. Not used in the observables: with an f(R) Boltzmann code
    (frahi_class) sigma8 of f(R) is computed directly; this is kept as a derived quantity / cross-check.
    """
    x = k * 8 / h
    # Get Sigma window function
    W = 3 / np.power(x, 3) * (np.sin(x) - x * np.cos(x))
    for ix, xi in enumerate(x):
        if xi < 0.01:
            W[ix] = 1 - xi**2 / 10

    # Get fofR boost to linear spectrum
    fR0 = np.power(10.0, -lgfR0)
    Boost = np.array([pofk_enhancement_linear(0, fR0, ki / h) for ki in k])

    Integr = np.power(k * W, 2) * Pk * Boost / (2 * np.pi**2)
    sigma8 = np.sqrt(simpson(Integr, x=k)) * kazuya_correktion(lgfR0)

    return sigma8


def fr_boost_nonlinear(bc, classres, k, z):
    """Hu-Sawicki f(R) nonlinear spectra P_NL^{LCDM} x B(k, z) for cosmology.boltzmann_code `bc`
    (NONLINEAR model 'winther2019' or 'emantis'); called from boltzmann_code.class_results.

    classres: the f(R) run (frahi_class, linear only). P_NL^{LCDM}: official classy, LCDM with the same parameters and
    the same A_s as the f(R) run (the boosts are ratios at fixed initial conditions), nonlinear prescription
    NONLINEAR['lcdm_nonlinear'] (default 'hmcode_2020'; 'halofit' is Halofit-Takahashi, as in Casas+2023).
    B(k, z): fofR_boost_grid (likelihood euclid_photometric_z_fofr); settings overridable with
    NONLINEAR['fofR_settings'] (keys of LKL_DEFAULTS). The total-matter boost is also applied to the cb spectrum
    (approximation, as for EE2). Stored in bc.results: lcdm_sigma8 (input of e-MANTIS) and sigma8_fofR_kazuya
    (sigma8_fofR, derived quantity only). Returns Pk_nl, Pk_cb_nl, k_nl, z_nl.
    Previous own boost implementation (Winther transcribed from the paper, blending in log|f_R0|; e-MANTIS
    6-parameter emulator): scripts/validation/old/fr_boosts.py.
    """
    from classy import Class as ClassLCDM

    from cosmicjellyfish.cosmology.cosmology import (
        _class_cb_subtraction_grid,
        _class_nonlinear_pk_grid,
    )

    nl_conf = bc.boltzmann_classpars.get("NONLINEAR", {})
    cosmopars = deepcopy(bc.cosmopars)
    lcdmpars = {
        **bc.boltzmann_classpars["ACCURACY"],
        **bc.boltzmann_classpars["COSMO_SETTINGS"],
        **bc.boltzmann_classpars.get("LCDM", {}),
    }
    lcdmpars.update(bc.changebasis_class(cosmopars))
    # parameters_smg may come from cosmopars (log10fR0) or from the HuSawicki YAML section: read it
    # from the merged parameters of the f(R) run; the LCDM run must not get it.
    log10fR0 = float(str(bc.classcosmopars["parameters_smg"]).split(",")[0])
    lcdmpars.pop("parameters_smg", None)
    for key in ("sigma8", "A_s", "ln10^{10}A_s", "ln_A_s_1e10"):
        lcdmpars.pop(key, None)
    lcdmpars["A_s"] = classres.get_current_derived_parameters(["A_s"])["A_s"]
    lcdmpars["non linear"] = nl_conf.get("lcdm_nonlinear", "hmcode_2020")
    lcdm = ClassLCDM()
    lcdm.set(lcdmpars)
    lcdm.compute()
    Pk_nl, k_nl, z_nl = _class_nonlinear_pk_grid(lcdm, k, z)
    f_nu = 1 - (lcdm.Omega0_cdm() + lcdm.Omega_b()) / lcdm.Omega_m()
    if f_nu > 1e-5 and bc.cb_prescription == "neutrino_subtraction":
        Pk_cb_nl = _class_cb_subtraction_grid(lcdm, Pk_nl, k_nl, z_nl)
    elif f_nu > 1e-5:
        Pk_cb_nl, _, _ = _class_nonlinear_pk_grid(lcdm, k, z, cb=True)
    else:
        Pk_cb_nl = Pk_nl.copy()

    h = lcdm.h()
    # Omega_m for e-MANTIS as in the likelihood: Omega0_cdm + Omega_b + Omega_nu (LCDM run)
    boost = fofR_boost_grid(
        bc.nonlinear_model,
        k_nl,
        z_nl,
        -log10fR0,
        h,
        Omega_m=lcdm.Omega0_cdm() + lcdm.Omega_b() + lcdm.Omega_nu,
        sigma8_lcdm=lcdm.sigma8(),
        settings=nl_conf.get("fofR_settings"),
    )
    bc.results.lcdm_sigma8 = lcdm.sigma8()
    # derived only (as the likelihood's sigma8_fofR): linear LCDM P(k, z = 0) on the CLASS grid
    Pk_m_l_grid, k_grid, _ = lcdm.get_pk_and_k_and_z(nonlinear=False)
    bc.results.sigma8_fofR_kazuya = sigma8_fofR(k_grid, Pk_m_l_grid[:, -1], h, -log10fR0)
    lcdm.struct_cleanup()
    lcdm.empty()
    return Pk_nl * boost, Pk_cb_nl * boost, k_nl, z_nl

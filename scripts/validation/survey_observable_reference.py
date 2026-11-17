"""Reference implementations of the historical survey observables.

These functions transcribe the galaxy-clustering and intensity-mapping recipe used by the
historical ``cosmicfish_reloaded_skaproject`` checkout, i.e. the implementation behind
Casas et al. 2023 (arXiv:2210.05705). They are intentionally independent of
``cosmicjellyfish.LSSsurvey``: only the cosmology object is shared. A comparison therefore
isolates the observable algebra (number densities, survey volume, AP rescaling, Kaiser
term, FoG, de-wiggling, beam and noise) from the Boltzmann solver.

Provenance of each formula is noted in the docstrings with the original file and function.
The historical checkout is treated as read-only; nothing here writes to it.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

DEFAULT_HISTORICAL_DIR = Path(
    "/home/santiago/CosmoProjects/CosmicFish-Projects/cosmicfish_reloaded_skaproject"
)
HISTORICAL_DIR_ENV = "COSMICFISH_HISTORICAL_DIR"


def historical_project_dir() -> Path:
    """Return the historical project root, honouring ``COSMICFISH_HISTORICAL_DIR``."""
    root = Path(os.environ.get(HISTORICAL_DIR_ENV, DEFAULT_HISTORICAL_DIR))
    if not root.is_dir():
        raise FileNotFoundError(
            f"Historical survey project not found at {root}. Set {HISTORICAL_DIR_ENV} "
            "to the cosmicfish_reloaded_skaproject checkout."
        )
    return root


def load_spectro_table(filename: str) -> dict:
    """Read one of the historical ``*_GCsp.dat`` tables.

    The tables have an ``# area = N`` header (deg^2) followed by the columns
    ``zmin zm zmax dn3 bias``. ``dn3`` is dN/dz per square degree.

    Parameters
    ----------
    filename : str
        File name inside ``survey_specifications/``.

    Returns
    -------
    dict
        Keys ``area``, ``zmin``, ``zm``, ``zmax``, ``dndz``, ``bias`` and ``path``.
    """
    path = historical_project_dir() / "survey_specifications" / filename
    area = None
    rows = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if "area" in stripped and "=" in stripped:
                area = float(stripped.split("=")[1])
            continue
        if not stripped:
            continue
        rows.append([float(value) for value in stripped.split()])
    table = np.asarray(rows, dtype=float)
    if area is None:
        raise ValueError(f"No '# area = ...' header found in {path}")
    return {
        "area": area,
        "zmin": table[:, 0],
        "zm": table[:, 1],
        "zmax": table[:, 2],
        "dndz": table[:, 3],
        "bias": table[:, 4],
        "path": str(path),
    }


def _shell_volume_per_sqdeg(cosmo, z_lo, z_hi):
    """Comoving shell volume per square degree between ``z_lo`` and ``z_hi``.

    Transcribed from ``bckpcosmicfishpie/LSSsurvey/spectro_obs.py``
    (``SpectroCov.volume_bin``): a spherical shell divided by ``4 pi (180/pi)^2``.
    """
    d_lo = cosmo.angdist(z_lo)
    d_hi = cosmo.angdist(z_hi)
    sphere = (4 * np.pi / 3) * (((1 + z_hi) * d_hi) ** 3 - ((1 + z_lo) * d_lo) ** 3)
    return sphere / (4 * np.pi * (180 / np.pi) ** 2)


def reference_n_density(table: dict, cosmo) -> np.ndarray:
    """Comoving number density per bin, in Mpc^-3.

    Transcribed from ``SpectroCov.n_density``: ``dn3 * dz / d_volume`` with
    ``d_volume`` in Mpc^3 per deg^2.
    """
    dz = table["zmax"] - table["zmin"]
    d_volume = np.array(
        [
            _shell_volume_per_sqdeg(cosmo, z_lo, z_hi)
            for z_lo, z_hi in zip(table["zmin"], table["zmax"])
        ]
    )
    return table["dndz"] * dz / d_volume


def reference_volume_survey(table: dict, cosmo) -> np.ndarray:
    """Survey volume per bin, in Mpc^3.

    Transcribed from ``SpectroCov.volume_survey``: ``area_survey * d_volume`` with the
    area in deg^2 and ``d_volume`` in Mpc^3 per deg^2.
    """
    d_volume = np.array(
        [
            _shell_volume_per_sqdeg(cosmo, z_lo, z_hi)
            for z_lo, z_hi in zip(table["zmin"], table["zmax"])
        ]
    )
    return table["area"] * d_volume


def reference_theta_moments(z, k_grid, cosmo, moment: int = 0):
    """Velocity-divergence moment ``(1 / 6 pi^2) int P(k) f(k)^moment dk``.

    Transcribed from ``ComputeGalSpectro.P_ThetaTheta_Moments``. ``k_grid`` is in
    1/Mpc, ``cosmo.matpow`` returns Mpc^3.
    """
    ff = np.asarray(cosmo.f_growthrate(z, k_grid)) ** moment
    pp = np.asarray(cosmo.matpow(z, k_grid))
    return np.trapezoid(pp * ff, x=k_grid) / (6 * np.pi**2)


def reference_sigma_p(z, k_grid, cosmo) -> float:
    """Pairwise velocity dispersion entering the Lorentzian FoG."""
    return float(np.sqrt(reference_theta_moments(z, k_grid, cosmo, moment=2)))


def reference_sigma_v(z, mu, k_grid, cosmo) -> np.ndarray:
    """Displacement variance entering the de-wiggling weight."""
    f0 = reference_theta_moments(z, k_grid, cosmo, moment=0)
    f1 = reference_theta_moments(z, k_grid, cosmo, moment=1)
    f2 = reference_theta_moments(z, k_grid, cosmo, moment=2)
    return np.sqrt(f0 + 2 * mu**2 * f1 + mu**2 * f2)


def reference_ap_factors(z, cosmo, fiducial_cosmo):
    """Return ``(q_parallel, q_perpendicular, bao)``.

    Transcribed from ``ComputeGalSpectro.qparallel``, ``qperpendicular`` and
    ``BAO_term``: ``q_par = H_fid / H``, ``q_perp = D_A / D_A,fid`` and
    ``bao = 1 / (q_perp^2 q_par)``.
    """
    q_par = fiducial_cosmo.Hubble(z) / cosmo.Hubble(z)
    q_perp = cosmo.angdist(z) / fiducial_cosmo.angdist(z)
    return q_par, q_perp, 1.0 / (q_perp**2 * q_par)


def reference_pgg(
    z,
    k,
    mu,
    *,
    cosmo,
    fiducial_cosmo,
    bias,
    sigma_p,
    sigma_v,
    dz_err,
    k_grid=None,
    dz_type="constant",
    sigma8_norm=True,
):
    """Observed galaxy power spectrum following the paper recipe (Eqs. 11-18).

    Parameters
    ----------
    z : float
        Redshift.
    k, mu : numpy.ndarray
        Observed wavenumber (1/Mpc) and cosine, on the survey grid.
    cosmo, fiducial_cosmo : cosmicjellyfish cosmology objects
        Sample and fiducial cosmology used for the AP rescaling.
    bias : float
        Linear galaxy bias at ``z`` (fiducial value).
    sigma_p, sigma_v : float or numpy.ndarray
        Pairwise velocity dispersion and displacement variance. Pass ``0`` to switch
        the FoG and de-wiggling off.
    dz_err : float
        Spectroscopic redshift error (``spec_sigma_dz``).
    k_grid : numpy.ndarray, optional
        1/Mpc grid used for the velocity moments. Defaults to
        ``logspace(-3, log10(5), 1024)``, matching ``set_internal_kgrid``.
    dz_type : str
        ``constant`` or ``z-dependent``, matching ``spec_err_z``.
    sigma8_norm : bool
        If True (paper/IST:F recipe) the Kaiser term uses ``b sigma8`` and
        ``f sigma8`` and the power spectrum is divided by ``sigma8^2``.
    """
    if k_grid is None:
        k_grid = np.logspace(-3, np.log10(5), 1024)

    q_par, q_perp, bao = reference_ap_factors(z, cosmo, fiducial_cosmo)
    k_par = k * mu / q_par
    k_perp = k * np.sqrt(1 - mu**2) / q_perp
    k_ap = np.sqrt(k_par**2 + k_perp**2)
    mu_ap = k_par / k_ap

    if dz_type == "z-dependent":
        dz = dz_err * (1 + z)
    else:
        dz = dz_err
    err = np.exp(-0.5 * (dz / cosmo.Hubble(z) * k_par) ** 2)

    s8 = cosmo.sigma8_of_z(z)
    f = cosmo.f_growthrate(z, k_ap)
    if sigma8_norm:
        # Kaiser term in the (b sigma8 + f sigma8 mu^2) form; the sigma8^2 factor is
        # cancelled by dividing the power spectrum by sigma8^2 below.
        kaiser = (bias * s8 + f * s8 * mu_ap**2) ** 2
        norm = s8**2
    else:
        kaiser = (bias + f * mu_ap**2) ** 2
        norm = 1.0

    p_dd = np.asarray(cosmo.matpow(z, k_ap)) / norm
    if sigma_p == 0 and sigma_v == 0:
        p_dw = p_dd
        fog = np.ones_like(k_ap)
    else:
        if np.ndim(sigma_v) == 0 and sigma_v == 0:
            gmu = np.zeros_like(mu_ap)
        else:
            gmu = np.asarray(sigma_v) ** 2
        p_nw = np.asarray(cosmo.nonwiggle_pow(z, k_ap)) / norm
        p_dw = p_dd * np.exp(-gmu * k_ap**2) + p_nw * (1 - np.exp(-gmu * k_ap**2))
        fog = 1.0 / (1.0 + (k_ap * mu_ap * sigma_p) ** 2)

    return bao * kaiser * p_dw * fog * err**2


def reference_omega_hi(z):
    """HI density fraction ``Omega_HI(z) = 4e-4 (1+z)^0.6`` (paper Eq. 20)."""
    return 4 * np.power(1 + z, 0.6) * 1e-4


def reference_b_hi(z):
    """HI bias ``b_HI(z) = 0.3 (1+z) + 0.6`` (paper Eq. 21)."""
    return 0.3 * (1 + z) + 0.6


def reference_temperature(z, cosmo):
    """Mean HI brightness temperature in mK (paper Eq. 19)."""
    h = cosmo.cosmopars["h"]
    h0 = cosmo.Hubble(0.0)
    return 189 * h * (1 + z) ** 2 * (h0 / cosmo.Hubble(z)) * reference_omega_hi(z)


def reference_theta_b(z, dish_diameter):
    """Beam size in radians, ``1.22 lambda_21 (1+z) / D_dish``."""
    lambda_21 = 21 / 100
    return 1.22 * lambda_21 * (1 + z) / dish_diameter


def reference_beta_beam(z, k, mu, cosmo, dish_diameter):
    """Beam damping factor, ``exp[-k^2 (1-mu^2) chi^2 theta_b^2 / (16 ln 2)]``."""
    expo = k**2 * (1 - mu**2) * cosmo.comoving(z) ** 2 * reference_theta_b(z, dish_diameter) ** 2
    bet = np.exp(-expo / (16.0 * np.log(2.0)))
    return np.maximum(bet, 1e-12)


def reference_p_noise_21(
    z,
    k,
    mu,
    *,
    cosmo,
    tsys,
    fsky,
    t_tot,
    n_dish,
    dish_diameter,
    beam_term=False,
):
    """HI thermal noise power in mK^2 Mpc^3 (paper Eq. 27).

    Parameters
    ----------
    tsys : float
        System temperature in mK.
    fsky : float
        Sky fraction.
    t_tot : float
        Total observing time in seconds.
    n_dish : int
        Number of dishes.
    """
    f_21 = 299792.458 * 1000 / (21 / 100)  # Hz, c in km/s -> m/s, lambda in m
    pref = 2 * np.pi * fsky / (f_21 * t_tot)
    geometric = (1 + z) ** 2 * cosmo.comoving(z) ** 2 / cosmo.Hubble(z)
    beta = reference_beta_beam(z, k, mu, cosmo, dish_diameter) if beam_term else np.ones_like(k)
    return pref * geometric * tsys**2 * (1.0 / n_dish) / beta**2

#!/usr/bin/env python
"""Validate DESI, Rubin and SKAO survey observables against the historical recipe.

This is the Phase 2 harness of ``docs/SURVEY_VALIDATION_ROADMAP.md``. Before trusting any
Fisher number for a newly migrated survey we check that the package reproduces the
individual observables of the historical ``cosmicfish_reloaded_skaproject`` checkout:

* galaxy clustering: bin number density, survey volume, fiducial bias and
  ``P_gg(k, mu, z)``;
* intensity mapping: ``Omega_HI``, ``b_HI``, the mean brightness temperature, the beam and
  the thermal noise power, plus ``P_II`` and ``P_Ig``;
* photometric surveys: the redshift distribution ``dN/dz`` and the per-bin galaxy counts;
* the SKAO Fig. 1 spectra at ``z = 0.6``, compared in shape and in amplitude against the
  historical ``data-for-fig1.dat`` (GR vs the modified-gravity fiducial used back then).

The reference formulas live in :mod:`survey_observable_reference` and are transcribed
from the historical source, so a comparison isolates the observable algebra rather than
the Boltzmann solver.

Usage
-----
::

    uv run python scripts/validation/validate_survey_observables.py
    uv run python scripts/validation/validate_survey_observables.py --survey desi-bgs
    uv run python scripts/validation/validate_survey_observables.py --list

The historical checkout is only read. Point ``COSMICFISH_HISTORICAL_DIR`` at it if it
lives somewhere other than the default path.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from survey_observable_reference import (  # noqa: E402
    historical_project_dir,
    load_spectro_table,
    reference_b_hi,
    reference_beta_beam,
    reference_n_density,
    reference_omega_hi,
    reference_p_noise_21,
    reference_pgg,
    reference_sigma_p,
    reference_sigma_v,
    reference_temperature,
    reference_theta_b,
    reference_volume_survey,
)

from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix  # noqa: E402
from cosmicjellyfish.LSSsurvey.photo_window import GalaxyPhotoDist  # noqa: E402
from cosmicjellyfish.LSSsurvey.spectro_cov import SpectroCov  # noqa: E402
from cosmicjellyfish.LSSsurvey.spectro_obs import ComputeGalSpectro  # noqa: E402

FIDUCIAL = {
    "Omegam": 0.32,
    "Omegab": 0.05,
    "h": 0.67,
    "ns": 0.96,
    "sigma8": 0.822,
}
BASE_OPTIONS = {
    "code": "symbolic",
    "nonlinear": True,
    "feedback": 0,
    "cosmo_model": "LCDM",
}

K_GRID = np.linspace(0.005, 0.10, 9)  # 1/Mpc
MU_GRID = np.array([0.0, 0.5, 1.0])


@dataclass(frozen=True)
class SurveyCase:
    """One survey configuration to validate."""

    name: str
    survey: str
    observables: tuple[str, ...]
    kind: str
    reference_table: str | None = None
    options: dict = field(default_factory=dict)


CASES: dict[str, SurveyCase] = {
    "desi-bgs": SurveyCase(
        name="desi-bgs",
        survey="DESI",
        observables=("GCsp",),
        kind="gcsp",
        reference_table="DESI_BGS_GCsp.dat",
        options={"survey_name_spectro": "DESI-BGS-SKAOPaper"},
    ),
    "desi-elg": SurveyCase(
        name="desi-elg",
        survey="DESI",
        observables=("GCsp",),
        kind="gcsp",
        reference_table="DESI_ELG_GCsp.dat",
        options={"survey_name_spectro": "DESI-ELG-SKAOPaper"},
    ),
    "skao-hi": SurveyCase(
        name="skao-hi",
        survey="SKAO",
        observables=("GCsp",),
        kind="gcsp",
        reference_table="SKA1_GCsp_MDB2_Redbook.dat",
        options={"survey_name_spectro": "SKAO-Spectroscopic-SKAOPaper"},
    ),
    "skao-im": SurveyCase(
        name="skao-im",
        survey="SKAO",
        observables=("IM",),
        kind="im",
    ),
    "skao-im-desi": SurveyCase(
        name="skao-im-desi",
        survey="SKAO",
        observables=("GCspxIM",),
        kind="im-cross",
        reference_table="DESI_ELG_GCsp.dat",
        options={
            "survey_name_spectro": "DESI-ELG-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
    ),
    "rubin-photo": SurveyCase(
        name="rubin-photo",
        survey="Rubin",
        observables=("GCph", "WL"),
        kind="photo",
        options={"survey_name_photo": "Rubin-Photometric-SKAOPaper"},
    ),
    "skao-photo": SurveyCase(
        name="skao-photo",
        survey="SKAO",
        observables=("GCph", "WL"),
        kind="photo",
        options={"survey_name_photo": "SKAO-Photometric-SKAOPaper"},
    ),
    "fig1": SurveyCase(
        name="fig1",
        survey="SKAO",
        observables=("GCspxIM",),
        kind="fig1",
        options={
            "survey_name_spectro": "SKAO-Spectroscopic-SKAOPaper",
            "survey_name_radio_IM": "SKAO-IM-Redbook-DESI-ELG",
        },
    ),
}


def build_configuration(case: SurveyCase, results_dir: Path) -> FisherMatrix:
    """Build a ``FisherMatrix`` that owns the settings, specs and fiducial cosmology."""
    options = dict(BASE_OPTIONS)
    options["results_dir"] = str(results_dir)
    options["outroot"] = f"validate_{case.name.replace('-', '_')}"
    options.update(case.options)
    return FisherMatrix(
        options=options,
        observables=list(case.observables),
        freepars={"Omegam": 0.01},
        fiducialpars=dict(FIDUCIAL),
        surveyName=case.survey,
        cosmoModel="LCDM",
    )


def _relative_difference(current, reference) -> float:
    """Max relative difference, guarded against a vanishing reference."""
    current = np.atleast_1d(np.asarray(current, dtype=float))
    reference = np.atleast_1d(np.asarray(reference, dtype=float))
    scale = np.maximum(np.abs(reference), 1e-300)
    return float(np.max(np.abs(current - reference) / scale))


def _worst_difference(differences) -> float:
    """Largest of several differences; NaN if any is not finite.

    The built-in ``max`` ignores a NaN that follows a smaller value, so ``[0.0, nan]`` would
    give ``0.0`` and the row would be recorded as agreeing.
    """
    values = np.asarray(differences, dtype=float)
    if not np.all(np.isfinite(values)):
        return float("nan")
    return float(np.max(values))


def _row(survey, observable, quantity, difference, note="", status=None) -> dict:
    tolerance = 1e-9
    if status is None:
        status = "ok" if np.isfinite(difference) and difference <= tolerance else "check"
    return {
        "survey": survey,
        "observable": observable,
        "quantity": quantity,
        "max_relative_difference": difference,
        "status": status,
        "note": note,
    }


def validate_gcsp(case: SurveyCase, fisher: FisherMatrix, results_dir: Path) -> list[dict]:
    """Validate number density, volume, bias and ``P_gg`` for a GCsp survey."""
    rows: list[dict] = []
    table = load_spectro_table(case.reference_table)
    spec_obs = ComputeGalSpectro(
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
        fiducial_specobs=spec_obs,
        bias_samples=["g", "g"],
        configuration=fisher,
    )
    cosmo = fisher.fiducialcosmo

    z_mids = np.asarray(cov.inter_z_bin_mids)
    n_current = np.array([cov.n_density(zi) for zi in z_mids])
    n_reference = reference_n_density(table, cosmo)
    rows.append(
        _row(
            case.name,
            "GCsp",
            "n_density [Mpc^-3]",
            _relative_difference(n_current, n_reference),
        )
    )

    volume_current = np.array([cov.volume_survey(i) for i in range(len(z_mids))])
    volume_reference = reference_volume_survey(table, cosmo)
    rows.append(
        _row(
            case.name,
            "GCsp",
            "volume_survey [Mpc^3]",
            _relative_difference(volume_current, volume_reference),
        )
    )

    bias_current = np.array([spec_obs.nuisance.gcsp_bias_at_zi(i + 1) for i in range(len(z_mids))])
    rows.append(
        _row(
            case.name,
            "GCsp",
            "fiducial bias",
            _relative_difference(bias_current, table["bias"]),
        )
    )

    k_grid_moments = spec_obs.k_grid
    differences = []
    for z in z_mids:
        sigma_p = reference_sigma_p(z, k_grid_moments, cosmo)
        mu_mesh = MU_GRID[:, None] * np.ones_like(K_GRID)
        k_mesh = np.ones((MU_GRID.size, 1)) * K_GRID
        current = spec_obs.observed_Pgg(
            z,
            k_mesh,
            mu_mesh,
            b_i=float(spec_obs.nuisance.gcsp_bias_at_z(z)),
        )
        reference = np.empty_like(current)
        for i, mu in enumerate(MU_GRID):
            reference[i] = reference_pgg(
                z,
                K_GRID,
                mu,
                cosmo=cosmo,
                fiducial_cosmo=cosmo,
                bias=float(spec_obs.nuisance.gcsp_bias_at_z(z)),
                sigma_p=sigma_p,
                sigma_v=reference_sigma_v(z, mu, k_grid_moments, cosmo),
                dz_err=fisher.specs["spec_sigma_dz"],
                k_grid=k_grid_moments,
            )
        differences.append(_relative_difference(current, reference))
    rows.append(
        _row(
            case.name,
            "GCsp",
            "P_gg(k, mu, z)",
            _worst_difference(differences),
            "s8-normalised paper form",
        )
    )
    return rows


def validate_im(case: SurveyCase, fisher: FisherMatrix, results_dir: Path) -> list[dict]:
    """Validate the intensity-mapping thermodynamical and noise quantities."""
    rows: list[dict] = []
    spec_obs = ComputeGalSpectro(
        cosmopars=fisher.fiducialcosmopars,
        fiducial_cosmopars=fisher.fiducialcosmopars,
        spectrobiaspars=fisher.Spectrobiaspars,
        spectrononlinearpars=fisher.Spectrononlinpars,
        IMbiaspars=fisher.IMbiaspars,
        PShotpars=fisher.PShotpars,
        bias_samples=["I", "I"],
        configuration=fisher,
    )
    cov = SpectroCov(
        fisher.fiducialcosmopars,
        fiducial_specobs=spec_obs,
        bias_samples=["I", "I"],
        configuration=fisher,
    )
    cosmo = fisher.fiducialcosmo
    z_test = float(np.mean(spec_obs.nuisance.IM_zbins_mids))
    dish = fisher.specs["D_dish"]
    mu_mesh = MU_GRID[:, None] * np.ones_like(K_GRID)
    k_mesh = np.ones((MU_GRID.size, 1)) * K_GRID

    rows.append(
        _row(
            case.name,
            "IM",
            "Omega_HI(z)",
            _relative_difference(spec_obs.Omega_HI(z_test), reference_omega_hi(z_test)),
        )
    )
    rows.append(
        _row(
            case.name,
            "IM",
            "b_HI(z)",
            _relative_difference(spec_obs.nuisance.IM_bias_at_z(z_test), reference_b_hi(z_test)),
        )
    )
    rows.append(
        _row(
            case.name,
            "IM",
            "Tbar_b(z) [mK]",
            _relative_difference(
                spec_obs.Temperature(z_test), reference_temperature(z_test, cosmo)
            ),
        )
    )
    rows.append(
        _row(
            case.name,
            "IM",
            "theta_b(z) [rad]",
            _relative_difference(spec_obs.theta_b(z_test), reference_theta_b(z_test, dish)),
        )
    )
    beta_current = spec_obs.beta_SD(z_test, k_mesh, mu_mesh)
    beta_reference = reference_beta_beam(z_test, k_mesh, mu_mesh, cosmo, dish)
    rows.append(
        _row(
            case.name, "IM", "beam beta(k, mu)", _relative_difference(beta_current, beta_reference)
        )
    )

    tsys = cov.Tsys_func(z_test)
    noise_current = cov.P_noise_21(z_test, k_mesh, mu_mesh, temp_dim=True)
    noise_reference = reference_p_noise_21(
        z_test,
        k_mesh,
        mu_mesh,
        cosmo=cosmo,
        tsys=tsys,
        fsky=spec_obs.fsky_IM,
        t_tot=spec_obs.t_tot,
        n_dish=spec_obs.N_d,
        dish_diameter=dish,
    )
    rows.append(
        _row(case.name, "IM", "P_noise_21", _relative_difference(noise_current, noise_reference))
    )

    # HI auto-power against the paper form.
    sigma_p = reference_sigma_p(z_test, spec_obs.k_grid, cosmo)
    b_hi = float(spec_obs.nuisance.IM_bias_at_z(z_test))
    temperature = spec_obs.Temperature(z_test)
    p_ii_current = spec_obs.observed_P_ij(z_test, k_mesh, mu_mesh, si="I", sj="I")
    p_ii_reference = np.empty_like(p_ii_current)
    for i, mu in enumerate(MU_GRID):
        base = reference_pgg(
            z_test,
            K_GRID,
            mu,
            cosmo=cosmo,
            fiducial_cosmo=cosmo,
            bias=b_hi,
            sigma_p=sigma_p,
            sigma_v=reference_sigma_v(z_test, mu, spec_obs.k_grid, cosmo),
            # The spectroscopic redshift error only suppresses the galaxy leg.
            dz_err=0.0,
            k_grid=spec_obs.k_grid,
            sigma8_norm=False,
        )
        p_ii_reference[i] = temperature**2 * base * beta_reference[i] ** 2
    rows.append(
        _row(case.name, "IM", "P_II(k, mu, z)", _relative_difference(p_ii_current, p_ii_reference))
    )
    return rows


def validate_im_cross(case: SurveyCase, fisher: FisherMatrix, results_dir: Path) -> list[dict]:
    """Validate the IM x galaxy cross-spectrum on the DESI-ELG aligned bins."""
    rows = validate_im(case, fisher, results_dir)
    spec_obs = ComputeGalSpectro(
        cosmopars=fisher.fiducialcosmopars,
        fiducial_cosmopars=fisher.fiducialcosmopars,
        spectrobiaspars=fisher.Spectrobiaspars,
        spectrononlinearpars=fisher.Spectrononlinpars,
        IMbiaspars=fisher.IMbiaspars,
        PShotpars=fisher.PShotpars,
        bias_samples=["I", "g"],
        configuration=fisher,
    )
    cosmo = fisher.fiducialcosmo
    z_test = float(np.mean(spec_obs.nuisance.IM_zbins_mids))
    mu_mesh = MU_GRID[:, None] * np.ones_like(K_GRID)
    k_mesh = np.ones((MU_GRID.size, 1)) * K_GRID
    b_g = float(spec_obs.nuisance.gcsp_bias_at_z(z_test))
    b_hi = float(spec_obs.nuisance.IM_bias_at_z(z_test))
    temperature = spec_obs.Temperature(z_test)
    sigma_p = reference_sigma_p(z_test, spec_obs.k_grid, cosmo)
    p_ig_current = spec_obs.observed_P_ij(z_test, k_mesh, mu_mesh, si="I", sj="g")
    p_ig_reference = np.empty_like(p_ig_current)
    for i, mu in enumerate(MU_GRID):
        common = reference_pgg(
            z_test,
            K_GRID,
            mu,
            cosmo=cosmo,
            fiducial_cosmo=cosmo,
            bias=1.0,
            sigma_p=sigma_p,
            sigma_v=reference_sigma_v(z_test, mu, spec_obs.k_grid, cosmo),
            # Applied once below, on the galaxy leg only.
            dz_err=0.0,
            k_grid=spec_obs.k_grid,
            sigma8_norm=False,
        )
        kaiser_g = b_g + cosmo.f_growthrate(z_test, K_GRID) * mu**2
        kaiser_i = b_hi + cosmo.f_growthrate(z_test, K_GRID) * mu**2
        beta = reference_beta_beam(z_test, K_GRID, mu, cosmo, fisher.specs["D_dish"])
        err = np.exp(
            -0.5 * (fisher.specs["spec_sigma_dz"] / cosmo.Hubble(z_test) * K_GRID * mu) ** 2
        )
        # ``common`` already carries (b=1 + f mu^2)^2; split it into the two legs.
        p_ig_reference[i] = (
            (
                temperature
                * common
                * kaiser_g
                * kaiser_i
                / (1.0 + cosmo.f_growthrate(z_test, K_GRID) * mu**2) ** 2
            )
            * beta
            * err
        )
    rows.append(
        _row(
            case.name,
            "IM x GCsp",
            "P_Ig(k, mu, z)",
            _relative_difference(p_ig_current, p_ig_reference),
        )
    )
    return rows


def diagnose_fig1(case: SurveyCase, fisher: FisherMatrix, results_dir: Path) -> list[dict]:
    """Reproduce the historical SKAO figure-1 spectra at ``z = 0.6``.

    The reference ``data-for-fig1.dat`` file was produced by the historical project at a
    modified-gravity fiducial (``E11 = 0.1007``, ``E22 = 0.8293``) using the external
    MGCAMB tables, while this run is GR. We therefore separate two questions:

    * *amplitude*: the median ratio reference/current over the reliable k window. A few
      percent offset is the expected modified-gravity growth enhancement and is reported,
      not failed.
    * *shape*: the scatter of that ratio around its median. The two recipes use the same
      AP, Kaiser, de-wiggling, FoG and beam algebra, so after removing the amplitude offset
      the shapes must agree.

    The very low-k part of the historical file is dominated by the extrapolation of the
    external power table, and above ``k ~ 0.05`` 1/Mpc the exponential FoG/beam damping
    amplifies the modified-gravity difference in the velocity moments. The shape check is
    therefore restricted to ``0.005 <= k <= 0.05`` 1/Mpc and uses a robust p10-p90 spread of
    the reference/current ratio instead of an extreme value.
    """
    rows: list[dict] = []
    reference = np.loadtxt(historical_project_dir() / "data-for-fig1.dat")
    k = reference[:, 0]
    z = 0.6

    spec_obs = ComputeGalSpectro(
        cosmopars=fisher.fiducialcosmopars,
        fiducial_cosmopars=fisher.fiducialcosmopars,
        spectrobiaspars=fisher.Spectrobiaspars,
        spectrononlinearpars=fisher.Spectrononlinpars,
        IMbiaspars=fisher.IMbiaspars,
        PShotpars=fisher.PShotpars,
        bias_samples=["I", "g"],
        configuration=fisher,
    )
    cov = SpectroCov(
        fisher.fiducialcosmopars,
        fiducial_specobs=spec_obs,
        bias_samples=["I", "g"],
        configuration=fisher,
    )
    window = (k >= 0.005) & (k <= 0.05)
    k_window = k[window]

    spectra = {
        "P_gg(k, mu=0)": ("gg", 0.0, 1),
        "P_gg(k, mu=1)": ("gg", 1.0, 2),
        "P_II(k, mu=0)": ("II", 0.0, 3),
        "P_II(k, mu=1)": ("II", 1.0, 4),
        "P_Ig(k, mu=0)": ("Ig", 0.0, 5),
        "P_Ig(k, mu=1)": ("Ig", 1.0, 6),
    }
    current = {}
    for label, (leg, mu, column) in spectra.items():
        if leg == "gg":
            values = spec_obs.observed_Pgg(
                z,
                k_window,
                np.full_like(k_window, mu),
                b_i=float(spec_obs.nuisance.gcsp_bias_at_z(z)),
            )
        else:
            values = spec_obs.observed_P_ij(
                z, k_window, np.full_like(k_window, mu), si="I", sj=("I" if leg == "II" else "g")
            )
        current[label] = values
        ratio = reference[window, column] / values
        median = float(np.median(ratio))
        p10, p90 = np.percentile(ratio, [10, 90])
        shape = float((p90 - p10) / median)
        rows.append(
            _row(
                case.name,
                "SKAO Fig. 1",
                f"{label} amplitude (ref/current)",
                abs(median - 1.0),
                note=f"median ratio {median:.4f}; MG fiducial in reference",
                status="expected",
            )
        )
        rows.append(
            _row(
                case.name,
                "SKAO Fig. 1",
                f"{label} shape residual",
                shape,
                note="p10-p90 spread around the median, 0.005 <= k <= 0.05 1/Mpc",
                status="ok" if shape <= 0.02 else "check",
            )
        )

    rows.append(
        _row(
            case.name,
            "SKAO Fig. 1",
            "Tbar_b(z=0.6) [mK]",
            _relative_difference(spec_obs.Temperature(z), reference[0, 7]),
            note="depends on H(z); MG background in reference",
            status="expected",
        )
    )
    noise_current = cov.P_noise_21(z, k_window, np.full_like(k_window, 0.0), temp_dim=False)
    rows.append(
        _row(
            case.name,
            "SKAO Fig. 1",
            "P_noise_21(k)/Tbar_b^2 [Mpc^3]",  # temp_dim=False: normalised by Tbar_b(z)^2
            _relative_difference(noise_current, reference[window, 8]),
            note="depends on H(z); MG background in reference",
            status="expected",
        )
    )

    diagnostic = {
        "z": z,
        "k": k.tolist(),
        "reference": {
            key: reference[:, column].tolist() for key, (_, _, column) in spectra.items()
        },
        "current": {key: current[key].tolist() for key in current},
        "k_window": k_window.tolist(),
    }
    path = results_dir / "fig1_diagnostic.json"
    path.write_text(json.dumps(diagnostic, indent=2))
    print(f"Wrote {path}")

    return rows


def validate_photo(case: SurveyCase, fisher: FisherMatrix, results_dir: Path) -> list[dict]:
    """Validate the photometric redshift distribution and bin populations."""
    rows: list[dict] = []
    window = GalaxyPhotoDist(fisher.photopars, specifications=fisher.specs)
    z = np.linspace(window.z_min + 1e-3, window.z_max, 500)

    analytic = (z / window.z0_p) ** 2 * np.exp(-((z / window.z0) ** window.ngamma))
    rows.append(
        _row(case.name, "Photo", "dN/dz shape", _relative_difference(window.dNdz(z), analytic))
    )

    for obs in ("GCph", "WL"):
        counts = np.asarray(fisher.specs[f"ngalbin_{obs}"], dtype=float)
        # Historical ``ngal_per_bin``: (ngal/arcmin^2 * 3600 / n_bins) * deg^2 per sr.
        ngal_sqdeg = fisher.specs[f"ngal_sqarmin_{obs}"] * 3600
        expected = (ngal_sqdeg / len(counts)) * (180 / np.pi) ** 2
        rows.append(
            _row(
                case.name,
                f"Photo {obs}",
                "galaxies per bin",
                _relative_difference(counts, np.full_like(counts, expected)),
            )
        )
    return rows


VALIDATORS = {
    "gcsp": validate_gcsp,
    "im": validate_im,
    "im-cross": validate_im_cross,
    "photo": validate_photo,
    "fig1": diagnose_fig1,
}


def run_case(case: SurveyCase, results_dir: Path) -> list[dict]:
    """Run the appropriate validator for ``case``."""
    fisher = build_configuration(case, results_dir)
    return VALIDATORS[case.kind](case, fisher, results_dir)


def format_table(rows: list[dict]) -> str:
    """Render the results as a fixed-width console table."""
    header = f"{'survey':<14} {'observable':<14} {'quantity':<24} {'max rel. diff':>16}  status"
    lines = [header, "-" * len(header)]
    for row in rows:
        lines.append(
            f"{row['survey']:<14} {row['observable']:<14} {row['quantity']:<24} "
            f"{row['max_relative_difference']:>16.3e}  {row['status']}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--survey",
        action="append",
        choices=sorted(CASES),
        help="Case to validate (repeatable). Defaults to all.",
    )
    parser.add_argument("--list", action="store_true", help="List the available cases and exit.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "results" / "survey_validation",
        help="Directory for the JSON report.",
    )
    args = parser.parse_args(argv)

    if args.list:
        for name, case in CASES.items():
            print(f"{name:<14} survey={case.survey:<7} kind={case.kind:<9} obs={case.observables}")
        return 0

    selected = args.survey or list(CASES)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for name in selected:
        case = CASES[name]
        print(f"Validating {name} ({case.survey}, {case.kind}) ...")
        rows.extend(run_case(case, args.output_dir))

    print()
    print(format_table(rows))

    report = args.output_dir / "observable_validation.json"
    report.write_text(json.dumps({"fiducial": FIDUCIAL, "rows": rows}, indent=2))
    print(f"\nWrote {report}")

    failures = [row for row in rows if row["status"] == "check"]
    if failures:
        print(f"\n{len(failures)} observable(s) need attention.")
        return 1
    print("\nAll observables agree with the historical recipe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

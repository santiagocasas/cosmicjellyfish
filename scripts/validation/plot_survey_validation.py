#!/usr/bin/env python
"""Build the figures of the survey-validation study.

The script only reads the JSON reports produced by
``scripts/validation/validate_survey_observables.py`` and
``scripts/validation/run_survey_forecasts.py``; it never runs a forecast itself. Run the
two producers first, then::

    uv run python scripts/validation/plot_survey_validation.py

The figures are written to ``docs/source/_static/survey_validation/`` so that the
documentation page can embed them. Pass ``--output-dir`` to write them elsewhere.

Figures
-------
``survey_inputs.png``
    Number density per redshift bin for the spectroscopic and intensity-mapping
    configurations, and the analytic photometric ``dN/dz`` of the three imaging surveys.
``forecast_errors.png``
    Marginalised 1-sigma errors on the shared cosmological parameters, LCDM and w0waCDM.
``w0wa_comparisons.png``
    Four small ``w0``-``wa`` Fisher-ellipse panels, each holding two comparable probes.
    The Planck-like case is deliberately absent: its single-channel approximation is far
    weaker than every LSS probe and would set the axis scale for all of them.
``fig1_diagnostic.png``
    Historical-versus-current SKAO Fig. 1 spectra, shown as a ratio to make the residual
    shape agreement visible. The amplitude offset is not attributed to a single cause:
    the reference used a modified-gravity fiducial, a different backend and extrapolated
    tables.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.patches import Ellipse

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_DIRECTORIES = (
    REPO_ROOT / "cosmicjellyfish/configs/other_survey_specifications",
    REPO_ROOT / "cosmicjellyfish/configs/default_survey_specifications",
)
SPECTRO_INPUTS = (
    ("DESI-BGS-SKAOPaper.yaml", "DESI BGS", "#1f77b4"),
    ("DESI-ELG-SKAOPaper.yaml", "DESI ELG", "#ff7f0e"),
    ("SKAO-Spectroscopic-SKAOPaper.yaml", "SKAO HI", "#2ca02c"),
)
PHOTO_INPUTS = (
    ("Euclid-Photometric-ISTF-Pessimistic.yaml", "Euclid", "#1f77b4"),
    ("Rubin-Photometric-SKAOPaper.yaml", "Rubin/LSST", "#ff7f0e"),
    ("SKAO-Photometric-SKAOPaper.yaml", "SKAO", "#2ca02c"),
)
# Each panel holds two probes of comparable constraining power. ``members`` are the
# result names summed to build that curve, so combinations reuse the stored Fisher blocks.
ELLIPSE_GROUPS = (
    (
        "Photometric",
        (
            (("euclid-photo",), "Euclid GCph+WL", "#1f77b4"),
            (("rubin-photo",), "Rubin/LSST GCph+WL", "#ff7f0e"),
        ),
    ),
    (
        "Spectroscopic",
        (
            (("euclid-spectro",), "Euclid GCsp", "#1f77b4"),
            (("desi-bgs", "desi-elg"), "DESI BGS+ELG", "#ff7f0e"),
        ),
    ),
    (
        "Photometry + spectroscopy",
        (
            (("euclid-photo", "euclid-spectro"), "Euclid GCph+WL+GCsp", "#1f77b4"),
            (("desi-bgs", "desi-elg", "rubin-photo"), "DESI BGS+ELG + Rubin/LSST", "#ff7f0e"),
        ),
    ),
    (
        "Intensity mapping vs clustering",
        (
            (("skao-im",), "SKAO IM", "#9467bd"),
            (("euclid-spectro",), "Euclid GCsp", "#2ca02c"),
        ),
    ),
)
PARAM_LABELS = {
    "Omegam": r"$\Omega_m$",
    "Omegab": r"$\Omega_b$",
    "h": r"$h$",
    "ns": r"$n_s$",
    "sigma8": r"$\sigma_8$",
    "w0": r"$w_0$",
    "wa": r"$w_a$",
}


def load_specification(name: str) -> dict:
    """Return the YAML dictionary of a shipped survey specification."""
    for directory in SPEC_DIRECTORIES:
        path = directory / name
        if path.exists():
            with path.open() as handle:
                content = yaml.safe_load(handle)
            return content.get("specifications", content)
    raise FileNotFoundError(f"Survey specification {name!r} not found")


def load_json(path: Path) -> dict:
    """Load one of the JSON reports, with a helpful error if it is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the producers first:\n"
            "  uv run python scripts/validation/validate_survey_observables.py\n"
            "  uv run python scripts/validation/run_survey_forecasts.py --model LCDM\n"
            "  uv run python scripts/validation/run_survey_forecasts.py --model w0waCDM"
        )
    with path.open() as handle:
        return json.load(handle)


def spectro_inputs(spec: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return bin centres and ``dN/dz`` per square degree of a spectroscopic spec."""
    buckets = spec["z_bins_sp"]
    edges = np.asarray([buckets[key] for key in sorted(buckets)], dtype=float)
    density = np.asarray(
        [spec["dndOmegadz"][key] for key in sorted(spec["dndOmegadz"])], dtype=float
    )
    return edges.mean(axis=1), density


def photo_inputs(spec: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return the analytic photometric ``dN/dz`` shape (normalised to unit area)."""
    edges = np.asarray(spec.get("z_bins_ph", spec.get("z_bins_GCph")), dtype=float)
    z = np.linspace(edges[0], edges[-1], 400)
    z0 = spec["zm"] / np.sqrt(2.0)
    shape = (z / z0) ** 2 * np.exp(-((z / z0) ** spec["ngamma"]))
    normalisation = np.trapezoid(shape, z)
    return z, shape / normalisation


def plot_survey_inputs(output_dir: Path) -> Path:
    """Plot the spectroscopic and photometric redshift distributions."""
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.5))

    for name, label, colour in SPECTRO_INPUTS:
        z, density = spectro_inputs(load_specification(name))
        left.plot(z, density, marker="o", label=label, color=colour)
    left.set_xlabel("redshift")
    left.set_ylabel(r"$dN/dz$ [deg$^{-2}$]")
    left.set_yscale("log")
    left.set_title("Spectroscopic galaxy number densities")
    left.legend()

    for name, label, colour in PHOTO_INPUTS:
        z, density = photo_inputs(load_specification(name))
        right.plot(z, density, label=label, color=colour)
    right.set_xlabel("redshift")
    right.set_ylabel(r"$dN/dz$ (normalised)")
    right.set_title("Photometric galaxies")
    right.legend()

    figure.tight_layout()
    path = output_dir / "survey_inputs.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_forecast_errors(results_dir: Path, output_dir: Path) -> Path:
    """Plot the marginalised errors of the two model runs as grouped bars."""
    reports = {
        model: load_json(results_dir / f"survey_forecasts_{model}.json")
        for model in ("LCDM", "w0waCDM")
    }
    figure, (left, right) = plt.subplots(1, 2, figsize=(13, 5.5))

    panels = (
        (left, "LCDM", ("Omegam", "sigma8")),
        (right, "w0waCDM", ("w0", "wa")),
    )
    for axis, model, parameters in panels:
        results = reports[model]["results"]
        labels = [result["label"] for result in results]
        positions = np.arange(len(labels))
        width = 0.8 / len(parameters)
        for index, parameter in enumerate(parameters):
            values = [result["sigma"][parameter] for result in results]
            axis.barh(
                positions + index * width - 0.4 + width / 2,
                values,
                height=width,
                label=PARAM_LABELS[parameter],
            )
        axis.set_yticks(positions)
        axis.set_yticklabels(labels, fontsize=8)
        axis.set_xscale("log")
        axis.set_xlabel(r"marginalised $1\sigma$")
        axis.set_title(model)
        axis.legend(fontsize=9)
        axis.grid(axis="x", alpha=0.3)

    figure.tight_layout()
    path = output_dir / "forecast_errors.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def _w0wa_covariance(report: dict, members: tuple[str, ...]) -> np.ndarray:
    """Return the two-parameter ``w0``-``wa`` covariance of one (summed) probe."""
    names = list(report["freepars"])
    results = {result["name"]: result for result in report["results"]}
    total = np.zeros((len(names), len(names)))
    for member in members:
        if member not in results:
            raise KeyError(
                f"forecast case {member!r} missing from the report; rerun "
                "run_survey_forecasts.py --model w0waCDM"
            )
        block = results[member].get("fisher_matrix")
        if block is None:
            raise ValueError(
                f"{member!r} has no stored Fisher block in the report; rerun "
                "run_survey_forecasts.py --model w0waCDM with the current script"
            )
        total = total + np.asarray(block, dtype=float)
    indices = [names.index(parameter) for parameter in ("w0", "wa")]
    # Marginalise over the other parameters: the 2x2 block of the *inverse* Fisher.
    # Inverting the 2x2 Fisher sub-block instead would give conditional errors.
    return np.linalg.inv(total)[np.ix_(indices, indices)]


def _draw_ellipse(axis, covariance: np.ndarray, colour: str, label: str) -> None:
    """Draw the 1-sigma (solid) and 2-sigma (dashed) ellipse at the fiducial point."""
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    angle = float(np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])))
    for scale, linestyle, alpha in ((2.0, "-", 1.0), (4.0, "--", 0.55)):
        axis.add_patch(
            Ellipse(
                (-1.0, 0.0),
                width=scale * float(np.sqrt(eigenvalues[0])),
                height=scale * float(np.sqrt(eigenvalues[1])),
                angle=angle,
                facecolor="none",
                edgecolor=colour,
                linestyle=linestyle,
                alpha=alpha,
                linewidth=1.8,
                label=label if scale == 2.0 else None,
            )
        )


def plot_w0wa_comparisons(results_dir: Path, output_dir: Path) -> Path:
    """Small multiples of comparable ``w0``-``wa`` constraints.

    Each panel holds two probes of similar constraining power, so the ellipses remain
    readable. The Planck-like run is excluded on purpose; see the module docstring.
    """
    report = load_json(results_dir / "survey_forecasts_w0waCDM.json")
    figure, axes = plt.subplots(2, 2, figsize=(11, 9))

    for axis, (title, curves) in zip(axes.ravel(), ELLIPSE_GROUPS):
        spans = {"w0": [], "wa": []}
        for members, label, colour in curves:
            covariance = _w0wa_covariance(report, members)
            _draw_ellipse(axis, covariance, colour, label)
            sigma = np.sqrt(np.diag(covariance))
            spans["w0"].append(2.0 * sigma[0])
            spans["wa"].append(2.0 * sigma[1])
        axis.axvline(-1.0, color="grey", linewidth=0.8)
        axis.axhline(0.0, color="grey", linewidth=0.8)
        for parameter, values in spans.items():
            centre = -1.0 if parameter == "w0" else 0.0
            radius = 1.15 * max(values)
            getattr(axis, "set_xlim" if parameter == "w0" else "set_ylim")(
                centre - radius, centre + radius
            )
        axis.set_xlabel(r"$w_0$")
        axis.set_ylabel(r"$w_a$")
        axis.set_title(title)
        axis.legend(fontsize=8, loc="best")
        axis.grid(alpha=0.2)

    figure.suptitle(r"$w_0w_a$CDM, marginalised $1\sigma$ (solid) and $2\sigma$ (dashed)")
    figure.tight_layout()
    path = output_dir / "w0wa_comparisons.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def plot_fig1(results_dir: Path, output_dir: Path) -> Path:
    """Plot the historical and current SKAO Fig. 1 spectra plus their ratio."""
    report = load_json(results_dir / "fig1_diagnostic.json")
    k = np.asarray(report["k"])
    window = np.asarray(report["k_window"])
    keys = ("P_gg(k, mu=0)", "P_II(k, mu=0)", "P_Ig(k, mu=0)", "P_gg(k, mu=1)")
    styles = ("-", "-.", ":", "--")
    window_index = np.searchsorted(k, window)

    figure, (left, right) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for key, style in zip(keys, styles):
        reference = np.asarray(report["reference"][key], dtype=float)
        current = np.asarray(report["current"][key], dtype=float)
        left.plot(k, reference, style, color="black", alpha=0.5)
        left.plot(window, current, marker="o", linestyle="none", markersize=3, label=key)
        right.plot(window, current / reference[window_index], style, marker="o", markersize=3)
    left.set_xscale("log")
    left.set_yscale("log")
    left.set_xlabel(r"$k$ [$1/\mathrm{Mpc}$]")
    left.set_ylabel(r"$P(k)$ [$(\mathrm{Mpc})^3$]")
    left.set_title("Historical (lines) and current (markers)")
    left.legend(fontsize=8)

    right.axhline(1.0, color="grey", linewidth=1)
    right.set_xscale("log")
    right.set_xlabel(r"$k$ [$1/\mathrm{Mpc}$]")
    right.set_ylabel("current / historical")
    right.set_title("Ratio in the amplitude window")

    figure.suptitle(r"SKAO Fig. 1 spectra at $z=0.6$ (GR rerun of an MG reference)", fontsize=11)
    figure.tight_layout()
    path = output_dir / "fig1_diagnostic.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results/survey_validation"),
        help="directory holding the JSON reports",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/source/_static/survey_validation"),
        help="where the PNG figures are written",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figures = [
        plot_survey_inputs(args.output_dir),
        plot_forecast_errors(args.results_dir, args.output_dir),
        plot_w0wa_comparisons(args.results_dir, args.output_dir),
        plot_fig1(args.results_dir, args.output_dir),
    ]
    for figure in figures:
        print(f"Wrote {figure}")


if __name__ == "__main__":
    main()

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
``desi2023_inputs.png``, ``desi2023_w0wa.png``
    Written only when the report holds the ``desi2023-*`` cases: densities and biases of
    the 2023 DESI tracers (Table 7 of arXiv:2306.06307) against the legacy BGS and ELG, and
    their ``w0``-``wa`` ellipses (single tracers with the quasars on top, a zoom without
    them, and the full set against the legacy DESI files and Euclid GCsp).
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
from matplotlib.colors import to_rgba
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


def _draw_ellipse(
    axis,
    covariance: np.ndarray,
    colour: str,
    label: str,
    fill_alpha: float = 0.0,
    zorder: int = 2,
) -> None:
    """Draw the 1-sigma (solid) and 2-sigma (dashed) ellipse at the fiducial point.

    ``fill_alpha > 0`` shades the 1-sigma ellipse, and ``zorder`` lets a curve sit on top.
    """
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
                facecolor=(
                    to_rgba(colour, fill_alpha) if (fill_alpha and scale == 2.0) else "none"
                ),
                edgecolor=to_rgba(colour, alpha),
                linestyle=linestyle,
                linewidth=1.8,
                zorder=zorder,
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


# --- DESI 2023 validation-paper specifications (arXiv:2306.06307, Table 7) -----------------
DESI2023_TRACERS = (
    ("DESI-BGS-Validation2023.yaml", "desi2023-bgs", "BGS", "#1f77b4"),
    ("DESI-LRG-Validation2023.yaml", "desi2023-lrg", "LRG", "#d62728"),
    ("DESI-ELG-Validation2023.yaml", "desi2023-elg", "ELG", "#2ca02c"),
    ("DESI-QSO-Validation2023.yaml", "desi2023-qso", "QSO", "#9467bd"),
)
DESI2023_COMBINED = tuple(case for _, case, _, _ in DESI2023_TRACERS)
DESI_LEGACY = (
    ("DESI-BGS-SKAOPaper.yaml", "BGS legacy", "#1f77b4"),
    ("DESI-ELG-SKAOPaper.yaml", "ELG legacy", "#2ca02c"),
)


def spectro_bias(spec: dict) -> np.ndarray:
    """Return the fiducial linear bias of each bin of a spectroscopic spec."""
    table = spec["sp_bias_parametrization"][spec["sp_bias_model"]]
    return np.asarray([table[f"bg_{i}"] for i in range(1, len(spec["z_bins_sp"]) + 1)])


def plot_desi2023_inputs(output_dir: Path) -> Path:
    """Densities and biases of the 2023 DESI tracers, with the legacy BGS and ELG for reference."""
    figure, (left, right) = plt.subplots(1, 2, figsize=(12, 4.5))
    for name, label, colour in DESI_LEGACY:
        spec = load_specification(name)
        z, density = spectro_inputs(spec)
        left.plot(z, density, linestyle="--", marker=".", color=colour, alpha=0.5, label=label)
        right.plot(z, spectro_bias(spec), linestyle="--", marker=".", color=colour, alpha=0.5)
    for name, _, label, colour in DESI2023_TRACERS:
        spec = load_specification(name)
        z, density = spectro_inputs(spec)
        left.plot(z, density, marker="o", color=colour, label=f"{label} 2023")
        right.plot(z, spectro_bias(spec), marker="o", color=colour, label=f"{label} 2023")
    left.set_yscale("log")
    left.set_xlabel("redshift")
    left.set_ylabel(r"$dN/dz$ [deg$^{-2}$]")
    left.set_title("Number density (Table 7)")
    left.legend(fontsize=8, ncol=2)
    right.set_xlabel("redshift")
    right.set_ylabel(r"fiducial bias $b_i = A/D(z_i)$")
    right.set_title("Linear bias per bin")
    right.legend(fontsize=8)
    figure.tight_layout()
    path = output_dir / "desi2023_inputs.png"
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path


def _set_w0wa_limits(axis, covariances: list[np.ndarray]) -> None:
    sigmas = [np.sqrt(np.diag(covariance)) for covariance in covariances]
    axis.set_xlim(
        -1.0 - 1.15 * 2.0 * max(s[0] for s in sigmas), -1.0 + 1.15 * 2.0 * max(s[0] for s in sigmas)
    )
    axis.set_ylim(-1.15 * 2.0 * max(s[1] for s in sigmas), 1.15 * 2.0 * max(s[1] for s in sigmas))
    axis.axvline(-1.0, color="grey", linewidth=0.8)
    axis.axhline(0.0, color="grey", linewidth=0.8)
    axis.set_xlabel(r"$w_0$")
    axis.set_ylabel(r"$w_a$")
    axis.grid(alpha=0.2)


def plot_desi2023_w0wa(results_dir: Path, output_dir: Path) -> Path:
    """Per-tracer ``w0``-``wa`` ellipses (QSO on top), a zoom without QSO, and the full set."""
    report = load_json(results_dir / "survey_forecasts_w0waCDM.json")
    covariance = {case: _w0wa_covariance(report, (case,)) for _, case, _, _ in DESI2023_TRACERS}
    figure, axes = plt.subplots(1, 3, figsize=(16, 5.2))

    # Panel 1: every tracer; the quasars are drawn last, shaded, so they sit on top.
    ordered = [t for t in DESI2023_TRACERS if t[2] != "QSO"] + [
        t for t in DESI2023_TRACERS if t[2] == "QSO"
    ]
    for _, case, label, colour in ordered:
        is_qso = label == "QSO"
        _draw_ellipse(
            axes[0],
            covariance[case],
            colour,
            label,
            fill_alpha=0.15 if is_qso else 0.0,
            zorder=10 if is_qso else 2,
        )
    _set_w0wa_limits(axes[0], list(covariance.values()))
    axes[0].set_title("DESI 2023, single tracers (QSO on top)")
    axes[0].legend(fontsize=8)

    # Panel 2: zoom on the three galaxy tracers.
    galaxies = [t for t in DESI2023_TRACERS if t[2] != "QSO"]
    for _, case, label, colour in galaxies:
        _draw_ellipse(axes[1], covariance[case], colour, label)
    _set_w0wa_limits(axes[1], [covariance[case] for _, case, _, _ in galaxies])
    axes[1].set_title("Zoom: BGS, LRG and ELG")
    axes[1].legend(fontsize=8)

    # Panel 3: full DESI 2023 against the legacy BGS+ELG and Euclid GCsp.
    curves = (
        (DESI2023_COMBINED, "DESI 2023 BGS+LRG+ELG+QSO", "#d62728"),
        (("desi-bgs", "desi-elg"), "DESI legacy BGS+ELG", "#ff7f0e"),
        (("euclid-spectro",), "Euclid GCsp", "#1f77b4"),
    )
    covariances = []
    for members, label, colour in curves:
        cov = _w0wa_covariance(report, members)
        covariances.append(cov)
        _draw_ellipse(axes[2], cov, colour, label)
    _set_w0wa_limits(axes[2], covariances)
    axes[2].set_title("Full DESI 2023 vs legacy vs Euclid (GCsp)")
    axes[2].legend(fontsize=8)

    figure.suptitle(
        r"$w_0w_a$CDM, GCsp only, marginalised $1\sigma$ (solid) and $2\sigma$ (dashed)"
    )
    figure.tight_layout()
    path = output_dir / "desi2023_w0wa.png"
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
    report = load_json(args.results_dir / "survey_forecasts_w0waCDM.json")
    if {result["name"] for result in report["results"]} >= set(DESI2023_COMBINED):
        figures.append(plot_desi2023_inputs(args.output_dir))
        figures.append(plot_desi2023_w0wa(args.results_dir, args.output_dir))
    for figure in figures:
        print(f"Wrote {figure}")


if __name__ == "__main__":
    main()

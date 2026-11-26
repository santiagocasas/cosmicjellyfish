"""Fig. 4: forecast comparison across Euclid, Rubin/LSST, DESI and SKAO.

The script runs a compact subset of the survey forecast comparison on a common GR
fiducial, first in LCDM and then in w0waCDM: Euclid and Rubin/LSST photometric probes,
Euclid spectroscopy, DESI (ELG + BGS, added as independent Fisher blocks) and SKAO
intensity mapping combined with the DESI ELG sample (auto- and cross-spectra analysed
jointly). It draws the marginalised errors and, in two separate panels, the w0-wa ellipses
of the photometric and of the spectroscopic probes. It takes a few minutes end-to-end and
writes ``paper/figures/fig4_survey_comparison.png``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse
from matplotlib.ticker import MaxNLocator

REPO_ROOT = Path(__file__).resolve().parents[2]

#: forecast cases that have to be run; DESI ELG + BGS is added by the script as a combination
RUN_CASES = ("euclid-photo", "rubin-photo", "euclid-spectro", "desi-bgs", "desi-elg")
RUN_CASES += ("skao-im-desi-joint",)

#: (entry, legend label, colour, forecast cases whose Fisher blocks are added); the order is the
#: order of the bars. DESI ELG and BGS cover different redshifts, so their blocks are independent.
ENTRIES = (
    ("euclid-photo", "Euclid GCph+WL", "#1f77b4", ("euclid-photo",)),
    ("rubin-photo", "Rubin/LSST GCph+WL", "#ff7f0e", ("rubin-photo",)),
    ("euclid-spectro", "Euclid GCsp", "#2ca02c", ("euclid-spectro",)),
    ("desi", "DESI ELG+BGS", "#d62728", ("desi-bgs", "desi-elg")),
    ("skao-im-desi", "SKAO IM + DESI ELG", "#9467bd", ("skao-im-desi-joint",)),
)
PHOTOMETRIC = ("euclid-photo", "rubin-photo")
SPECTROSCOPIC = ("euclid-spectro", "desi", "skao-im-desi")
PARAMETER_LABELS = {"Omegam": r"$\Omega_m$", "sigma8": r"$\sigma_8$"}
FIDUCIAL_W0WA = (-1.0, 0.0)
FONT = 12


def run_model(model: str, output_dir: Path) -> dict:
    """Run the selected forecast cases for one model and return the report."""
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/validation/run_survey_forecasts.py"),
        "--model",
        model,
        "--output-dir",
        str(output_dir),
    ]
    for case in RUN_CASES:
        command.extend(["--case", case])
    subprocess.run(command, check=True, cwd=REPO_ROOT)
    return json.loads((output_dir / f"survey_forecasts_{model}.json").read_text())


def covariance(report: dict, members: tuple[str, ...]) -> tuple[list[str], np.ndarray]:
    """Marginalised covariance of the summed, nuisance-marginalised Fisher blocks.

    Every block follows the free-parameter order of the report. The blocks are added as
    matrices and inverted afterwards, so the parameter correlations are kept.
    """
    names = list(report["freepars"])
    results = {result["name"]: result for result in report["results"]}
    total = sum(np.asarray(results[member]["fisher_matrix"], dtype=float) for member in members)
    return names, np.linalg.inv(total)


def w0wa_covariance(report: dict, members: tuple[str, ...]) -> np.ndarray:
    """Marginalised (w0, wa) covariance of a (sum of) forecast(s)."""
    names, cov = covariance(report, members)
    indices = [names.index("w0"), names.index("wa")]
    return cov[np.ix_(indices, indices)]


def draw_ellipse(
    axis, covariance: np.ndarray, centre: tuple[float, float], colour: str, label: str
) -> None:
    """Draw the 1-sigma ellipse of a two-parameter covariance at the fiducial point."""
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    axis.add_patch(
        Ellipse(
            centre,
            width=2.0 * np.sqrt(eigenvalues[0]),
            height=2.0 * np.sqrt(eigenvalues[1]),
            angle=angle,
            facecolor=colour,
            alpha=0.18,
            edgecolor="none",
        )
    )
    axis.add_patch(
        Ellipse(
            centre,
            width=2.0 * np.sqrt(eigenvalues[0]),
            height=2.0 * np.sqrt(eigenvalues[1]),
            angle=angle,
            facecolor="none",
            edgecolor=colour,
            linewidth=2.0,
            label=label,
        )
    )


def ellipse_panel(axis, report: dict, names: tuple[str, ...], title: str) -> None:
    """Draw the w0-wa ellipses of ``names`` and set the limits from their extent.

    Matplotlib patches do not rescale the axes, so the limits are taken from the half-widths
    of the ellipses (the square roots of the marginal variances) with some padding.
    """
    entries = {name: (label, colour, members) for name, label, colour, members in ENTRIES}
    half = np.zeros(2)
    for name in names:
        label, colour, members = entries[name]
        cov = w0wa_covariance(report, members)
        draw_ellipse(axis, cov, FIDUCIAL_W0WA, colour, label)
        half = np.maximum(half, np.sqrt(np.diag(cov)))
    pad = 1.3
    axis.set_xlim(FIDUCIAL_W0WA[0] - pad * half[0], FIDUCIAL_W0WA[0] + pad * half[0])
    axis.set_ylim(FIDUCIAL_W0WA[1] - pad * half[1], FIDUCIAL_W0WA[1] + pad * half[1])
    axis.axhline(FIDUCIAL_W0WA[1], color="grey", linewidth=0.8)
    axis.axvline(FIDUCIAL_W0WA[0], color="grey", linewidth=0.8)
    axis.xaxis.set_major_locator(MaxNLocator(4))
    axis.yaxis.set_major_locator(MaxNLocator(5))
    axis.tick_params(labelsize=FONT - 1)
    axis.set_xlabel(r"$w_0$", fontsize=FONT)
    axis.set_ylabel(r"$w_a$", fontsize=FONT)
    axis.set_title(title, fontsize=FONT)
    axis.legend(fontsize=FONT - 2, loc="upper right", frameon=False)


def bar_panel(axis, report: dict) -> None:
    """Marginalised LCDM errors on Omega_m and sigma_8, one pair of bars per survey."""
    width = 0.38
    positions = np.arange(len(ENTRIES))
    for index, parameter in enumerate(("Omegam", "sigma8")):
        values = []
        for _name, _label, _colour, members in ENTRIES:
            names, cov = covariance(report, members)
            values.append(float(np.sqrt(cov[names.index(parameter), names.index(parameter)])))
        axis.barh(
            positions + (index - 0.5) * width,
            values,
            height=width,
            color=[colour for _name, _label, colour, _members in ENTRIES],
            alpha=1.0 if index == 0 else 0.45,
            label=PARAMETER_LABELS[parameter],
        )
    axis.set_yticks(positions)
    axis.set_yticklabels([label for _name, label, _colour, _members in ENTRIES], fontsize=FONT - 1)
    axis.invert_yaxis()
    axis.set_xscale("log")
    axis.set_xlabel(r"marginalised $1\sigma$, $\Lambda$CDM", fontsize=FONT)
    axis.tick_params(axis="x", labelsize=FONT - 1)
    axis.grid(axis="x", alpha=0.3)
    axis.legend(fontsize=FONT - 2, loc="lower right", frameon=False)


def main() -> None:
    output_dir = Path(tempfile.mkdtemp(prefix="paper_survey_comparison_"))
    lcdm = run_model("LCDM", output_dir)
    w0wa = run_model("w0waCDM", output_dir)

    figure, (bars, photo, spectro) = plt.subplots(
        1, 3, figsize=(15, 4.8), gridspec_kw={"width_ratios": [1.15, 1, 1]}
    )
    bar_panel(bars, lcdm)
    ellipse_panel(photo, w0wa, PHOTOMETRIC, r"photometric, $w_0w_a$CDM, $1\sigma$")
    ellipse_panel(spectro, w0wa, SPECTROSCOPIC, r"spectroscopic, $w_0w_a$CDM, $1\sigma$")

    figure.tight_layout()
    path = REPO_ROOT / "paper/figures/fig4_survey_comparison.png"
    figure.savefig(path, dpi=200)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

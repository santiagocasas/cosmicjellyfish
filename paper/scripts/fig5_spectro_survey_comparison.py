"""Fig. 5: spectroscopic constraints from Euclid GCsp, DESI and SKAO IM x DESI.

Three entries are compared on the same GR fiducial, with all nuisance parameters
marginalised:

* Euclid spectroscopic clustering (``euclid-spectro``);
* the four DESI 2023 galaxy samples (BGS, LRG, ELG and QSO), added as independent
  Fisher blocks because they cover disjoint redshift ranges;
* SKAO intensity mapping combined with the DESI ELG sample, with the galaxy auto-,
  IM auto- and cross-spectra analysed jointly (``skao-im-desi-joint``).

The left panel shows the marginalised 1-sigma errors on Omega_m and sigma_8 in
LCDM; the right panel shows the 68.27% and 95.45% joint w0-wa contours in w0waCDM.
It takes a few minutes end-to-end and writes
``paper/figures/fig5_spectro_survey_comparison.png``.
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

#: Forecast cases that have to be run. The DESI combination is built below by adding
#: the four independent tracer blocks.
RUN_CASES = (
    "euclid-spectro",
    "desi2023-bgs",
    "desi2023-lrg",
    "desi2023-elg",
    "desi2023-qso",
    "skao-im-desi-joint",
)

#: (entry, legend label, colour, forecast cases whose Fisher blocks are added).
ENTRIES = (
    ("euclid", "Euclid GCsp", "#2ca02c", ("euclid-spectro",)),
    (
        "desi2023",
        "DESI BGS+LRG+ELG+QSO",
        "#d62728",
        ("desi2023-bgs", "desi2023-lrg", "desi2023-elg", "desi2023-qso"),
    ),
    (
        "skao-im-desi",
        r"SKAO IM $\times$ DESI ELG (auto+cross)",
        "#9467bd",
        ("skao-im-desi-joint",),
    ),
)
PARAMETER_LABELS = {"Omegam": r"$\Omega_m$", "sigma8": r"$\sigma_8$"}
FIDUCIAL_W0WA = (-1.0, 0.0)
#: Joint confidence levels of the contours: 68.27% (solid) and 95.45% (dashed).
CONTOUR_SIGMAS = (1.515, 2.486)
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
    """Marginalised covariance of the summed, nuisance-marginalised Fisher blocks."""
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
    axis, covariance: np.ndarray, colour: str, label: str, fill_alpha: float = 0.0
) -> None:
    """Draw the 68.27% (solid) and 95.45% (dashed) joint contours at the fiducial point."""
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    for index, (sigma, linestyle) in enumerate(zip(CONTOUR_SIGMAS, ("-", "--"))):
        axis.add_patch(
            Ellipse(
                FIDUCIAL_W0WA,
                width=2.0 * sigma * np.sqrt(eigenvalues[0]),
                height=2.0 * sigma * np.sqrt(eigenvalues[1]),
                angle=angle,
                facecolor=colour if (fill_alpha and index == 0) else "none",
                edgecolor=colour,
                alpha=1.0 if index == 0 else 0.55,
                linestyle=linestyle,
                linewidth=1.8,
                label=label if index == 0 else None,
            )
        )


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
        for position, value in zip(positions + (index - 0.5) * width, values):
            axis.text(
                value,
                position,
                f"  {value:.1e}",
                va="center",
                fontsize=FONT - 4,
                color="0.25",
            )
    axis.set_yticks(positions)
    axis.set_yticklabels([label for _name, label, _colour, _members in ENTRIES], fontsize=FONT - 1)
    axis.invert_yaxis()
    axis.set_xscale("log")
    axis.set_xlim(right=axis.get_xlim()[1] * 2.2)
    axis.set_xlabel(r"marginalised $1\sigma$, $\Lambda$CDM", fontsize=FONT)
    axis.tick_params(axis="x", labelsize=FONT - 1)
    axis.grid(axis="x", alpha=0.3)
    axis.legend(fontsize=FONT - 2, loc="lower right", frameon=False)


def ellipse_panel(axis, report: dict) -> None:
    """68.27% and 95.45% w0-wa contours of the three entries."""
    half = np.zeros(2)
    for _name, label, colour, members in ENTRIES:
        cov = w0wa_covariance(report, members)
        draw_ellipse(axis, cov, colour, label)
        half = np.maximum(half, CONTOUR_SIGMAS[-1] * np.sqrt(np.diag(cov)))
    pad = 1.15
    axis.set_xlim(FIDUCIAL_W0WA[0] - pad * half[0], FIDUCIAL_W0WA[0] + pad * half[0])
    axis.set_ylim(FIDUCIAL_W0WA[1] - pad * half[1], FIDUCIAL_W0WA[1] + pad * half[1])
    axis.axhline(FIDUCIAL_W0WA[1], color="grey", linewidth=0.8)
    axis.axvline(FIDUCIAL_W0WA[0], color="grey", linewidth=0.8)
    axis.xaxis.set_major_locator(MaxNLocator(4))
    axis.yaxis.set_major_locator(MaxNLocator(5))
    axis.tick_params(labelsize=FONT - 1)
    axis.set_xlabel(r"$w_0$", fontsize=FONT)
    axis.set_ylabel(r"$w_a$", fontsize=FONT)
    axis.set_title(r"$w_0w_a$CDM, 68.27% (solid) and 95.45% (dashed)", fontsize=FONT)
    axis.legend(fontsize=FONT - 2, loc="upper right", frameon=False)


def main() -> None:
    output_dir = Path(tempfile.mkdtemp(prefix="paper_spectro_comparison_"))
    lcdm = run_model("LCDM", output_dir)
    w0wa = run_model("w0waCDM", output_dir)

    figure, (bars, ellipses) = plt.subplots(
        1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.05, 1]}
    )
    bar_panel(bars, lcdm)
    ellipse_panel(ellipses, w0wa)

    figure.tight_layout()
    path = REPO_ROOT / "paper/figures/fig5_spectro_survey_comparison.png"
    figure.savefig(path, dpi=200)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

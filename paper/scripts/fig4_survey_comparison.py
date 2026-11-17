"""Fig. 4: forecast comparison across DESI, Rubin/LSST, SKAO and Euclid.

The script runs a compact subset of the survey forecast comparison (Euclid 3x2pt,
Rubin/LSST 3x2pt, DESI ELG and SKAO intensity mapping) on a common GR fiducial, first in
LCDM and then in w0waCDM, and draws the marginalised errors and the w0-wa ellipses. It
takes about three minutes end-to-end and writes ``paper/figures/fig4_survey_comparison.png``.
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

from cosmicjellyfish.analysis.fisher_matrix import fisher_matrix
from cosmicjellyfish.analysis.fisher_operations import marginalise

REPO_ROOT = Path(__file__).resolve().parents[2]
CASES = (
    ("euclid-photo", "Euclid photo", "#1f77b4"),
    ("rubin-photo", "Rubin photo", "#ff7f0e"),
    ("desi-elg", "DESI ELG", "#d62728"),
    ("skao-im", "SKAO IM", "#9467bd"),
)
PARAMETER_LABELS = {"Omegam": r"$\Omega_m$", "sigma8": r"$\sigma_8$"}


def run_model(model: str, output_dir: Path) -> dict:
    """Run the selected forecast cases for one cosmological model."""
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/validation/run_survey_forecasts.py"),
        "--model",
        model,
        "--output-dir",
        str(output_dir),
    ]
    for case, _label, _colour in CASES:
        command.extend(["--case", case])
    subprocess.run(command, check=True, cwd=REPO_ROOT)
    path = output_dir / f"survey_forecasts_{model}.json"
    return json.loads(path.read_text())


def fisher_path(output_dir: Path, case: str) -> Path:
    """Return the w0waCDM Fisher matrix of one case."""
    pattern = f"CosmicFish_*_survey_forecast_w0wacdm_{case.replace('-', '_')}_*_FM.txt"
    return sorted((output_dir / "fishers").glob(pattern))[0]


def draw_ellipse(
    axis, covariance: np.ndarray, centre: tuple[float, float], colour: str, label: str
) -> None:
    """Draw the 1-sigma ellipse of a two-parameter covariance at the fiducial point."""
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    angle = np.degrees(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))
    ellipse = Ellipse(
        centre,
        width=2.0 * np.sqrt(eigenvalues[0]),
        height=2.0 * np.sqrt(eigenvalues[1]),
        angle=angle,
        facecolor="none",
        edgecolor=colour,
        linewidth=2.0,
        label=label,
    )
    axis.add_patch(ellipse)


def main() -> None:
    output_dir = Path(tempfile.mkdtemp(prefix="paper_survey_comparison_"))
    lcdm = run_model("LCDM", output_dir)
    run_model("w0waCDM", output_dir)

    figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4.4))

    labels = [result["label"] for result in lcdm["results"]]
    positions = np.arange(len(labels))
    width = 0.38
    for index, parameter in enumerate(("Omegam", "sigma8")):
        values = [result["sigma"][parameter] for result in lcdm["results"]]
        left.barh(
            positions + (index - 0.5) * width,
            values,
            height=width,
            color=[colour for _case, _label, colour in CASES],
            alpha=1.0 if index == 0 else 0.45,
            label=PARAMETER_LABELS[parameter],
        )
    left.set_yticks(positions)
    left.set_yticklabels(labels, fontsize=9)
    left.set_xscale("log")
    left.set_xlabel(r"marginalised $1\sigma$, $\Lambda$CDM")
    left.grid(axis="x", alpha=0.3)
    left.legend(fontsize=8)

    for case, label, colour in CASES:
        matrix = marginalise(
            fisher_matrix(file_name=str(fisher_path(output_dir, case))), ["w0", "wa"]
        )
        draw_ellipse(
            right,
            np.linalg.inv(matrix.get_fisher_matrix()),
            centre=(-1.0, 0.0),
            colour=colour,
            label=label,
        )
    right.axhline(0.0, color="grey", linewidth=0.8)
    right.axvline(-1.0, color="grey", linewidth=0.8)
    right.set_xlabel(r"$w_0$")
    right.set_ylabel(r"$w_a$")
    right.set_title(r"$w_0w_a$CDM, $1\sigma$")
    right.legend(fontsize=8)

    figure.tight_layout()
    path = REPO_ROOT / "paper/figures/fig4_survey_comparison.png"
    figure.savefig(path, dpi=200)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()

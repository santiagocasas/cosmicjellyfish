#!/usr/bin/env python
"""Plot the autodiff-versus-finite-difference ratios of the JOSS paper.

Reads ``autodiff_sigma_ratios.txt`` written by ``autodiff_numbers.py`` and draws the
marginalised errors from finite differences relative to autodiff for all parameters:
the same JAX observable and the standard NumPy one. Writes
``<out-dir>/fig_autodiff_ratios.{png,pdf}``.

The paper quotes the largest absolute deviation: 0.05% (JAX finite differences) and
0.4% (NumPy finite differences) for the 17 parameters.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

TEX = {
    "10^9As": r"$10^9A_s$",
    "Omegam": r"$\Omega_m$",
    "Omegab": r"$\Omega_b$",
    "h": r"$h$",
    "ns": r"$n_s$",
    "sigma8": r"$\sigma_8$",
    "AIA": r"$A_{\rm IA}$",
    "betaIA": r"$\beta_{\rm IA}$",
    "etaIA": r"$\eta_{\rm IA}$",
}


def read_ratios(path: Path) -> tuple[list[str], np.ndarray]:
    """Return the parameter names and the (JAX FD, NumPy FD) ratio columns."""
    header = path.read_text().splitlines()[0].lstrip("#").split()
    names = header[2:]
    ratios = np.loadtxt(path)
    if ratios.shape != (len(names), 2):
        raise ValueError(f"{path} has shape {ratios.shape}, expected ({len(names)}, 2)")
    return names, ratios


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="directory holding autodiff_sigma_ratios.txt (and receiving the figure)",
    )
    args = parser.parse_args()
    out = args.out_dir.resolve()
    names, ratios = read_ratios(out / "autodiff_sigma_ratios.txt")
    r_jfd, r_fd = 100 * ratios[:, 0], 100 * ratios[:, 1]

    labels = [TEX.get(name, rf"$b_{{{name[1:]}}}$") for name in names]
    x = np.arange(len(names))
    figure, axis = plt.subplots(figsize=(8, 3.4))
    axis.axhline(0, color="0.4", lw=0.8)
    axis.plot(x, r_jfd, "o", color="#2a9d8f", label="finite differences, same JAX observable")
    axis.plot(
        x,
        r_fd,
        "s",
        color="#3a86ff",
        mfc="none",
        label="finite differences, NumPy observable",
    )
    axis.set_xticks(x, labels)
    axis.set_ylabel(r"$\sigma_{\rm FD}/\sigma_{\rm AD} - 1$  [%]")
    axis.set_title(
        "Marginalised errors relative to autodiff (Euclid WL+GCph, jaxcosmo)", fontsize=10
    )
    axis.legend(frameon=False, fontsize=9)
    axis.text(
        0.99,
        0.03,
        f"max |JAX FD| = {np.abs(r_jfd).max():.3f}%\n"
        f"max |NumPy FD| = {np.abs(r_fd).max():.3f}%",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="0.25",
    )
    figure.tight_layout()
    for extension in ("png", "pdf"):
        path = out / f"fig_autodiff_ratios.{extension}"
        figure.savefig(path, dpi=200)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

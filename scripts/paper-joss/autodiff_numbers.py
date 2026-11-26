#!/usr/bin/env python
"""Reproduce the autodiff numbers quoted in the JOSS paper.

Paper text ("Fisher matrices against posteriors"): for the Euclid photometric probes
(WL+GCph, jaxcosmo backend, massless neutrinos), the marginalised errors from automatic
differentiation agree with finite differences of the same JAX observable to 0.05% and
with the standard NumPy implementation to 0.4%, for all 17 parameters.

Writes ``<out-dir>/autodiff_sigma_ratios.txt`` and ``<out-dir>/autodiff_summary.json``.
Takes a few minutes on a laptop CPU.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from cosmicjellyfish.fishermatrix.cosmicfish import FisherMatrix
from cosmicjellyfish.fishermatrix.jaxcosmo_derivatives import (
    JaxAutodiffProvider,
    JaxFiniteDifferenceProvider,
)

FIDUCIAL = {"10^9As": 2.1, "Omegam": 0.32, "Omegab": 0.05, "h": 0.67, "ns": 0.96, "mnu": 0.0}
FREEPARS = {name: 0.01 for name in ["10^9As", "Omegam", "Omegab", "h"]}
PAPER_VALUES = {"jax_fd_percent": 0.05, "numpy_fd_percent": 0.4, "n_params": 17}


def forecast(provider, outroot: str, results_dir: str):
    options = {  # a fresh dictionary for each forecast
        "code": "jaxcosmo",
        "accuracy": 1,
        "feedback": 0,
        "nonlinear": True,
        "derivatives": "3PT",
        "results_dir": results_dir,
        "outroot": outroot,
        "survey_name_photo": "Euclid-Photometric-ISTF-Pessimistic",
    }
    return FisherMatrix(
        fiducialpars=dict(FIDUCIAL),
        freepars=dict(FREEPARS),
        options=options,
        observables=["GCph", "WL"],
        cosmoModel="LCDM",
        surveyName="Euclid",
        derivative_provider=provider,
    ).compute()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "output")
    args = parser.parse_args()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results_dir = os.path.join(str(out), "autodiff_results") + "/"

    fisher_ad = forecast(JaxAutodiffProvider(), "paper_ad", results_dir)
    fisher_jfd = forecast(JaxFiniteDifferenceProvider(), "paper_jaxfd", results_dir)
    fisher_fd = forecast(None, "paper_fd", results_dir)

    names = fisher_ad.get_param_names()
    assert names == fisher_jfd.get_param_names() == fisher_fd.get_param_names()
    sig_ad = fisher_ad.get_confidence_bounds()
    r_jfd = fisher_jfd.get_confidence_bounds() / sig_ad - 1
    r_fd = fisher_fd.get_confidence_bounds() / sig_ad - 1

    np.savetxt(
        out / "autodiff_sigma_ratios.txt",
        np.c_[r_jfd, r_fd],
        header="JAXFD/AD-1 stdFD/AD-1  " + " ".join(names),
    )
    summary = {
        "n_params": len(names),
        "params": list(names),
        "max_abs_jax_fd_percent": 100 * float(np.abs(r_jfd).max()),
        "max_abs_numpy_fd_percent": 100 * float(np.abs(r_fd).max()),
        "paper": PAPER_VALUES,
    }
    (out / "autodiff_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"{len(names)} parameters: {', '.join(names)}")
    print(
        f"max |sigma_FD/sigma_AD - 1|: JAX FD {summary['max_abs_jax_fd_percent']:.3f}% "
        f"(paper {PAPER_VALUES['jax_fd_percent']}%), NumPy FD "
        f"{summary['max_abs_numpy_fd_percent']:.3f}% (paper {PAPER_VALUES['numpy_fd_percent']}%)"
    )


if __name__ == "__main__":
    main()

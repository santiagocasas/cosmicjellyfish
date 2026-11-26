#!/usr/bin/env python
"""Compare a reproduced Fisher-vs-Nautilus run with the numbers quoted in the paper.

Reads the statistics JSON written by ``render_likelihood_validation.py`` for the new
run, the tracked reference statistics of the published run, and the per-case
``case_metadata.json`` (wall-clock times). Prints one table and writes it to
``<out-dir>/comparison.md``. Nested sampling is stochastic, so the reproduced
numbers agree with the paper only within the sampling noise (a few per mille on the
errors for n_eff = 2000); the paper quotes max |sigma_Nautilus / sigma_Fisher - 1|
over Omegam and sigma8, rounded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REFERENCE = (
    REPO / "scripts/likelihood_validation_results/wl_gcsp_symbolic_euclid_64cpu_statistics.json"
)
STATS_NAME = "wl_gcsp_symbolic_euclid_64cpu_statistics.json"
CASES = {"wl": "WL", "gcsp": "GCsp", "joint": "WL+GCsp"}
# Values printed in paper/paper.md ("Fisher matrices against posteriors").
PAPER = {
    "WL": {"dims": 5, "max_sigma_dev_percent": 5.0, "minutes": 17},
    "GCsp": {"dims": 10, "max_sigma_dev_percent": 0.4, "minutes": 22},
    "WL+GCsp": {"dims": 13, "max_sigma_dev_percent": 1.3, "minutes": 105},
}


def _max_dev(probe: dict) -> float:
    return 100 * max(abs(r - 1) for r in probe["sigma_ratio"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Nautilus run directory")
    parser.add_argument("--out-dir", type=Path, required=True, help="Reproduction output dir")
    args = parser.parse_args()

    new = json.loads((args.out_dir / "stats" / STATS_NAME).read_text())["probes"]
    ref = json.loads(REFERENCE.read_text())["probes"]

    header = (
        "| Probe | dims | max dev. paper | published run | this run | sigma ratios (this run) "
        "| ESS | minutes paper | minutes this run | workers |"
    )
    rows = [header, "|" + "---|" * 10]
    for case, label in CASES.items():
        meta = json.loads((args.run_dir / case / "case_metadata.json").read_text())
        ratios = ", ".join(f"{r:.4f}" for r in new[label]["sigma_ratio"])
        rows.append(
            f"| {label} | {len(meta['sampled_parameters'])} (paper {PAPER[label]['dims']}) "
            f"| {PAPER[label]['max_sigma_dev_percent']}% | {_max_dev(ref[label]):.2f}% "
            f"| {_max_dev(new[label]):.2f}% | {ratios} | {new[label]['effective_sample_size']:.0f} "
            f"| {PAPER[label]['minutes']} | {meta['elapsed_seconds'] / 60:.0f} | {meta['workers']} |"
        )
    table = "\n".join(rows)
    print(table)
    (args.out_dir / "comparison.md").write_text(table + "\n")
    print(f"\nSaved: {args.out_dir / 'comparison.md'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Run the Python listings of the JOSS paper exactly as printed.

The ``python`` code blocks are extracted from ``paper/paper.md`` so the paper text
and what is tested cannot drift apart. Each block is written to
``<out-dir>/listings/listing_<n>.py`` and executed there with the current
interpreter (outputs such as ``results/`` and ``chains/`` stay in that folder).

Examples
--------
    uv run python scripts/paper-joss/check_listings.py --list
    uv run python scripts/paper-joss/check_listings.py --only 1
    uv run python scripts/paper-joss/check_listings.py   # all, incl. the Nautilus one
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAPER = REPO / "paper" / "paper.md"
BLOCK = re.compile(r"^```python\n(.*?)^```", re.MULTILINE | re.DOTALL)


def extract_listings(paper: Path = PAPER) -> list[str]:
    """Return the python code blocks of the paper, in order."""
    return BLOCK.findall(paper.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "output")
    parser.add_argument("--only", type=int, nargs="*", help="1-based listing numbers to run")
    parser.add_argument("--list", action="store_true", help="Print the listings and exit")
    args = parser.parse_args()

    listings = extract_listings()
    if not listings:
        print(f"No python listings found in {PAPER}")
        return 1
    if args.list:
        for n, code in enumerate(listings, start=1):
            print(f"--- listing {n} ---\n{code}")
        return 0

    workdir = args.out_dir.resolve() / "listings"
    workdir.mkdir(parents=True, exist_ok=True)
    selected = args.only or range(1, len(listings) + 1)
    failed = []
    for n in selected:
        script = workdir / f"listing_{n}.py"
        script.write_text(listings[n - 1])
        print(f"=== listing {n}: {script}", flush=True)
        started = time.time()
        result = subprocess.run([sys.executable, script.name], cwd=workdir, check=False)
        status = "OK" if result.returncode == 0 else f"FAILED ({result.returncode})"
        print(f"=== listing {n}: {status} in {time.time() - started:.0f} s", flush=True)
        if result.returncode != 0:
            failed.append(n)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check that the package version and the citation metadata agree.

The single source of truth is ``cosmicjellyfish/version.py``. This script fails
(exit code 1) if ``CITATION.cff`` carries a different ``version:`` value, so
that the citation file cannot silently drift from the released package.

It only uses the standard library and does not import the package itself, so it
runs in any CI job without installing dependencies.

Usage
-----
    python scripts/maintenance/release/check_version_consistency.py
"""

from __future__ import annotations

import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERSION_FILE = ROOT / "cosmicjellyfish" / "version.py"
CITATION_FILE = ROOT / "CITATION.cff"


def package_version() -> str:
    """Return ``VERSION`` as defined in ``cosmicjellyfish/version.py``."""
    return str(runpy.run_path(str(VERSION_FILE))["VERSION"])


def citation_version() -> str:
    """Return the top-level ``version:`` entry of ``CITATION.cff``."""
    for line in CITATION_FILE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^version:\s*['\"]?([^'\"\s#]+)['\"]?\s*(?:#.*)?$", line)
        if match:
            return match.group(1)
    raise SystemExit(f"Error, no top-level 'version:' entry found in {CITATION_FILE}")


def main() -> int:
    """Compare the two versions and report the result."""
    expected = package_version()
    found = citation_version()
    if expected != found:
        print(
            f"Version mismatch: {VERSION_FILE.relative_to(ROOT)} says {expected!r} "
            f"but {CITATION_FILE.name} says {found!r}. "
            f"Update the 'version:' line in {CITATION_FILE.name}.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: package and {CITATION_FILE.name} both report version {expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check the CRediT roles of paper.md.

The machine-readable roles live in the YAML front matter of ``paper.md`` (``roles:`` under
each author). They end up as ``<role vocab="credit" ...>`` elements in the JATS output.
The human-readable list sits in the "Author contributions" section. This script

1. validates every role against the 14 official CRediT roles (slug and name), and
2. checks that the prose list names the same roles as the YAML for every author.

Usage (from the repository root)::

    python paper/scripts/check_credit_roles.py

Requires PyYAML. Exits with status 1 if anything is inconsistent.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

PAPER = Path(__file__).resolve().parents[1] / "paper.md"

CREDIT = {
    "conceptualization": "Conceptualization",
    "data-curation": "Data curation",
    "formal-analysis": "Formal analysis",
    "funding-acquisition": "Funding acquisition",
    "investigation": "Investigation",
    "methodology": "Methodology",
    "project-administration": "Project administration",
    "resources": "Resources",
    "software": "Software",
    "supervision": "Supervision",
    "validation": "Validation",
    "visualization": "Visualization",
    "writing-original-draft": "Writing \u2013 original draft",
    "writing-review-editing": "Writing \u2013 review & editing",
}


def norm(text: str) -> str:
    """Normalise a role name for comparison (en dash and '--' are equivalent)."""
    return re.sub(r"\s+", " ", text.replace("\u2013", "--").replace("-", " ")).strip().lower()


def front_matter(text: str) -> dict:
    return yaml.safe_load(text.split("---", 2)[1])


def prose_roles(text: str) -> dict[str, set[str]]:
    """Map 'S. Casas' -> {normalised roles} from the bullets of '# Author contributions'."""
    section = text.split("# Author contributions", 1)[1].split("\n# ", 1)[0]
    bullets = re.findall(r"^- \*\*(.+?)\*\*: (.*?)(?=^- |\n\n|\Z)", section, re.S | re.M)
    out = {}
    for who, body in bullets:
        body = re.sub(r"\s+", " ", body).strip().rstrip(".")
        body = re.sub(r"\$[^$]*\$", "", body)  # drop inline math, e.g. $f(R)$
        body = re.sub(r"\([^()]*\)", "", body)  # drop parenthetical remarks
        out[who] = {norm(r) for r in body.split(",") if r.strip() and "TODO" not in r}
    return out


def main() -> int:
    text = PAPER.read_text(encoding="utf-8")
    authors = front_matter(text)["authors"]
    prose = prose_roles(text)
    errors = []

    for author in authors:
        name = author["name"]
        roles = author.get("roles", [])
        slugs = []
        for role in roles:
            slug, label = role.get("credit"), role.get("credit-name")
            if slug not in CREDIT:
                errors.append(f"{name}: unknown CRediT slug {slug!r}")
            elif label != CREDIT[slug]:
                errors.append(f"{name}: credit-name {label!r} should be {CREDIT[slug]!r}")
            slugs.append(slug)
        if len(slugs) != len(set(slugs)):
            errors.append(f"{name}: duplicated roles")

        initials = " ".join(f"{p[0]}." if not p.endswith(".") else p for p in name.split()[:-1])
        key = f"{initials} {name.split()[-1]}"
        if key not in prose:
            errors.append(f"{name}: no bullet {key!r} in 'Author contributions'")
            continue
        yaml_set = {norm(CREDIT[s]) for s in slugs if s in CREDIT}
        for r in prose[key] - yaml_set:
            errors.append(f"{name}: '{r}' in prose but not in YAML")
        for r in yaml_set - prose[key]:
            errors.append(f"{name}: '{r}' in YAML but not in prose")
        if not roles:
            print(f"warning: {name} has no roles yet")

    n = sum(len(a.get("roles", [])) for a in authors)
    for e in errors:
        print("error:", e)
    print(f"{len(authors)} authors, {n} roles, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

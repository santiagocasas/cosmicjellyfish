"""Plot the ARA exploration graph of the development as a timeline (paper Figure 4).

The development decisions, experiments, questions, pivots and dead ends were
recorded with the Agent-Native Research Artifact (ARA) ``research-manager``
skill in ``ara/trace/exploration_tree.yaml``. That trace lives on the ``dev``
branch (worktree ``cfp-dev``), not on this branch, so its path is an argument.

Each node is placed at its timestamp (x) in the lane of its type (y) and is
coloured by provenance (human or AI). Grey arcs are the ``also_depends_on``
edges and the parent -> child nesting of the tree. Only types, provenance,
times and edges are read; titles and texts are not shown.

Usage (from the repository root of this branch):

    python paper/scripts/fig6_ara_trace.py --ara ../cfp-dev/ara
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

LANES = ["question", "decision", "experiment", "pivot", "dead_end"]
LANE_LABEL = {
    "question": "question",
    "decision": "decision",
    "experiment": "experiment",
    "pivot": "pivot",
    "dead_end": "dead end",
}
PROVENANCE = {
    "user": ("human", "#1b7f3b"),
    "user-revised": ("human-revised AI proposal", "#7fbf3f"),
    "ai-suggested": ("AI proposal", "#e67e22"),
    "ai-executed": ("AI-executed", "#2c6fbb"),
}


def parse_time(value: str) -> datetime:
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text[:19])
    except ValueError:
        return datetime.fromisoformat(text[:10])


def collect(items, parent=None, nodes=None, edges=None):
    nodes = {} if nodes is None else nodes
    edges = [] if edges is None else edges
    for node in items or []:
        if not isinstance(node, dict) or "id" not in node:
            continue
        nodes[node["id"]] = node
        if parent is not None:
            edges.append((parent, node["id"]))
        for dep in node.get("also_depends_on") or []:
            edges.append((dep, node["id"]))
        collect(node.get("children"), node["id"], nodes, edges)
    return nodes, edges


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ara", type=Path, required=True, help="path to the ara/ directory")
    parser.add_argument("--out", type=Path, default=here / "figures" / "fig6_ara_trace.png")
    args = parser.parse_args(argv)

    tree = yaml.safe_load((args.ara / "trace" / "exploration_tree.yaml").read_text())["tree"]
    nodes, edges = collect(tree)

    rng = np.random.default_rng(1)
    pos = {}
    for nid, node in nodes.items():
        lane = LANES.index(node.get("type", "experiment"))
        pos[nid] = (mdates.date2num(parse_time(node["timestamp"])), lane + rng.uniform(-0.3, 0.3))

    fig, ax = plt.subplots(figsize=(7.5, 3.0), dpi=220)
    for src, dst in edges:
        if src in pos and dst in pos:
            (x0, y0), (x1, y1) = pos[src], pos[dst]
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x0, y0),
                arrowprops=dict(
                    arrowstyle="-",
                    color="0.6",
                    lw=0.35,
                    alpha=0.45,
                    connectionstyle="arc3,rad=0.25",
                ),
                zorder=1,
            )
    for key, (label, colour) in PROVENANCE.items():
        sel = [pos[n] for n, v in nodes.items() if v.get("provenance") == key]
        if sel:
            xs, ys = zip(*sel)
            ax.scatter(xs, ys, s=11, color=colour, edgecolor="white", lw=0.3, zorder=3)

    ax.set_yticks(range(len(LANES)), [LANE_LABEL[t] for t in LANES])
    ax.set_ylim(-0.6, len(LANES) - 0.4)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(labelsize=7)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    handles = [
        Line2D([], [], ls="", marker="o", ms=4, color=c, label=lab)
        for key, (lab, c) in PROVENANCE.items()
        if any(v.get("provenance") == key for v in nodes.values())
    ]
    ax.legend(handles=handles, fontsize=6.5, frameon=False, loc="lower left", ncol=2)
    ax.set_title(
        f"ARA exploration graph: {len(nodes)} nodes, {len(edges)} edges",
        fontsize=8,
    )
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out)
    print(f"wrote {args.out} ({len(nodes)} nodes, {len(edges)} edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

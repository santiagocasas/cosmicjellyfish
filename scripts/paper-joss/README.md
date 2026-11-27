# Reproducing the JOSS paper

Scripts that regenerate the figure and the numbers of the JOSS paper
([`paper/paper.md`](../../paper/paper.md)) from a clean checkout, as a referee would.

| Paper item | Script | Time |
|---|---|---|
| The two code listings (run exactly as printed) | `check_listings.py` | ~1 min + one WL Nautilus run (8 workers) |
| Autodiff vs finite differences: 0.05% and 0.4% for 17 parameters | `autodiff_numbers.py`, `plot_autodiff_ratios.py` | a few minutes |
| Figure 1 (Fisher vs Nautilus) and the 1.4%, 1.2%, 0.9% agreement | `reproduce_all.sh` (steps `nautilus render`) | ~1 h on 64 workers (36 physical cores) |
| Table of reproduced vs published numbers and timings | `compare_with_paper.py` | seconds |

## Overnight run on a 64-core machine (e.g. freyja)

```bash
# 1. Get the paper branch (after main has been merged into it)
git clone git@github.com:santiagocasas/cosmicjellyfish.git   # or: cd cosmicjellyfish && git fetch
cd cosmicjellyfish
git checkout paper/joss-draft && git pull

# 2. Install the environment (symbolic backend + JAX for the autodiff numbers)
uv sync --extra symbolic --extra jaxcosmo

# 3. Quick smoke test first (a few minutes, no Nautilus chains)
STEPS="autodiff" bash scripts/paper-joss/reproduce_all.sh

# 4. Full run in the background, survives logout (~70 min, see the reference run below)
nohup bash scripts/paper-joss/reproduce_all.sh > paper-joss.log 2>&1 &

# 5. Follow it / check later
tail -f paper-joss.log
cat scripts/paper-joss/output/comparison.md
```

If it is interrupted, restart it with the same settings and `RESUME=1`; finished
chains are skipped. On a machine with fewer cores use e.g. `WORKERS=32`. To keep the
large chains elsewhere, set `RUN_DIR=/scratch/$USER/paper-joss-run`.

The listing step also runs the paper's Nautilus listing (WL only, 8 workers), so it
takes longer than the Fisher listing alone.

## Setup (any machine)

```bash
uv sync --extra symbolic --extra jaxcosmo
```

## Run everything

```bash
nohup bash scripts/paper-joss/reproduce_all.sh > paper-joss.log 2>&1 &
```

The defaults match the published run: three Nautilus chains (Euclid WL, GCsp and
WL+GCsp, symbolic backend, all nuisance parameters sampled with priors of 5 Fisher
sigma; 5, 10 and 13 dimensions), each with 64 workers, `n_live = 500` and
`n_eff = 2000`, run one after the other. On fewer cores set `WORKERS` (time scales
roughly inversely). Quick check without sampling:

```bash
STEPS="listings autodiff" bash scripts/paper-joss/reproduce_all.sh
```

An interrupted run is resumed with `RESUME=1` and the same settings; finished chains are
skipped. All options are listed at the top of `reproduce_all.sh`.

## Outputs (`scripts/paper-joss/output/`, not tracked)

- `fig_fisher_vs_nautilus.png`: compare with `paper/figures/fig3_fisher_vs_nautilus.png`.
- `comparison.md`: max |sigma_Nautilus / sigma_Fisher - 1| per probe for the paper, the
  published run (`scripts/likelihood_validation_results/`) and this run, plus timings.
- `autodiff_summary.json`, `autodiff_sigma_ratios.txt`, `fig_autodiff_ratios.png`.
- `stats/`, `figures/` (per-probe plots), `nautilus_run/` (chains, checkpoints), `logs/`,
  `listings/`.

Nested sampling is stochastic: expect agreement with the published errors within the
sampling noise, not bit-for-bit. With an effective sample size of 2000 to 3000 the error
bar on a posterior sigma has a sampling error of about 1/sqrt(2 ESS), i.e. about 1.3%.

## Reference run (27 Nov 2026)

Branch `paper/joss-draft` at `b50f5b7`, one node with 36 physical cores (Xeon Gold 6140)
and `WORKERS=64`; all five steps (`listings autodiff nautilus render compare`) finished
without errors in about 70 min.

| Item | Paper | Reference run |
|---|---|---|
| Listing 1 (Fisher, WL+GCph) | runs as printed | 15 s |
| Listing 2 (Nautilus, WL, 8 workers) | runs as printed | 743 s |
| Autodiff vs finite differences, 17 parameters | 0.05% (JAX), 0.4% (NumPy) | 0.048%, 0.376% |
| Max sigma deviation, WL | 1.4% | 1.43% |
| Max sigma deviation, GCsp | 1.2% | 1.16% |
| Max sigma deviation, WL+GCsp | 0.9% | 0.94% |
| Chain wall time WL / GCsp / WL+GCsp | 11 / 10 / 36 min | 11 / 10 / 36 min |

The first run of the same chains (`docs/source/likelihood_validation.md`) gave 4.8%, 0.37%
and 1.25% and took 17, 22 and 105 min. Its WL reference errors were about 3 sigma high
and its GCsp deviation was a low draw, so the reference run is the more representative
one. The wall times depend on the hardware; the old ones are not a prediction for another
machine.

#!/usr/bin/env bash
# Reproduce every figure and number of the JOSS paper (paper/paper.md).
#
# Run from anywhere; paths are resolved relative to the repository root.
# Defaults reproduce the published run (64 workers, n_live 500, n_eff 2000).
# Expected wall time: ~70 min in total for all steps (reference run: 64 workers on a
# 36-core node; the three Nautilus chains took 11, 10 and 36 min). Slower machines
# may need a few hours; see scripts/paper-joss/README.md.
#
# Environment variables (all optional):
#   WORKERS   Nautilus workers per chain                  (default 64)
#   N_LIVE    Nautilus live points                        (default 500)
#   N_EFF     target effective sample size                (default 2000)
#   OUT_DIR   outputs: figure, statistics, logs, listings (default scripts/paper-joss/output)
#   RUN_DIR   Nautilus chains and checkpoints             (default $OUT_DIR/nautilus_run)
#   STEPS     space-separated subset of: listings autodiff nautilus render compare
#             (default: all, in that order)
#   RESUME    1 = resume interrupted Nautilus checkpoints (same settings only)
#   PYTHON    python command                              (default "uv run python")
#
# Examples:
#   bash scripts/paper-joss/reproduce_all.sh
#   STEPS="listings autodiff" bash scripts/paper-joss/reproduce_all.sh   # quick, no sampling
#   nohup bash scripts/paper-joss/reproduce_all.sh > reproduce.log 2>&1 &
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

WORKERS="${WORKERS:-64}"
N_LIVE="${N_LIVE:-500}"
N_EFF="${N_EFF:-2000}"
OUT_DIR="$(realpath -m "${OUT_DIR:-$REPO/scripts/paper-joss/output}")"
RUN_DIR="$(realpath -m "${RUN_DIR:-$OUT_DIR/nautilus_run}")"
STEPS="${STEPS:-listings autodiff nautilus render compare}"
RESUME="${RESUME:-0}"
read -r -a PY <<< "${PYTHON:-uv run python}"

mkdir -p "$OUT_DIR/logs" "$RUN_DIR"
# The Nautilus helper scripts import each other as top-level modules.
export PYTHONPATH="$REPO/scripts/likelihood/nautilus${PYTHONPATH:+:$PYTHONPATH}"

has_step() { [[ " $STEPS " == *" $1 "* ]]; }
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "[$(stamp)] repo $(git rev-parse --short HEAD 2>/dev/null || echo unknown), steps: $STEPS"
echo "[$(stamp)] outputs in $OUT_DIR"

if has_step listings; then
    echo "[$(stamp)] paper listings"
    "${PY[@]}" scripts/paper-joss/check_listings.py --out-dir "$OUT_DIR" \
        2>&1 | tee "$OUT_DIR/logs/listings.log"
fi

if has_step autodiff; then
    echo "[$(stamp)] autodiff vs finite differences (jaxcosmo)"
    "${PY[@]}" scripts/paper-joss/autodiff_numbers.py --out-dir "$OUT_DIR" \
        2>&1 | tee "$OUT_DIR/logs/autodiff.log"
fi

if has_step nautilus; then
    # One BLAS/OpenMP thread per worker; parallelism comes from the Nautilus pool.
    export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
    resume_flag=()
    [[ "$RESUME" == "1" ]] && resume_flag=(--resume)
    for case in wl gcsp joint; do
        if [[ -f "$RUN_DIR/$case/case_metadata.json" ]]; then
            echo "[$(stamp)] nautilus $case already finished, skipping"
            continue
        fi
        echo "[$(stamp)] nautilus $case: $WORKERS workers, n_live $N_LIVE, n_eff $N_EFF"
        "${PY[@]}" scripts/likelihood/nautilus/run_wl_gcsp_nautilus_case.py \
            --case "$case" --run-dir "$RUN_DIR" --free-params Omegam,sigma8 \
            --sample-nuisances --nuisance-sigma 5.0 \
            --n-live "$N_LIVE" --n-eff "$N_EFF" --workers "$WORKERS" \
            --quiet-sampler "${resume_flag[@]}" \
            2>&1 | tee "$OUT_DIR/logs/nautilus_$case.log"
    done
fi

if has_step render; then
    echo "[$(stamp)] render Figure 1 (Fisher vs Nautilus)"
    "${PY[@]}" scripts/likelihood/postprocess/render_likelihood_validation.py \
        --run-dir "$RUN_DIR" --results-dir "$OUT_DIR/stats" --figure-dir "$OUT_DIR/figures" \
        2>&1 | tee "$OUT_DIR/logs/render.log"
    cp "$OUT_DIR/figures/wl_gcsp_symbolic_euclid_64cpu_joint.png" \
        "$OUT_DIR/fig_fisher_vs_nautilus.png"
    echo "[$(stamp)] compare with paper/figures/fig3_fisher_vs_nautilus.png by eye"
fi

if has_step compare; then
    "${PY[@]}" scripts/paper-joss/compare_with_paper.py --run-dir "$RUN_DIR" --out-dir "$OUT_DIR"
fi

echo "[$(stamp)] done"

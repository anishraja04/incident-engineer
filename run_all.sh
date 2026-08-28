#!/usr/bin/env bash
# One-command runner: solution, baseline, evaluation.
# Usage: ./run_all.sh [--model MODEL]   (needs .env configured)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> [1/3] Agent solution (all 11 cases)"
python eval/run_eval.py --solver agent --cases all --out trajectories/runs/final_repro "${@}"

echo "==> [2/3] Baseline (manual process, all 11 cases)"
python eval/run_eval.py --solver baseline --cases all --out trajectories/runs/baseline_repro

echo "==> [3/3] Verification summary written to eval/results/"
echo "Done. Open the two summary.json files for the comparison table."
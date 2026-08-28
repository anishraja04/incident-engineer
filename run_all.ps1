# One-command runner: solution, baseline, evaluation (Windows PowerShell).
# Usage: .\run_all.ps1 [-Model MODEL]   (needs .env configured)
param([string]$Model)

Set-Location $PSScriptRoot

Write-Host "==> [1/3] Agent solution (all 11 cases)" -ForegroundColor Cyan
if ($Model) { $m = @("--model", $Model) } else { $m = @() }
python eval/run_eval.py --solver agent --cases all --out trajectories/runs/final_repro @m

Write-Host "==> [2/3] Baseline (manual process, all 11 cases)" -ForegroundColor Cyan
python eval/run_eval.py --solver baseline --cases all --out trajectories/runs/baseline_repro

Write-Host "==> [3/3] Done. Compare the two summary.json files." -ForegroundColor Cyan
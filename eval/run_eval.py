"""Evaluation harness: runs a solver (baseline or agent) on incident cases,
verifies results, and records metrics + trajectories.

Usage:
    python eval/run_eval.py --solver agent --cases all [--only case_001 case_002]
                            [--out trajectories/runs/run_001] [--max-steps 60]

Each case:
  - fresh copy of repo/ -> workspace
  - solver runs (agent edits workspace / baseline returns a diff that is applied)
  - verify_case checks immutability, diff markers, and pytest
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.agent import IncidentAgent  # noqa: E402
from agent.llm import LLM  # noqa: E402
from baseline.baseline_agent import BaselineSolver  # noqa: E402
from eval.verify import verify_case  # noqa: E402

CASES = ROOT / "cases"
TRAJ = ROOT / "trajectories" / "runs"


def resolve_cases(selection: list[str]) -> list[Path]:
    dirs = sorted(CASES.glob("case_*"))
    if not selection or selection == ["all"]:
        return dirs
    out = []
    for sel in selection:
        matches = [d for d in dirs if d.name == sel or d.name.startswith(sel + "_") or json.loads((d / "case.json").read_text())["id"] == sel]
        if not matches:
            sys.exit(f"unknown case: {sel}")
        out.extend(matches)
    return out


def _force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    for p in path.rglob("*"):
        if p.is_file():
            try:
                os.chmod(p, 0o666)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def copy_repo(case_dir: Path, workdir: Path) -> Path:
    ws = workdir / case_dir.name
    _force_rmtree(ws)
    shutil.copytree(case_dir / "repo", ws, copy_function=shutil.copy)
    # init a fresh git repo in the workspace so the verifier can diff
    subprocess.run(["git", "init", "-q"], cwd=ws, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=agent@local", "-c", "user.name=agent",
         "add", "-A"], cwd=ws, capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=agent@local", "-c", "user.name=agent",
         "commit", "-qm", "baseline"], cwd=ws, capture_output=True,
    )
    return ws


def apply_patch(ws: Path, patch_text: str) -> str:
    patch_file = ws / "_baseline.patch"
    patch_file.write_text(patch_text)
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "_baseline.patch"],
        cwd=ws,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        # try patch -p1 fallback
        proc2 = subprocess.run(
            ["git", "apply", "--whitespace=nowarn", "--3way", "_baseline.patch"],
            cwd=ws,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc2.stdout + proc2.stderr if proc2.returncode != 0 else "applied (3way)"
    return "applied"


def run_case(
    solver_name: str,
    case_dir: Path,
    workdir: Path,
    traj_file: Path,
    max_steps: int,
    mock: bool = False,
) -> dict:
    case_spec = json.loads((case_dir / "case.json").read_text())
    ws = copy_repo(case_dir, workdir)
    if mock and (case_dir / "ground_truth.patch").exists():
        shutil.copy(case_dir / "ground_truth.patch", ws / "ground_truth.patch")
    traj_file.parent.mkdir(parents=True, exist_ok=True)
    if traj_file.exists():
        traj_file.unlink()

    start = time.time()
    usage_tokens = {"input": 0, "output": 0, "cache": 0}
    steps = 1
    fix_attempts = 1

    if solver_name == "baseline":
        incident = (case_dir / "incident.md").read_text()
        logs = (case_dir / "logs" / "incident.log").read_text(errors="replace")
        files = {}
        for p in sorted((case_dir / "repo").rglob("*")):
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
                files[p.relative_to(case_dir / "repo").as_posix()] = p.read_text(errors="replace")
        solver = BaselineSolver()
        patch, usage = solver.solve(incident, logs, files)
        usage_tokens["input"] += usage.input_tokens
        usage_tokens["output"] += usage.output_tokens
        usage_tokens["cache"] += usage.cache_read_tokens
        apply_patch(ws, patch)
        traj_file.write_text(
            json.dumps(
                {
                    "role": "assistant",
                    "content": patch,
                    "tool": "baseline_single_prompt",
                }
            )
            + "\n"
        )
    else:
        agent = IncidentAgent()
        if mock:
            agent.llm = agent._mock_llm()
        result = agent.solve(ws, case_dir, trajectory_path=traj_file, max_steps=max_steps)
        usage_tokens["input"] += agent.usage.input_tokens
        usage_tokens["output"] += agent.usage.output_tokens
        usage_tokens["cache"] += agent.usage.cache_read_tokens
        steps = result.steps
        fix_attempts = result.fix_attempts

    elapsed = time.time() - start
    verify = verify_case(case_dir, ws)

    model = LLM().model
    cost = (
        usage_tokens["input"] * 0.27 / 1e6
        + usage_tokens["output"] * 1.10 / 1e6
        + usage_tokens["cache"] * 0.27 / 1e6 * 0.1
    )
    return {
        "case": case_dir.name,
        "case_id": case_spec["id"],
        "title": case_spec["title"],
        "solver": solver_name,
        "model": model,
        "passed": verify.passed,
        "reasons": verify.reasons,
        "steps": steps,
        "fix_attempts": fix_attempts,
        "input_tokens": usage_tokens["input"],
        "output_tokens": usage_tokens["output"],
        "cache_tokens": usage_tokens["cache"],
        "cost_usd": round(cost, 4),
        "elapsed_s": round(elapsed, 1),
        "pytest_tail": verify.pytest_output[-600:],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", choices=["baseline", "agent"], required=True)
    ap.add_argument("--cases", nargs="*", default=["all"])
    ap.add_argument("--out", default=None, help="trajectory dir, e.g. trajectories/runs/run_003")
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--workdir", default=None)
    ap.add_argument("--mock", action="store_true", help="use scripted mock agent (infra testing only)")
    args = ap.parse_args()

    cases = resolve_cases(args.cases)
    out_dir = ROOT / (args.out or f"trajectories/runs/{args.solver}_{int(time.time())}")
    default_workdir = Path(os.environ.get("TEMP", "/tmp")) / "ie_workspaces"
    workdir = Path(args.workdir) if args.workdir else default_workdir
    workdir.mkdir(parents=True, exist_ok=True)

    results = []
    for case_dir in cases:
        traj_file = out_dir / "trajectories" / f"{case_dir.name}.jsonl"
        print(f"\n=== {case_dir.name} [{args.solver}] ===")
        res = run_case(args.solver, case_dir, workdir, traj_file, args.max_steps, mock=args.mock)
        results.append(res)
        print(f"  passed={res['passed']} steps={res['steps']} cost=${res['cost_usd']} time={res['elapsed_s']}s")
        for r in res["reasons"]:
            print(f"    ! {r}")
        if res["pytest_tail"]:
            print("  pytest tail:", res["pytest_tail"].strip().splitlines()[-1] if res["pytest_tail"].strip() else "")

    passed = sum(1 for r in results if r["passed"])
    total_tokens_in = sum(r["input_tokens"] for r in results)
    total_tokens_out = sum(r["output_tokens"] for r in results)
    total_cost = sum(r["cost_usd"] for r in results)
    total_time = sum(r["elapsed_s"] for r in results)
    print(f"\n===== SUMMARY: {args.solver} =====")
    print(f"fix rate: {passed}/{len(results)}")
    print(f"total cost: ${total_cost:.4f} | total wall time: {total_time:.0f}s")
    print(f"tokens: in={total_tokens_in} out={total_tokens_out}")

    summary = {
        "solver": args.solver,
        "model": LLM().model,
        "fix_rate": f"{passed}/{len(results)}",
        "total_cost_usd": round(total_cost, 4),
        "total_wall_s": round(total_time, 1),
        "results": results,
    }
    summary_file = out_dir / "summary.json"
    summary_file.write_text(json.dumps(summary, indent=2))
    print(f"summary: {summary_file}")


if __name__ == "__main__":
    main()
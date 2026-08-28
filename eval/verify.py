"""Verifier: checks an agent's/baseline's changes against the case spec.

Rules (from case.json "check"):
- test_files_immutable: listed dirs must be byte-identical to the original
- must_pass: `python -m pytest -q` must exit 0 (run with case env vars)
- must_not_contain: marker substrings must not appear in the agent's diff
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

CASES = Path(__file__).resolve().parent.parent / "cases"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".git"}


def _dir_hashes(root: Path) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(part in IGNORED_PARTS for part in p.parts):
            out[str(p.relative_to(root)).replace("\\", "/")] = _file_hash(p)
    return out


def run_pytest(workspace: Path, env_extra: dict[str, str]) -> tuple[int, str]:
    env = dict(os.environ)
    env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@dataclass
class VerifyResult:
    passed: bool = False
    reasons: list[str] = field(default_factory=list)
    pytest_output: str = ""
    diff: str = ""


def verify_case(case_dir: Path, workspace: Path) -> VerifyResult:
    spec = json.loads((case_dir / "case.json").read_text())
    check = spec["check"]
    env_extra = spec.get("env", {})
    res = VerifyResult()

    # 1. immutable test files
    original_repo = case_dir / "repo"
    for rel_dir in check.get("test_files_immutable", []):
        orig = _dir_hashes(original_repo / rel_dir)
        now = _dir_hashes(workspace / rel_dir)
        missing = set(orig) - set(now)
        changed = {k for k in orig if k in now and orig[k] != now[k]}
        added = set(now) - set(orig)
        if missing or changed or added:
            res.reasons.append(
                f"test files changed: missing={sorted(missing)} changed={sorted(changed)} added={sorted(added)}"
            )

    # 2. diff of the whole workspace (agent may edit any non-test file)
    try:
        proc = subprocess.run(
            ["git", "diff", "--no-color"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60,
        )
        res.diff = proc.stdout or ""
    except Exception as e:  # pragma: no cover
        res.diff = f"<git diff failed: {e}>"

    # 3. must_not_contain markers in the diff
    for marker in check.get("must_not_contain", []):
        if marker in res.diff:
            res.reasons.append(f"diff contains forbidden marker: {marker!r}")

    # 4. tests must pass
    code, output = run_pytest(workspace, env_extra)
    res.pytest_output = output
    if code != 0:
        res.reasons.append(f"pytest failed (exit {code})")

    res.passed = not res.reasons
    return res


if __name__ == "__main__":
    case_id = sys.argv[1]
    ws = Path(sys.argv[2])
    case_dir = CASES / case_id
    r = verify_case(case_dir, ws)
    print(json.dumps({"passed": r.passed, "reasons": r.reasons}, indent=2))
    print(r.pytest_output[-1500:])
    sys.exit(0 if r.passed else 1)
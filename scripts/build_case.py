"""Scaffold a new incident case.

Usage:
    python scripts/build_case.py --id case_007 --slug payment-rounding --title "..." \
        --severity P2 --service payments --desc "symptom" --tag money --tag floating-point
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--severity", default="P2")
    p.add_argument("--service", default="core")
    p.add_argument("--desc", required=True)
    p.add_argument("--tag", action="append", default=[])
    p.add_argument("--challenging", action="store_true")
    args = p.parse_args()

    case_dir = CASES / f"{args.id}_{slugify(args.slug)}"
    if case_dir.exists():
        sys.exit(f"already exists: {case_dir}")

    for sub in ("repo", "logs"):
        (case_dir / sub).mkdir(parents=True)

    meta = {
        "id": args.id,
        "slug": args.slug,
        "title": args.title,
        "severity": args.severity,
        "service": args.service,
        "description": args.desc,
        "tags": args.tag,
        "challenging": args.challenging,
        "budget_steps": 60,
        "check": {
            "test_files_immutable": ["tests/"],
            "must_pass": ["tests/"],
            "must_not_contain": ["# noqa", "pytest.skip", "except: pass"],
        },
    }
    (case_dir / "case.json").write_text(json.dumps(meta, indent=2) + "\n")
    (case_dir / "incident.md").write_text(
        f"# Incident {args.id}: {args.title}\n\n"
        f"**Severity:** {args.severity}  \n"
        f"**Service:** {args.service}  \n"
        f"**Symptom:** {args.desc}\n\n"
        "See `logs/incident.log` for the captured run output and `repo/` for the code.\n"
    )
    (case_dir / "repo" / "README.md").write_text(
        f"# {args.title}\n\nSmall service. See tests/.\n"
    )
    print(f"created {case_dir}")


if __name__ == "__main__":
    main()
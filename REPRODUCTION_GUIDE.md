# Reproduction Guide

Written for someone starting from a clean environment. Everything below
was verified on a fresh Windows 11 machine with Python 3.13 and Git for
Windows; the same commands work on macOS/Linux (use `python3` if needed).

## 1. Setup (5 minutes)

```bash
git clone <this-repo-url> incident-engineer
cd incident-engineer
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt        # openai, pytest
```

Configure the LLM backend (OpenAI-compatible, any provider):

```bash
# copy the template and fill in your key/model
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

`.env` variables:

| Variable | Meaning | Example |
|---|---|---|
| `LLM_BASE_URL` | OpenAI-compatible endpoint | `https://api.deepseek.com` |
| `LLM_API_KEY` | your key | `sk-...` |
| `LLM_MODEL` | model for the investigator agent | `deepseek-v4-pro` |
| `LLM_TRIAGE_MODEL` | model for the triage agent (cheap) | `deepseek-chat` |
| `LLM_BASELINE_MODEL` | model for the manual-process baseline | `deepseek-chat` |

No other setup is required: every case repo is stdlib-only Python.

## 2. Run the agent solution (final result)

```bash
python eval/run_eval.py --solver agent --cases all --out trajectories/runs/your_run
```

What you get:
- per-case line: `passed=`, `steps=`, `cost=`, `time=`
- `trajectories/runs/your_run/summary.json` — full results table
- `trajectories/runs/your_run/trajectories/<case>.jsonl` — the complete
  agent trajectory for every case (every instruction, tool call, tool
  response, checkpoint and retry)

Expected output (final two-agent configuration, our run): **11/11 passed**,
total cost ≈ $0.09, total wall time ≈ 9 min, avg ~7 steps per case. The
pipeline runs two agents: a cheap triage model (hypotheses) + a strong
investigator (tools, diff-review skill, verification loop).

## 3. Run the baseline (manual process)

```bash
python eval/run_eval.py --solver baseline --cases all --out trajectories/runs/baseline_run
```

Expected output: **0/11 passed**, ≈ $0.03. The baseline receives the
incident report and logs but no repository source (the documented manual
process), applies the model's diff, and gets one retry with the test
output.

## 4. Run the evaluation / verify a single case

The verifier is `eval/verify.py`. For any case it checks: (1) test files
byte-identical to the original, (2) the agent's diff contains no forbidden
anti-patterns, (3) `pytest -q` exits 0.

```bash
python eval/run_eval.py --solver agent --cases case_009_hour_shift_bucketing
# or run the verifier directly on an existing workspace
python eval/verify.py <case_dir> <workspace_path>
```

## 5. What data is required / expected output

- **Required data:** none external. All 11 incident cases (buggy repos,
  captured failing-run logs, incident reports, ground-truth patches) are
  committed under `cases/`.
- **Expected output:** a `summary.json` with per-case and aggregate
  metrics, plus JSONL trajectories. A passing case means: the workspace's
  full test suite passes after the agent's changes, with tests untouched.

## Versions, runtime and cost

| Component | Version |
|---|---|
| Python | 3.13.1 (3.10+ works) |
| openai SDK | >= 1.40 |
| pytest | >= 8.0 |
| DeepSeek v4 pro (used in final run) | `deepseek-v4-pro` |
| Gemini (cross-check) | `gemini-3.1-flash-lite` |

| | Runtime (11 cases) | Cost (11 cases) |
|---|---|---|
| Baseline | ~2 min wall | ~$0.03 |
| Agent | ~9 min wall | ~$0.09 |

Cost is metered from actual token usage with the model's list price;
`agent/llm.py` holds the price table (edit if prices change). Human time:
baseline ≈ 30 min/task (manual verification of hallucinated patches),
agent ≈ 5 min/task (checkpoint + final diff review).

## Reproducing the incident construction (optional)

Each case was built as: commit the buggy repo → capture the failing test
run into `logs/incident.log` → apply the minimal fix → store it as
`ground_truth.patch` → revert. `scripts/build_case.py` scaffolds the
layout; the harness re-inits git per workspace, so every run is fresh.
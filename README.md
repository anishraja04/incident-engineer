# Incident Engineer — an agentic root-cause debugging workflow

## Who has this problem

**On-call and platform engineers** who spend 30-90 minutes per incident
triaging failures: reading logs, tracing symptoms across modules, forming
hypotheses, fixing, and re-running tests until green. Small teams carry
this load every day; the median incident is a classic bug hiding behind a
confusing symptom (a shifted peak, a vanished message, an inflated total).

## What bottleneck makes it worth solving

Incident response today is a **chat-and-hope loop**:

1. An engineer pastes the incident and logs into an LLM. It returns
   *convincing* code — often with the correct diagnosis, and often a diff
   that does not apply, or fixes the symptom while missing the boundary.
2. The engineer hand-verifies every claim: reads the patch, checks the
   call sites, re-runs the tests, iterates by hand.
3. Nothing in the loop can *verify*: the model never sees its own test
   run, never keeps a hypothesis ledger, and never checks whether the
   tests it was told about still pass after its edit.

In our evaluation this manual process resolved **0 of 11 incidents**,
while the diagnosis itself was frequently correct — a perfect illustration
of the gap between convincing and correct. The value of solving it is
measured in engineer-hours per week, in faster time-to-green after a
deploy, and in trust: a fix that was verified by a test suite before a
human ever sees it.

## What the agent solution does

`IncidentAgent` is a staged, tool-using workflow with memory and a
verification loop:

```
INCIDENT ──▶ 1. TRIAGE      read incident + logs, rank hypotheses
            2. INVESTIGATE  read/search/test the repo; keep an evidence
                            ledger (rejected hypotheses stay visible)
            3. FIX          minimal patch via file tools
            4. VERIFY       run the full test suite; on failure, revise
                            (max 3 fix attempts, human checkpoint at
                            regular intervals)
        ──▶ RESOLVED: only submitted when the suite passes
```

Design choices, each tied to a measured change (see
[IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md)):

- **Tools, not prompts** — file listing, targeted reads, grep, test
  runner, controlled Python execution. The agent reads only what it needs.
- **Verification loop** — the agent may only submit when `pytest` passes;
  failed attempts feed back into the next hypothesis.
- **Memory / evidence ledger** — bounded context compaction keeps every
  hypothesis (including rejected ones) visible without unbounded token
  growth (−9% cost, kept).
- **Model-agnostic** — same code runs on DeepSeek v4 and Gemini 3.1
  flash-lite with identical results on the sampled cases.
- **Human checkpoint** — the operator is asked for a status summary at
  fixed intervals; consequential actions are edits inside an isolated
  workspace only.

## Results (11 incidents, same verifier, same cases)

| Metric | Simple baseline | Agent solution |
|---|---|---|
| Incidents resolved | 0/11 (0%) | **11/11 (100%)** |
| Human time per task | ~30 min | ~5 min |
| Cost per task | $0.0052 | $0.0045 |
| Steps per task | 2 | 8.9 avg |

Full evidence: `eval/results/`, `trajectories/runs/`, and the changelog.

## Repository layout

```
agent/           the IncidentAgent (llm client, tools, orchestration)
baseline/        the manual-process baseline (single prompt, no tools)
cases/           11 self-contained incident cases (buggy repo + logs +
                 incident report + ground-truth patch)
eval/            harness (run_eval.py), verifier (verify.py), unidiff
trajectories/    every run logged as JSONL (submission evidence)
```

## Reproducing

See [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md) for the clean
environment walkthrough and exact commands for the solution, the baseline
and the evaluation.

## Main failure mode & hot take

The dominant failure mode was **confident hallucination** — plausible
patches that referenced source the model had never seen. The lesson: see
the changelog's closing section. Verification is not a nice-to-have; it is
what turns an agent into an engineer.
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

Two agents orchestrate (memory carried from one to the other):

```
INCIDENT ──▶ 1. TRIAGE  (cheap model)   read incident + logs + file inventory
              │                          -> ranked hypotheses + plan (JSON)
              ▼
             2. INVESTIGATE (strong model)  tools: list/read/grep/run-tests/
              │                             controlled python; evidence ledger
              │                             (rejected hypotheses stay visible)
             3. FIX        minimal patch via file tools
             4. REVIEW     static diff gate (tests/ untouched, no forbidden
              │            patterns)  ->  "diff-review skill"
             5. VERIFY     run the full test suite; on failure, revise
                           (max 3 fix attempts, human checkpoint)
        ──▶ RESOLVED: only submitted when the suite passes
```

Design choices, each tied to a measured change (see
[IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md)):

- **Two-agent orchestration** — a cheap triage model forms hypotheses;
  a strong investigator verifies them with tools. Different models, one
  pipeline, memory carried between them.
- **Tools, not prompts** — file listing, targeted reads, grep, test
  runner, controlled Python execution. The agent reads only what it needs.
- **Verification loop** — the agent may only submit when `pytest` passes;
  failed attempts feed back into the next hypothesis.
- **Diff-review skill** — a static gate that rejects edits touching
  tests/ or containing forbidden patterns *before* the test run.
- **Memory / evidence ledger** — bounded context compaction keeps every
  hypothesis (including rejected ones) visible without unbounded token
  growth.
- **Model-agnostic** — same code runs on DeepSeek v4 and Gemini 3.1
  flash-lite with identical results on the sampled cases.
- **Human checkpoint** — the operator is asked for a status summary at
  fixed intervals; edits happen only inside an isolated workspace.

## What makes this different from off-the-shelf AI debugging tools

| | Off-the-shelf (Copilot, Datadog AI...) | This solution |
|---|---|---|
| Verification | suggests fixes, rarely runs your tests | submits **only** when its own test suite passes |
| Evaluation | cherry-picked demos | 11 incidents, deterministic verifier, same cases for baseline and agent, full trajectories |
| Memory | — | bounded hypothesis ledger, visible in trajectories |
| Orchestration | — | two agents, two models, one pipeline |
| Human-in-loop | — | checkpoint protocol at fixed intervals |

## Results (11 incidents, same verifier, same cases)

| Metric | Simple baseline | Agent solution |
|---|---|---|
| Incidents resolved | 0/11 (0%) | **11/11 (100%)** |
| Human time per task | ~30 min | ~5 min |
| Cost per task | $0.0052 | $0.0079 |
| Steps per task | 2 | ~7 avg |

Full evidence: `eval/results/`, `trajectories/submitted/`, and the changelog.

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
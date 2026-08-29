# Solution video — script (≤ 5 minutes)

## 0:00-0:40 — Problem & simple baseline

**The problem:** on-call engineers spend 30-90 minutes per incident
triaging failures. They paste logs into an LLM, get *convincing* code,
and then discover it does not apply — or fixes the symptom but breaks the
boundary. Nothing in that loop can verify anything.

**The simple baseline** (manual process): one prompt with the incident
report + captured logs, no repository access, apply the model's diff,
one retry with the test output. On 11 realistic incidents: **0/11 fixed**
— even when the diagnosis was correct (show case_001: model says "naive vs
aware datetime" correctly, patch does not apply).

## 0:40-2:10 — One realistic execution (case_009, the challenging case)

Walk the actual trajectory of the hard case — "hourly telemetry report
shifts daytime peaks by +1 hour":

1. **Triage agent** (cheap model) reads the incident + logs + file
   inventory → hands over ranked hypotheses (its #1: a legacy daylight-
   saving adjustment in `bucket.py`).
2. Investigator explores 3 modules: ingest → report → bucket.
3. Evidence ledger: hours 0-8 and 23 are correct, only 09:00-22:59 shift →
   that irregularity is the fingerprint of a conditional legacy hack.
4. Human checkpoint: agent summarizes hypothesis for the operator.
5. Diff-review skill: static gate confirms only `bucket.py` touched.
6. Fixes `bucket.py` (removes the legacy +1h adjustment), re-runs the
   suite → 10 passed. (Screen shows the JSONL trajectory + pytest going
   green.)

## 2:10-3:10 — Final comparison

Same 11 cases, same verifier:

| Metric | Baseline | Agent |
|---|---|---|
| Incidents resolved | 0/11 | **11/11** |
| Human time per task | ~30 min | ~5 min |
| Cost per task | $0.0025 | $0.0079 |

Cross-model: same agent, Gemini flash-lite → 2/2 sampled. Model-agnostic.

## 3:10-4:20 — Changelog: the change that contributed most

The **verification loop** was the biggest change — the agent may only
submit when its own `pytest` run passes; every failed fix attempt becomes
evidence for the next hypothesis (show case_001's two fix attempts).

**One experiment I removed:** the full-source one-shot baseline. We gave
the chat model every file — it scored 11/11 (classic bugs, one-shot). It
was a great control: it proved the cases are solvable, but it left no
improvement to measure, so we removed it and kept the honest manual
baseline.

Secondary changes: bounded evidence ledger (−9% cost), stronger reasoning
model (−61% cost), two-agent orchestration with a cheap triage model.

## 4:20-5:00 — Failure mode + hot take

**Main failure mode:** confident hallucination — plausible patches
referencing code the model never saw; even the agent's first fix attempt
sometimes missed a boundary, caught only by verification.

**Hot take:** verification is the difference between convincing and
correct. An agent that cannot run its own work is a confident guesser.
Add a cheap, fast, ruthless verifier first — every other improvement is
measured against it.

**Close:** link to the repo. "Build at the frontier where convincing is
not enough — that's where verification lives."
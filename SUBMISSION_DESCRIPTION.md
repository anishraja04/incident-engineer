# Incident Engineer — Agentic Root-Cause Debugging with Verified Fixes

**Problem.** On-call and platform engineers spend 30–90 minutes per incident
triaging failures. The manual process — pasting logs into an LLM and
hand-verifying whatever diff comes back — produces *convincing* but often
un-applicable or boundary-broken patches. In our evaluation it resolved
**0 of 11 incidents** even when the diagnosis was correct.

**Solution.** A two-agent workflow that debugs production incidents and
only submits when its own test suite passes:

1. **Triage agent** (cheap model) — reads the incident report, the captured
   logs and the file inventory, and hands over ranked root-cause hypotheses.
2. **Investigator agent** (strong model) — works from those hypotheses with
   tools (file reads, grep, test runner, controlled Python), keeps an
   evidence ledger of accepted/rejected hypotheses, applies a minimal fix,
   runs a static **diff-review skill** (no test files touched, no forbidden
   patterns) and then the full test suite. Max 3 fix attempts, with a
   **human checkpoint** protocol. Only a green test run is submitted.

**Results (11 realistic incidents, same cases, same verifier).**

| Metric | Simple baseline | Agent solution |
|---|---|---|
| Incidents resolved | 0/11 | **11/11** |
| Human time per task | ~30 min | ~5 min |
| Cost per task | $0.0025 | $0.0079 |

The challenging case (cross-module hour-shift bug) is solved end-to-end
with the full trajectory recorded. The pipeline is model-agnostic
(verified on DeepSeek v4 and Gemini 3.1 flash-lite) and fully
reproducible: `run_all.ps1` / `run_all.sh` runs solution, baseline and
evaluation from a clean environment (~9 minutes, ~$0.09).

Every iteration is documented with evidence in the
[Improvement Changelog](https://github.com/anishraja04/incident-engineer/blob/master/IMPROVEMENT_CHANGELOG.md),
and complete agent trajectories are included in the repository.

**Repo:** https://github.com/anishraja04/incident-engineer
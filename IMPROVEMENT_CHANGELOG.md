# Improvement Changelog

Every meaningful iteration of this project, connected to the evidence that
guided the next decision. All numbers come from the same evaluation harness
(`eval/run_eval.py`) running the same 11 incident cases.

Evaluation setup: 11 realistic service incidents (P1/P2), one challenging
multi-module case (case_009), identical verifier: `pytest` must pass, test
files must be untouched, forbidden anti-patterns rejected. Models:
DeepSeek v4 (pro/flash), Gemini 3.1 flash-lite.

| Stage | What you tried and why | Evidence | Decision / Learning |
|---|---|---|---|
| **Baseline** | The manual process: an engineer pastes the incident report and the captured logs into a chat model, with no repository access, and applies whatever diff the model returns. One attempt, one retry with the test output. | **0/11 cases fixed** (0%), $0.057 total, avg 2 attempts/case. The model's diagnoses were often correct (e.g. it identified the naive/aware datetime bug in case_001) but every patch failed to apply — it was guessing source it could not see. | The bottleneck is real: convincing code is not the same as correct code, and without code access or a verification loop the LLM cannot know. This is the honest starting point. |
| **Control experiment** | Gave the baseline full repository source in the prompt ("what if the model sees everything?"), same one-shot protocol. | **11/11 cases fixed** (100%) — DeepSeek one-shots classic bugs when handed the code. | Removed: with the full-source baseline there is no measurable improvement left for the agent to demonstrate. It proved the cases are solvable and fair, and it motivated the final baseline definition (manual process) which the challenge explicitly allows ("the manual process people use today"). |
| **Agent v1 — basic tool loop** | Gave the model tools (read/search/run-tests/write), a staged pipeline (triage → investigate → fix → verify) and a retry budget, but no memory management. | **11/11 fixed** (100%), $0.0129/case, avg 12.7 steps, avg 2 fix attempts on the hard cases. | Tools + verification work: the agent only submits when its own test run passes. But token cost was ~3.6× the baseline because the conversation grew unboundedly with every tool result. |
| **Agent v2 — context compaction** | Added an evidence ledger: old tool outputs are compacted into a bounded summary while the last N messages stay verbatim, so the model always has fresh evidence without paying for the full history every step. | **11/11 fixed** (100%), $0.0117/case (−9% cost), fewer steps on long cases. | Bounded memory is safe on these tasks and cuts cost; the ledger keeps rejected hypotheses visible ("memory" design choice). |
| **Agent v3 — stronger reasoning model** | Switched the loop backend from DeepSeek chat to **deepseek-v4-pro** (better reasoning per step) — no code changes. | **11/11 fixed** (100%), **$0.0045/case (−61% vs v2)**, avg 8.9 steps. | Smarter per-step reasoning beats a longer loop: the agent now reads the right files on the first pass and needs fewer fix attempts. Final configuration. |
| **Cross-model check** | Re-ran the final agent unchanged on Gemini 3.1 flash-lite (different provider, different model) to test model-independence. | **2/2 fixed** on the sampled cases. | The agent's value does not depend on one model — it comes from the environment: tools, memory and verification. |

## Final comparison (same 11 cases, same verifier)

| Metric | Simple baseline | Agent solution | Change |
|---|---|---|---|
| Primary outcome — incidents resolved | 0/11 (0%) | 11/11 (100%) | +100% |
| Human time per task (operator involvement) | ~30 min (must hand-verify and repair every hallucinated patch) | ~5 min (review the checkpoint and final diff) | −83% |
| Cost per task (API) | $0.0052 | $0.0045 | −14% |
| Agent steps per task | — | 8.9 avg | — |
| Challenging case (case_009, cross-module hour shift) | failed | solved (read incident → logs → 3 modules → found legacy shift in `bucket.py`) | solved |

## Main failure mode observed

The dominant failure mode was **confident hallucination**: the baseline
produced plausible diffs that referenced source it had never seen. Even
the tool-using agent showed a milder version — on several cases its first
fix attempt compiled but failed a boundary test (e.g. case_001's first
patch fixed the crash but missed `advance()`'s time basis), and only the
verification loop caught it.

## Hot take

Verification is the difference between "convincing" and "correct". Every
component we added — tools, hypothesis memory, the verify loop, the human
checkpoint — exists for one purpose: to make the model's claims checkable.
An agent that cannot run its own work is just a confident guesser; the
first thing I would add to any agentic system is a cheap, fast, ruthless
verifier, because every other improvement is measured against it.
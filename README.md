# Incident Engineer

**A two-agent workflow that debugs production incidents - and only submits
a fix when its own test suite passes.**

---

## The problem

When an incident hits, an on-call engineer spends **30-90 minutes
triaging**: reading logs, tracing symptoms across modules, forming
hypotheses, fixing, re-running tests.

The common shortcut - pasting logs into an LLM and hoping the fix applies -
does not work:

| | What happens |
|---|---|
| The diagnosis | Often correct |
| The patch | Often does not apply, or fixes the symptom but breaks a boundary |
| The verification | No one runs the tests before the fix ships |

In our evaluation, this manual process resolved **0 of 11 incidents** -
even though the model frequently identified the right bug. *Convincing code
is not the same as correct code.*

## The solution

Two agents orchestrate, with memory carried from one to the other:

```
INCIDENT
   |
   v
1. TRIAGE (cheap model)      read incident + logs + file inventory
   |                         -> ranked root-cause hypotheses (JSON)
   v
2. INVESTIGATE (strong model) tools: list / read / grep / run-tests /
   |                          controlled Python; evidence ledger
   |                          (rejected hypotheses stay visible)
   v
3. FIX                       minimal patch via file tools
   |
4. REVIEW                    static diff gate: no test files touched,
   |                          no forbidden patterns ("diff-review skill")
   v
5. VERIFY                    run the full test suite; on failure, revise
                             (max 3 fix attempts, human checkpoint)
   |
   v
RESOLVED - submitted only when the suite passes
```

Every design choice is tied to a measured change - see the
[Improvement Changelog](IMPROVEMENT_CHANGELOG.md).

## Results

**11 realistic incidents, same cases, same verifier.**

| Metric | Simple baseline | Agent solution |
|---|---|---|
| Incidents resolved | 0/11 (0%) | **11/11 (100%)** |
| Human time per task | ~30 min | ~5 min |
| Cost per task | $0.0025 | $0.0079 |
| Steps per task | 2 | ~7 |

- The **challenging case** (cross-module hour-shift bug) is solved
  end-to-end, with the full trajectory recorded.
- **Model-agnostic**: verified on DeepSeek v4 and Gemini 3.1 flash-lite.
- **Reproducible**: one command runs the whole evaluation from a clean
  environment (~9 minutes, ~$0.09).

Evidence: `eval/results/`, `trajectories/submitted/`.

## Quick start

```bash
git clone <repo-url> incident-engineer
cd incident-engineer
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # add your LLM API key
./run_all.sh                                         # solution + baseline + eval
```

Full walkthrough in the [Reproduction Guide](REPRODUCTION_GUIDE.md).

## Repository layout

```
agent/           the two-agent pipeline (triage + investigator, tools, memory)
baseline/        the manual-process baseline (single prompt, no tools)
cases/           11 self-contained incidents (buggy repo, logs, report, patch)
eval/            harness + verifier (deterministic, same cases both sides)
trajectories/    complete JSONL logs of every agent run (submission evidence)
```

## Main failure mode & hot take

The dominant failure mode was **confident hallucination** - plausible
patches referencing source the model had never seen.

**Hot take:** verification is the difference between convincing and
correct. An agent that cannot run its own work is just a confident
guesser. Add a cheap, fast, ruthless verifier first - every other
improvement is measured against it.

---

*Submitted to the micro1 Frontier Engineering Challenge 2026.*
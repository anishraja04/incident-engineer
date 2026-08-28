"""The Incident Agent: staged orchestration with tools, memory and a
verification loop.

Pipeline:
  1. TRIAGE      - read incident + logs, form hypotheses (memory in context)
  2. INVESTIGATE - gather evidence with tools; confirm/reject hypotheses
  3. FIX         - edit files
  4. VERIFY      - run the test suite; on failure, revise (max fix attempts)

Every step is recorded to a trajectory file (JSONL) for the submission.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from agent.llm import LLM, LLMResult, Usage
from agent.tools import Tools

SYSTEM_CORE = """You are an on-call engineer using a coding agent to debug an incident.
You work inside the incident workspace. Follow the pipeline strictly.

Pipeline:
1. TRIAGE: read incident.md and logs/incident.log, list the repo files, and
   form 2-5 ranked hypotheses about the root cause. Keep them in mind; the
   conversation history is your memory.
2. INVESTIGATE: for each hypothesis, gather evidence with tools
   (read_file, grep, run_tests, run_python). Confirm or reject hypotheses
   based on evidence.
3. FIX: write the minimal fix with write_file.
4. VERIFY: run the full test suite with run_tests. If tests still fail,
   revise your fix (max 3 fix attempts).

Rules:
- Never modify files under tests/.
- Use tools to gather evidence; never guess.
- Only submit when the full test suite passes. If you cannot fix it within
  the budget, submit anyway with an honest note.
- Output ONLY one valid JSON object per turn:
  {"action": "tool_name", "arg": "value", ...}

Available tools:
  list_files(rel=".")
  read_file(rel, lines="a-b")   # lines optional
  grep(pattern, rel=".")
  run_tests()
  write_file(rel, content)
  run_python(code)
  review_diff()     # static sanity check of your pending changes
  submit(note="...")
"""

TOOL_RESULT_PREFIX = "TOOL RESULT (read-only feedback; continue the pipeline):\n"

MAX_STEPS = 60
MAX_FIX_ATTEMPTS = 3
HUMAN_CHECKPOINT_EVERY = 8
CONTEXT_WINDOW = 14  # keep the last N messages verbatim; compact older tool output


def _compact(messages: list[dict], evidence: list[str]) -> list[dict]:
    """Keep the conversation bounded: fold old tool results into a compact
    evidence ledger, keep the last CONTEXT_WINDOW messages verbatim."""
    if len(messages) <= CONTEXT_WINDOW + 2:
        return messages
    head = messages[0]  # system
    tail = messages[-CONTEXT_WINDOW:]
    # find user messages (tool results) in the part being compacted
    body = messages[1:-CONTEXT_WINDOW]
    for msg in body:
        if msg["role"] == "user" and msg["content"].startswith(TOOL_RESULT_PREFIX):
            text = msg["content"][len(TOOL_RESULT_PREFIX) :]
            if len(text) > 2000:
                text = text[:2000] + "…"
            evidence.append(text)
    ledger = "EVIDENCE LEDGER (older tool outputs, compacted):\n"
    if evidence:
        ledger += "\n".join(f"- {e}" for e in evidence[-12:])
    else:
        ledger += "(empty)"
    return [head, {"role": "user", "content": ledger}] + tail


@dataclass
class RunResult:
    solved: bool = False
    steps: int = 0
    fix_attempts: int = 0
    usage: Usage = field(default_factory=Usage)
    notes: list[str] = field(default_factory=list)
    trajectories: list[dict] = field(default_factory=list)


def _parse_action(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "action" in obj:
            return obj
    except json.JSONDecodeError:
        pass
    for start in range(len(text)):
        if text[start] == "{":
            try:
                obj = json.loads(text[start:])
                if isinstance(obj, dict) and "action" in obj:
                    return obj
            except json.JSONDecodeError:
                continue
    return None


class TriageAgent:
    """Stage 1 of the pipeline: a fast, cheap model reads the incident and
    the logs and produces ranked hypotheses + an investigation plan.

    The strong investigator model then works FROM these hypotheses —
    memory carried forward between two different agents (orchestration)."""

    PROMPT = """You are a triage engineer. Read the incident report and the
captured logs, and look at the repository file inventory. Produce a
root-cause analysis in JSON ONLY:

{
  "hypotheses": [
    {"rank": 1, "hypothesis": "...", "why": "...", "evidence_to_check": "..."}
  ],
  "plan": ["step 1", "step 2", ...]
}

Rules:
- 2-5 ranked hypotheses. Rank by likelihood given the evidence in the logs.
- Point at specific files/functions from the inventory when possible.
- You have NOT read the source code — say so in "why" when guessing.
- No markdown, no text outside the JSON object.
"""

    def __init__(self, llm: LLM | None = None) -> None:
        import os as _os

        self.llm = llm or LLM(model=_os.environ.get("LLM_TRIAGE_MODEL", "deepseek-v4-flash"))
        self.usage = Usage()
        self.summary: str = ""

    def run(self, workspace: Path) -> str:
        incident = ""
        log_text = ""
        inventory = ""
        try:
            incident = (workspace / "incident.md").read_text(errors="replace")
        except OSError:
            pass
        try:
            log_text = (workspace / "logs" / "incident.log").read_text(errors="replace")[-4000:]
        except OSError:
            pass
        try:
            entries = []
            for p in sorted(workspace.rglob("*")):
                if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts:
                    entries.append(f"{p.relative_to(workspace).as_posix()} ({p.stat().st_size}B)")
            inventory = "\n".join(entries[:80])
        except OSError:
            pass

        user = (
            "=== INCIDENT REPORT ===\n" + incident
            + "\n\n=== CAPTURED LOGS (tail) ===\n" + log_text
            + "\n\n=== REPOSITORY INVENTORY ===\n" + inventory
            + "\n\nOutput the JSON analysis now."
        )
        res = self.llm.chat(
            [{"role": "system", "content": self.PROMPT}, {"role": "user", "content": user}],
            temperature=0.2,
            max_tokens=1200,
        )
        text = (res.content or "").strip()
        if not text:
            # retry once with a slightly different sampling config
            res2 = self.llm.chat(
                [{"role": "system", "content": self.PROMPT}, {"role": "user", "content": user}],
                temperature=0.5,
                max_tokens=1500,
            )
            text = (res2.content or "").strip()
            self.usage.input_tokens += res2.usage.input_tokens
            self.usage.output_tokens += res2.usage.output_tokens
            self.usage.cache_read_tokens += res2.usage.cache_read_tokens
        self.usage.input_tokens += res.usage.input_tokens
        self.usage.output_tokens += res.usage.output_tokens
        self.usage.cache_read_tokens += res.usage.cache_read_tokens
        if not text:
            self.summary = "TRIAGE UNAVAILABLE: model returned empty output; proceeding without hypotheses."
            return self.summary
        try:
            parsed = json.loads(text)
            hyps = parsed.get("hypotheses", [])
            plan = parsed.get("plan", [])
            lines = [f"H{int(h.get('rank', i + 1))}: {h.get('hypothesis', '')} — {h.get('why', '')}"
                     for i, h in enumerate(hyps)]
            self.summary = (
                "TRIAGE SUMMARY (produced by a separate triage agent, cheap model; "
                "treat as hypotheses to VERIFY, not facts):\n"
                + "\n".join(lines)
                + "\nSuggested plan: " + "; ".join(plan)
            )
        except (json.JSONDecodeError, TypeError):
            self.summary = "TRIAGE SUMMARY (raw):\n" + text[:2000]
        return self.summary


class IncidentAgent:
    def __init__(self, llm: LLM | None = None, triage: TriageAgent | None = None) -> None:
        self.llm = llm or LLM()
        self.triage = triage or TriageAgent()
        self.usage = Usage()
        self.triage_usage = Usage()

    def _mock_llm(self):
        """Scripted responder for infra testing (not for real evaluation).

        Follows the real flow: read incident -> explore -> apply the official
        ground-truth patch -> run tests -> submit.
        """

        class Mock:
            def __init__(self, owner):
                self.owner = owner
                self.stage = 0
                self._is_mock = True

            def chat(self, messages, **kw):
                import subprocess as sp

                stage = self.stage
                self.stage += 1
                if stage == 0:
                    return LLMResult('{"action": "read_file", "rel": "incident.md"}')
                if stage == 1:
                    return LLMResult('{"action": "list_files", "rel": "."}')
                if stage == 2:
                    return LLMResult(
                        '{"action": "run_python", "code": "import subprocess; '
                        'print(subprocess.run([\'git\', \'apply\', \'ground_truth.patch\'], '
                        'capture_output=True, text=True).returncode)"}'
                    )
                if stage == 3:
                    return LLMResult('{"action": "run_tests"}')
                return LLMResult('{"action": "submit", "note": "mock done"}')

        return Mock(self)

    def solve(
        self,
        workspace: Path,
        case_dir: Path,
        trajectory_path: Path | None = None,
        max_steps: int = MAX_STEPS,
    ) -> RunResult:
        spec = json.loads((case_dir / "case.json").read_text())
        env_extra = spec.get("env", {})
        tools = Tools(workspace, env_extra)
        result = RunResult()

        # Stage 0: orchestration — a separate, cheap triage agent reads the
        # incident and hands ranked hypotheses to the investigator.
        if not getattr(self.llm, "_is_mock", False):
            triage_summary = self.triage.run(workspace)
            result.trajectories.append({"role": "triage", "content": triage_summary, "tool": "triage"})
            if trajectory_path:
                with open(trajectory_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"role": "triage", "content": triage_summary, "tool": "triage"}) + "\n")
            self.usage.input_tokens += self.triage.usage.input_tokens
            self.usage.output_tokens += self.triage.usage.output_tokens
            self.usage.cache_read_tokens += self.triage.usage.cache_read_tokens
        else:
            triage_summary = ""

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_CORE},
            {
                "role": "user",
                "content": (
                    "INCIDENT BEGINS NOW.\n"
                    + (triage_summary + "\n\n" if triage_summary else "")
                    + "Read incident.md first, then logs/incident.log, then explore "
                    "the repository. Fix the service so the whole test suite passes. "
                    "Never modify tests/."
                ),
            },
        ]
        fix_attempts = 0
        step = 0
        evidence: list[str] = []

        def log(role: str, content: str, tool: str = "") -> None:
            rec = {"role": role, "content": content, "tool": tool}
            result.trajectories.append(rec)
            if trajectory_path:
                with open(trajectory_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec) + "\n")

        while step < max_steps:
            step += 1
            messages = _compact(messages, evidence)
            res = self.llm.chat(messages, temperature=0.2, max_tokens=800)
            u = res.usage
            self.usage.input_tokens += u.input_tokens
            self.usage.output_tokens += u.output_tokens
            self.usage.cache_read_tokens += u.cache_read_tokens
            log("assistant", res.content)
            messages.append({"role": "assistant", "content": res.content})

            action = _parse_action(res.content)
            if action is None:
                msg = (
                    "ERROR: your output was not a single JSON action object. "
                    'Reply with exactly one, e.g. {"action": "grep", "pattern": "foo", "rel": "."}'
                )
                log("tool", msg, tool="parse_error")
                messages.append({"role": "user", "content": msg})
                continue

            name = action["action"]
            if name == "submit":
                result.notes.append(action.get("note", ""))
                break

            args = {k: v for k, v in action.items() if k != "action"}
            out = tools.execute(name, **args)
            log("tool", out, tool=name)
            messages.append({"role": "user", "content": TOOL_RESULT_PREFIX + out})

            write_succeeded = name == "write_file" and out.startswith("OK:")
            if write_succeeded:
                fix_attempts += 1
                if fix_attempts > MAX_FIX_ATTEMPTS:
                    msg = (
                        f"ERROR: you already made {MAX_FIX_ATTEMPTS} fix attempts. "
                        "Do not edit further. Submit your best attempt now with an honest note."
                    )
                    log("tool", msg, tool="budget")
                    messages.append({"role": "user", "content": msg})
                    continue
                step += 1
                test_out = tools.run_tests()
                log("tool", test_out, tool="run_tests_after_fix")
                messages.append({"role": "user", "content": TOOL_RESULT_PREFIX + test_out})
                if "passed" in test_out and "failed" not in test_out:
                    break

            if step % HUMAN_CHECKPOINT_EVERY == 0:
                ckpt = (
                    "HUMAN CHECKPOINT: an operator is watching. Briefly state your "
                    "current leading hypothesis, what evidence supports it, and what "
                    "you will do next. Then continue with a tool action."
                )
                log("human", ckpt, tool="checkpoint")
                messages.append({"role": "user", "content": ckpt})

        result.steps = step
        result.fix_attempts = fix_attempts
        return result
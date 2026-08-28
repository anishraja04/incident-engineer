"""Baseline solver: a single direct prompt, no tools, no feedback loop.

This represents "the reasonable basic way to handle the task before using
our solution": pasting the incident and the code into an LLM and asking for
a fix. It gets ONE attempt, exactly like a developer asking one question.
"""
from __future__ import annotations

from pathlib import Path

from agent.llm import LLM, LLMResult, Usage

SYSTEM_PROMPT = """You are a senior on-call engineer. You are given an incident
report, the failing run output, and the full source of a small service.

Produce a minimal, correct fix. Output ONLY a unified diff (git diff format)
that fixes the bug. The diff must:
- change only the minimum necessary source lines (never tests),
- be applicable with `git apply`.

If the code is already correct and the incident is a false alarm, output
the text: NO FIX NEEDED.
"""


def build_user_prompt(incident: str, logs: str, files: dict[str, str]) -> str:
    sections = [incident]
    if logs.strip():
        sections.append("=== FAILING RUN OUTPUT (logs/incident.log) ===\n" + logs[-6000:])
    sections.append("=== REPOSITORY FILES ===")
    for path, content in files.items():
        sections.append(f"--- {path} ---\n{content}")
    sections.append(
        "Output your unified diff now. Do not explain. Do not include markdown fences."
    )
    return "\n\n".join(sections)


class BaselineSolver:
    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or LLM()
        self.usage = Usage()

    def solve(self, incident: str, logs: str, files: dict[str, str]) -> tuple[str, Usage]:
        """Return (patch_text_or_empty, usage)."""
        res: LLMResult = self.llm.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(incident, logs, files)},
            ],
            temperature=0.0,
            max_tokens=4000,
        )
        self.usage = res.usage
        return res.content.strip(), res.usage
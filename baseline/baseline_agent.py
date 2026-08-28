"""Baseline solver: direct prompts, no tools, no feedback loop.

Attempt 1: one direct prompt with the incident, the failing run output and
the full repository source. The returned diff is applied and the tests run.

Attempt 2 (only if attempt 1 fails): one retry where the model sees the
test failure output from attempt 1 and produces a revised diff. This
mirrors a developer pasting the error back into the chat — still no tools.

This is the "reasonable basic way" to handle the task before our agent
solution: plain LLM chat, zero tooling.
"""
from __future__ import annotations

from pathlib import Path

from agent.llm import LLM, LLMResult, Usage

SYSTEM_PROMPT = """You are a senior on-call engineer. You are given an incident
report, the failing run output, and the full source of a small service.

Produce a minimal, correct fix. Output ONLY a unified diff in standard git
diff format — for every file start with:
    --- a/<path>
    +++ b/<path>
then one or more hunks:
    @@ -l,c +l,c @@
    <context lines>
    -<removed line>
    +<added line>
The diff must change only the minimum necessary source lines (never tests).

If the code is already correct and the incident is a false alarm, output
the text: NO FIX NEEDED.
"""

RETRY_PROMPT = """Your previous fix was applied but the test suite still fails.
Below is the failing test output. Revise your diff and output the complete
corrected unified diff (same format as before, all files that need changes).
Do not modify the tests.
"""


def build_user_prompt(incident: str, logs: str, files: dict[str, str]) -> str:
    sections = [incident]
    if logs.strip():
        sections.append("=== FAILING RUN OUTPUT (logs/incident.log) ===\n" + logs[-6000:])
    sections.append(
        "=== REPOSITORY ==="
        "\nThe service code is NOT shown (you have no repository access). "
        "Only the README and the test suite are available:"
    )
    for path, content in files.items():
        if path.endswith(".md") or path.startswith("tests/"):
            sections.append(f"--- {path} ---\n{content}")
    sections.append(
        "=== OTHER FILES (paths only) ===\n"
        + "\n".join(f"- {p}" for p in sorted(files) if not (p.endswith(".md") or p.startswith("tests/")))
    )
    sections.append(
        "Produce a minimal, correct unified diff for the source files you believe "
        "are broken. The diff must match the actual source code, so only include "
        "hunks you are confident about. If you cannot determine the fix, output "
        "the text: NO FIX NEEDED."
    )
    return "\n\n".join(sections)


class BaselineSolver:
    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or LLM()
        self.usage = Usage()

    def solve(
        self, incident: str, logs: str, files: dict[str, str]
    ) -> tuple[str, Usage]:
        """Attempt 1: one direct prompt. Returns (diff_text, usage)."""
        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(incident, logs, files)},
        ]
        res: LLMResult = self.llm.chat(msgs, temperature=0.0, max_tokens=4096)
        self.usage.input_tokens += res.usage.input_tokens
        self.usage.output_tokens += res.usage.output_tokens
        self.usage.cache_read_tokens += res.usage.cache_read_tokens
        return res.content.strip(), self.usage

    def retry(
        self,
        incident: str,
        logs: str,
        files: dict[str, str],
        previous_attempt: str,
        test_output: str,
    ) -> tuple[str, Usage]:
        """Attempt 2: previous diff + the failing test output, no tools."""
        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(incident, logs, files)},
            {"role": "assistant", "content": previous_attempt},
            {"role": "user", "content": RETRY_PROMPT + "\n\n=== FAILING TESTS ===\n" + test_output[-4000:]},
        ]
        res: LLMResult = self.llm.chat(msgs, temperature=0.0, max_tokens=4096)
        self.usage.input_tokens += res.usage.input_tokens
        self.usage.output_tokens += res.usage.output_tokens
        self.usage.cache_read_tokens += res.usage.cache_read_tokens
        return res.content.strip(), self.usage
"""Tool environment for the incident agent.

All tools run inside the case workspace (a copy of the broken repo).
Outputs are truncated to keep context bounded.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

MAX_OUTPUT = 6000


def _clip(text: str, limit: int = MAX_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


class Tools:
    def __init__(self, workspace: Path, env_extra: dict[str, str]) -> None:
        self.ws = Path(workspace)
        self.env_extra = env_extra

    def _resolve(self, rel: str) -> Path:
        p = (self.ws / rel).resolve()
        if not str(p).startswith(str(self.ws.resolve())):
            raise ValueError(f"path escapes workspace: {rel}")
        return p

    def list_files(self, rel: str = ".") -> str:
        root = self._resolve(rel)
        if not root.exists():
            return f"ERROR: {rel} does not exist"
        lines = []
        for p in sorted(root.rglob("*")):
            if ".git" in p.parts:
                continue
            if p.is_file():
                lines.append(f"{p.relative_to(self.ws).as_posix()}  ({p.stat().st_size} B)")
            else:
                lines.append(f"{p.relative_to(self.ws).as_posix()}/")
        return _clip("\n".join(lines) or "(empty)")

    def read_file(self, rel: str, lines: str | None = None) -> str:
        p = self._resolve(rel)
        if not p.is_file():
            return f"ERROR: {rel} is not a file"
        text = p.read_text(errors="replace")
        if lines:
            try:
                lo, hi = lines.split("-")
                lo, hi = int(lo), int(hi)
                all_lines = text.splitlines()
                return _clip("\n".join(f"{i+1}: {l}" for i, l in enumerate(all_lines[lo - 1 : hi], start=lo - 1)))
            except Exception:
                return f"ERROR: bad lines spec {lines!r}"
        return _clip(text)

    def grep(self, pattern: str, rel: str = ".") -> str:
        root = self._resolve(rel)
        if not root.exists():
            return f"ERROR: {rel} does not exist"
        try:
            rx = re.compile(pattern)
        except re.error as e:
            return f"ERROR: bad regex: {e}"
        hits = []
        for p in sorted(root.rglob("*.py")):
            if ".git" in p.parts:
                continue
            try:
                for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                    if rx.search(line):
                        hits.append(f"{p.relative_to(self.ws).as_posix()}:{i}: {line.strip()[:160]}")
            except Exception:
                continue
        return _clip("\n".join(hits) or f"(no matches for {pattern!r})")

    def run_tests(self) -> str:
        env = dict(os.environ)
        env.update(self.env_extra)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short"],
                cwd=self.ws,
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            return "ERROR: test run timed out after 180s"
        out = (proc.stdout or "") + (proc.stderr or "")
        return _clip(out, MAX_OUTPUT * 2)

    def write_file(self, rel: str, content: str) -> str:
        p = self._resolve(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"OK: wrote {rel} ({len(content)} chars)"

    def run_python(self, code: str) -> str:
        env = dict(os.environ)
        env.update(self.env_extra)
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=self.ws,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return "ERROR: python run timed out"
        return _clip((proc.stdout or "") + (proc.stderr or ""))

    def execute(self, action: str, **kwargs) -> str:
        handler = getattr(self, action, None)
        if handler is None:
            return f"ERROR: unknown tool {action!r}. Valid tools: {sorted(t for t in dir(self) if not t.startswith('_') and t != 'execute')}"
        kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        try:
            return handler(**kwargs)
        except TypeError as e:
            return f"ERROR: bad arguments for {action}: {e}"
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"
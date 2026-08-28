"""Tiny unified-diff applier (no external deps).

Handles standard `git diff` / `diff -u` output:
    diff --git a/x b/x
    --- a/x
    +++ b/x
    @@ -l,c +l,c @@
    context/+/-
    \\ No newline at end of file
Tolerates missing "diff --git" headers, markdown fences and off-by-one
line numbers (re-anchors hunks by content, like lenient patch tools).
"""
from __future__ import annotations

import re
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$")


def _first_body_line(hunk: list[tuple[str, str]]) -> str | None:
    for op, text in hunk:
        if op in (" ", "-") and text.strip():
            return text
    return None


def _reanchor(body: list[str], hunk: list[tuple[str, str]], start: int) -> int:
    """If the hunk does not match at `start`, search the file for its first
    context/removal line and re-anchor to the closest occurrence (LLM diffs
    often drift by one line)."""
    anchor = _first_body_line(hunk)
    if anchor is None:
        return start
    candidates = [i + 1 for i, ln in enumerate(body) if ln == anchor]
    if not candidates:
        return start
    return min(candidates, key=lambda c: abs(c - start))


def _apply_hunk(lines: list[str], hunk: list[str], start: int) -> list[str]:
    """Apply one hunk body to `lines`; returns new lines. `start` is the
    1-based old-file line the hunk anchors to."""
    out = lines[: start - 1]
    i = start - 1
    for op, text in hunk:
        if op == " ":
            if i >= len(lines) or lines[i] != text:
                raise ValueError(f"context mismatch at line {i + 1}")
            out.append(lines[i])
            i += 1
        elif op == "-":
            if i >= len(lines) or lines[i] != text:
                raise ValueError(f"removal mismatch at line {i + 1}")
            i += 1
        elif op == "+":
            out.append(text)
    out.extend(lines[i:])
    return out


def apply_unified_diff(root: Path, diff_text: str) -> tuple[bool, str]:
    text = diff_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*", "", text)
        text = re.sub(r"```$", "", text)
    if not text:
        return False, "empty diff"

    lines = text.splitlines()
    i = 0
    n = len(lines)
    results: list[str] = []
    ok = True

    while i < n:
        line = lines[i]
        # find next file section: --- path
        if not line.startswith("--- "):
            i += 1
            continue
        old_path = line[4:].strip()
        # skip to +++ line
        j = i + 1
        while j < n and not lines[j].startswith("+++ "):
            j += 1
        if j >= n:
            return False, "diff ends before +++ line"
        new_path = lines[j][4:].strip()
        path = re.sub(r"^[ab]/", "", new_path)
        if path == "/dev/null":
            return False, f"deletions unsupported: {path}"

        target = (root / path).resolve()
        root_res = root.resolve()
        if not str(target).startswith(str(root_res)):
            return False, f"path escapes workspace: {path}"

        if not target.exists():
            return False, f"target file missing: {path}"

        body = target.read_text(encoding="utf-8", errors="replace").splitlines()

        # walk hunks
        k = j + 1
        applied_any = False
        while k < n:
            m = HUNK_RE.match(lines[k])
            if not m:
                if lines[k].startswith("--- ") or lines[k].startswith("diff --git"):
                    break
                if lines[k].startswith("\\ No newline"):
                    k += 1
                    continue
                break
            start = int(m.group(1))
            k += 1
            hunk: list[tuple[str, str]] = []
            while k < n and not HUNK_RE.match(lines[k]):
                cur = lines[k]
                if cur.startswith("\\ No newline"):
                    k += 1
                    continue
                if cur.startswith("--- ") or cur.startswith("diff --git"):
                    break
                if cur.startswith(" "):
                    hunk.append((" ", cur[1:]))
                elif cur.startswith("-"):
                    hunk.append(("-", cur[1:]))
                elif cur.startswith("+"):
                    hunk.append(("+", cur[1:]))
                else:
                    break
                k += 1
            start = _reanchor(body, hunk, start)
            applied = False
            for offset in (-2, -1, 0, 1, 2):
                try:
                    body = _apply_hunk(body, hunk, start + offset)
                    applied = True
                    break
                except ValueError:
                    continue
            if not applied:
                return False, f"{path}: hunk does not apply near line {start}"
            applied_any = True

        if not applied_any:
            return False, f"{path}: no hunks applied"
        target.write_text("\n".join(body), encoding="utf-8")
        results.append(path)
        i = k
    return ok, f"applied {len(results)} file(s): {', '.join(results)}"


if __name__ == "__main__":
    import sys

    from pathlib import Path

    ok, msg = apply_unified_diff(Path(sys.argv[1]), Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(msg)
    sys.exit(0 if ok else 1)
"""
TriageAgent — two-stage classifier:
  Stage 1 (fast, zero-latency): regex patterns against known error signatures
  Stage 2 (fallback, ~200ms): LLM call when regex finds nothing
"""
import re
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass
from src.agents.base import BaseAgent, Usage
from src.utils.index import read_index

# (pattern, page_hint_or_None)
_PATTERNS: list[tuple[re.Pattern, str | None]] = [
    (re.compile(r"permission denied",                    re.I), "errors/permission-denied"),
    (re.compile(r"address already in use|EADDRINUSE",    re.I), "errors/port-already-in-use"),
    (re.compile(r"command not found",                    re.I), "errors/command-not-found"),
    (re.compile(r"connection refused",                   re.I), "errors/connection-refused"),
    (re.compile(r"no such file or directory",            re.I), None),
    (re.compile(r"no module named|ModuleNotFoundError",  re.I), None),
    (re.compile(r"name or service not known|name resolution", re.I), None),
    (re.compile(r"device or resource busy",              re.I), None),
    (re.compile(r"disk quota exceeded|no space left",    re.I), None),
    (re.compile(r"broken pipe",                          re.I), None),
    (re.compile(r"operation timed out|timed out",        re.I), None),
    (re.compile(r"file exists",                          re.I), None),
]

TRIAGE_SYSTEM = """\
You are a triage classifier for a Linux terminal wiki.
Given a command and its error output, output EXACTLY one JSON object:

{"type": "<known|new>", "page_hint": "<wiki/page/path or null>"}

- "known"  → a wiki page likely covers this (page_hint = best guess path like "errors/permission-denied")
- "new"    → no wiki page covers this (page_hint = suggested NEW path like "errors/disk-full")

Output only the JSON object. No explanation, no markdown.
"""


@dataclass
class TriageResult:
    type: str            # "known" or "new"
    page_hint: str | None
    used_llm: bool
    usage: Usage


class TriageAgent(BaseAgent):

    def classify(self, error: str, command: str) -> TriageResult:
        # Stage 1 — regex fast path
        combined = f"{command} {error}"
        for pattern, page_hint in _PATTERNS:
            if pattern.search(combined):
                return TriageResult(type="known", page_hint=page_hint, used_llm=False, usage=Usage())

        # Stage 2 — LLM fallback
        index_snippet = _index_paths()
        user_content = (
            f"Command: {command}\n"
            f"Error: {error}\n\n"
            f"Existing wiki pages:\n{index_snippet}"
        )
        raw, usage = self._call_simple(TRIAGE_SYSTEM, user_content, max_tokens=100)
        parsed = _parse_json(raw)
        return TriageResult(
            type=parsed.get("type", "known"),
            page_hint=parsed.get("page_hint") or None,
            used_llm=True,
            usage=usage,
        )


def _index_paths() -> str:
    import re as _re
    index = read_index()
    return "\n".join(_re.findall(r"\[\[([\w/.-]+)\]\]", index))


def _parse_json(raw: str) -> dict:
    m = re.search(r"\{[^}]+\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return {"type": "known", "page_hint": None}

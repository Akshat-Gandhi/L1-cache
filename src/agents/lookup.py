import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass, field
from src.agents.base import BaseAgent, Usage
from src.utils.wiki import read_agents_md, read_wiki_page
from src.utils.index import read_index

_NEW_PAGE_RE = re.compile(r"<!--\s*new-page:\s*([\w/.-]+)\s*-->")
_PATH_RE     = re.compile(r"(?:errors|commands|concepts)/[\w/-]+")


@dataclass
class QueryResult:
    suggestion: str
    pages_read: list[str] = field(default_factory=list)
    new_page_hint: str | None = None
    usage: Usage = field(default_factory=Usage)


IDENTIFY_SYSTEM = """\
You are a wiki page selector.
Given a wiki index and a terminal error, output ONLY the 1–3 most relevant page paths.
One path per line. No explanation, no markdown, no bullet points.
Example output:
errors/permission-denied
commands/systemctl
"""

SYNTHESIZE_SYSTEM = """\
You are a Linux terminal assistant. A user ran a command that failed.
You are given relevant wiki pages. Return the exact fix.

Output format:
FIX: <exact command(s)>
WHY: <one sentence>
SOURCE: [[page/path]]

If the wiki pages don't cover this error, answer from general knowledge and add:
<!-- new-page: errors/suggested-name -->
"""


class LookupAgent(BaseAgent):
    """
    Two-step approach:
      Step 1 — identify 1-3 relevant pages from the index (~150 tokens)
      Step 2 — read those pages, synthesize the fix (~1500 tokens)

    Works with both the anthropic SDK and the claude -p CLI backend.
    """

    def query(self, error: str, command: str = "", context: list[str] | None = None) -> QueryResult:
        system_main = read_agents_md()
        index = read_index()
        total_usage = Usage()
        context_block = "\n".join(context or [])

        # ── Step 1: identify pages ──────────────────────────────────── #
        identify_prompt = (
            f"Wiki index:\n{index}\n\n"
            f"Command: {command}\n"
            f"Error: {error}\n"
            + (f"Recent context:\n{context_block}\n" if context_block else "")
            + "\nList the 1-3 most relevant page paths."
        )
        paths_text, usage1 = self._call_simple(IDENTIFY_SYSTEM, identify_prompt, max_tokens=150)
        total_usage.merge(usage1)

        pages = _parse_paths(paths_text, index)

        # ── Step 2: read pages + synthesize fix ─────────────────────── #
        page_contents = {}
        for p in pages:
            content = read_wiki_page(p)
            if content:
                page_contents[p] = content

        pages_block = "\n\n---\n\n".join(
            f"[[{path}]]\n{content}" for path, content in page_contents.items()
        ) or "No wiki pages found for this error."

        fix_prompt = (
            f"Command: {command}\n"
            f"Error: {error}\n\n"
            f"Wiki pages:\n{pages_block}\n\n"
            "Provide the fix."
        )
        fix_text, usage2 = self._call_simple(SYNTHESIZE_SYSTEM, fix_prompt, max_tokens=1024)
        total_usage.merge(usage2)

        new_page_hint = _extract_new_page_hint(fix_text)
        return QueryResult(
            suggestion=fix_text,
            pages_read=list(page_contents.keys()),
            new_page_hint=new_page_hint,
            usage=total_usage,
        )


def _parse_paths(text: str, index: str) -> list[str]:
    """Extract valid wiki paths from Step 1 response."""
    found = _PATH_RE.findall(text)
    # Deduplicate, preserve order, limit to 3
    seen = set()
    result = []
    for p in found:
        p = p.strip("/").rstrip(".")
        if p not in seen:
            seen.add(p)
            result.append(p)
        if len(result) == 3:
            break
    return result


def _extract_new_page_hint(text: str) -> str | None:
    m = _NEW_PAGE_RE.search(text)
    return m.group(1) if m else None

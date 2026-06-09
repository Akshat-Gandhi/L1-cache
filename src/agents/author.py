import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass
from src.agents.base import BaseAgent, Usage
from src.utils.wiki import write_wiki_page
from src.utils.index import add_entry
from src.utils import log

AUTHOR_SYSTEM = """\
You are a wiki page author for a Linux terminal wiki.
Given an error, command, and optional fix, write a structured wiki page.

Output ONLY valid markdown matching this exact schema:

# <title>

## One-liner
<one sentence description>

## Common Patterns
<2-3 most frequent use cases with exact commands, as a markdown list>

## Errors & Fixes
<known errors with working fixes, as a markdown list>

## Related
<[[links]] to other pages if relevant, or empty>

## Session Notes

Rules:
- Be specific and terse.
- Use exact commands, not prose descriptions.
- The title should be the error name or command name in Title Case.
- On the very last line output exactly:
  INDEX: <10-word description for the wiki index>
"""


@dataclass
class AuthorResult:
    page_path: str
    content: str
    index_description: str
    usage: Usage


class AuthorAgent(BaseAgent):

    def create_page(self, page_path: str, error: str, command: str = "",
                    fix: str = "", context: str = "") -> AuthorResult:
        user_content = (
            f"Page path: {page_path}\n"
            f"Command: {command}\n"
            f"Error: {error}\n"
            + (f"Working fix: {fix}\n" if fix else "")
            + (f"Context: {context}\n" if context else "")
            + "\nWrite the wiki page now."
        )

        raw, usage = self._call_simple(AUTHOR_SYSTEM, user_content, max_tokens=1500)
        content, index_desc = _split_index_line(raw)

        write_wiki_page(page_path, content)
        add_entry(page_path, index_desc)
        log.append("ingest", f"created {page_path}", error[:80])

        return AuthorResult(
            page_path=page_path,
            content=content,
            index_description=index_desc,
            usage=usage,
        )


def _split_index_line(raw: str) -> tuple[str, str]:
    lines = raw.splitlines()
    index_desc = "See this page for details"
    clean_lines = []
    for line in lines:
        if line.startswith("INDEX:"):
            index_desc = line.removeprefix("INDEX:").strip()
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip(), index_desc

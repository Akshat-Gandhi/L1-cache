import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass
from src.agents.base import BaseAgent, Usage
from src.utils.wiki import read_wiki_page, write_wiki_page, append_session_note
from src.utils import log

EDITOR_SYSTEM = """\
You are a wiki page editor. You receive an existing wiki page and a confirmed fix.
Your job is to update the page's "Errors & Fixes" section with the new confirmed fix if it is not already there.

Rules:
- Only edit the "Errors & Fixes" section.
- Add the new fix as a bullet point: `- **<error pattern>**: <exact command>`
- Do not remove existing content.
- Return the COMPLETE updated page, unchanged except for the addition.
- If the fix is already documented, return the page unchanged.
"""


@dataclass
class EditResult:
    page_path: str
    changed: bool
    usage: Usage


class EditorAgent(BaseAgent):
    """Updates an existing wiki page with a confirmed fix."""

    def update_fix(self, page_path: str, error: str, fix: str) -> EditResult:
        existing = read_wiki_page(page_path)
        if existing is None:
            return EditResult(page_path=page_path, changed=False, usage=Usage())

        response, usage = self._call(
            system=EDITOR_SYSTEM,
            messages=[{
                "role": "user",
                "content": (
                    f"Existing page:\n\n{existing}\n\n"
                    f"---\n"
                    f"Error: {error}\n"
                    f"Confirmed fix: {fix}\n\n"
                    "Return the updated page."
                )
            }],
            max_tokens=2000,
        )

        updated = next((b.text for b in response.content if hasattr(b, "text")), "")
        changed = updated.strip() != existing.strip()

        if changed:
            write_wiki_page(page_path, updated)
            log.append("update", page_path, fix[:80])

        return EditResult(page_path=page_path, changed=changed, usage=usage)

    def add_session_note(self, page_path: str, note: str) -> bool:
        ok = append_session_note(page_path, note)
        if ok:
            log.append("note", page_path, note[:80])
        return ok

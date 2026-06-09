"""
Writeback workflow — called when the user confirms a fix worked.

Flow:
  confirmed fix + page_path → EditorAgent updates Errors & Fixes section
                             → log.md appended
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass
from src.agents.editor import EditorAgent, EditResult
from src.utils import log


@dataclass
class WritebackResult:
    page_path: str
    updated: bool
    input_tokens: int
    output_tokens: int


def confirm_fix(page_path: str, error: str, fix: str) -> WritebackResult:
    """
    Called after user confirms the suggested fix worked.
    Updates the wiki page and logs the confirmed fix.
    """
    agent = EditorAgent()
    result: EditResult = agent.update_fix(page_path=page_path, error=error, fix=fix)

    if result.changed:
        log.append("fix-confirmed", page_path, fix[:80])

    return WritebackResult(
        page_path=page_path,
        updated=result.changed,
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
    )

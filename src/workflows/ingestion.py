"""
Ingestion workflow — runs when a new error is encountered that has no wiki page.

Flow:
  error + command → AuthorAgent creates page → index updated → log updated
  Optionally: if a fix is already known, it's embedded in the new page.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass
from src.agents.author import AuthorAgent, AuthorResult
from src.utils.wiki import wiki_page_exists


@dataclass
class IngestionResult:
    page_path: str
    created: bool
    author_result: AuthorResult | None = None


def ingest_new_error(page_path: str, error: str, command: str = "",
                     fix: str = "", context: str = "") -> IngestionResult:
    """
    Create a new wiki page for an error. Idempotent: skips if page already exists.
    """
    if wiki_page_exists(page_path):
        return IngestionResult(page_path=page_path, created=False)

    agent = AuthorAgent()
    result = agent.create_page(
        page_path=page_path,
        error=error,
        command=command,
        fix=fix,
        context=context,
    )
    return IngestionResult(page_path=page_path, created=True, author_result=result)

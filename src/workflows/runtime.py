"""
Runtime workflow — called by the shell hook on every failed command.

Flow:
  command + stderr → LookupAgent → suggestion
  If LookupAgent flags new-page: → IngestionWorkflow runs async
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
from dataclasses import dataclass
from src.agents.lookup import LookupAgent, QueryResult
from src.workflows.ingestion import ingest_new_error
from src.utils import log


@dataclass
class RuntimeResult:
    suggestion: str
    pages_read: list[str]
    latency_ms: float
    input_tokens: int
    output_tokens: int
    new_page_created: str | None = None


def handle_error(command: str, stderr: str, context: list[str] | None = None) -> RuntimeResult:
    """
    Main entry point called by the shell hook.
    Returns a suggestion to display as ghost text.
    """
    t0 = time.perf_counter()
    agent = LookupAgent()
    result: QueryResult = agent.query(error=stderr, command=command, context=context)
    latency_ms = (time.perf_counter() - t0) * 1000

    log.append("query", command[:60], stderr[:60])

    new_page = None
    if result.new_page_hint:
        try:
            ingest_new_error(
                page_path=result.new_page_hint,
                error=stderr,
                command=command,
            )
            new_page = result.new_page_hint
            log.append("ingest", f"auto-created {result.new_page_hint}", "from runtime")
        except Exception:
            pass

    return RuntimeResult(
        suggestion=result.suggestion,
        pages_read=result.pages_read,
        latency_ms=latency_ms,
        input_tokens=result.usage.input_tokens,
        output_tokens=result.usage.output_tokens,
        new_page_created=new_page,
    )

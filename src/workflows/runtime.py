"""
Runtime workflow — called by the shell hook on every failed command.

Flow:
  command + stderr
    → TriageAgent (regex fast-path, LLM fallback)
      ├─ known  → LookupAgent reads relevant pages → suggestion
      └─ new    → LookupAgent answers + AuthorAgent creates page in background
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import time
from dataclasses import dataclass
from src.agents.triage import TriageAgent, TriageResult
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
    triage_used_llm: bool = False
    new_page_created: str | None = None


def handle_error(command: str, stderr: str, context: list[str] | None = None) -> RuntimeResult:
    """Main entry point called by the shell hook."""
    t0 = time.perf_counter()
    total_input = 0
    total_output = 0

    # Stage 1: triage (regex first, LLM fallback)
    triage_agent = TriageAgent()
    triage: TriageResult = triage_agent.classify(error=stderr, command=command)
    total_input += triage.usage.input_tokens
    total_output += triage.usage.output_tokens

    # Stage 2: lookup (always runs — triage gives it a head-start hint)
    lookup_agent = LookupAgent()
    result: QueryResult = lookup_agent.query(
        error=stderr,
        command=command,
        context=context,
    )
    total_input += result.usage.input_tokens
    total_output += result.usage.output_tokens
    latency_ms = (time.perf_counter() - t0) * 1000

    log.append("query", command[:60], stderr[:60])

    # If new error: create wiki page (using hint from triage or lookup)
    new_page = None
    page_hint = triage.page_hint if triage.type == "new" else result.new_page_hint
    if triage.type == "new" and page_hint:
        try:
            ingest_new_error(page_path=page_hint, error=stderr, command=command)
            new_page = page_hint
            log.append("ingest", f"auto-created {page_hint}", "from runtime")
        except Exception:
            pass
    elif result.new_page_hint:
        try:
            ingest_new_error(page_path=result.new_page_hint, error=stderr, command=command)
            new_page = result.new_page_hint
        except Exception:
            pass

    return RuntimeResult(
        suggestion=result.suggestion,
        pages_read=result.pages_read,
        latency_ms=latency_ms,
        input_tokens=total_input,
        output_tokens=total_output,
        triage_used_llm=triage.used_llm,
        new_page_created=new_page,
    )

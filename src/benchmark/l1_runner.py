"""
L1 Cache benchmark runner.
For each test case: run the LookupAgent (tool-use loop), record all metrics.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import traceback
from src.agents.lookup import LookupAgent
from src.benchmark.test_suite import TestCase, score_response
from src.benchmark.metrics import RunMetrics, Timer


def run_single(case: TestCase) -> RunMetrics:
    m = RunMetrics(system="l1_cache", test_case_id=case.id, category=case.category)

    try:
        agent = LookupAgent()

        with Timer() as total_t:
            result = agent.query(
                error=case.stderr,
                command=case.command,
                context=[],
            )

        m.total_latency_ms = total_t.elapsed_ms
        m.llm_latency_ms = total_t.elapsed_ms   # L1 has no separate retrieval step
        m.items_retrieved = len(result.pages_read)
        m.api_calls = result.usage.api_calls
        m.input_tokens = result.usage.input_tokens
        m.output_tokens = result.usage.output_tokens
        m.response_text = result.suggestion

        scores = score_response(result.suggestion, case)
        m.partial_score = scores["partial"]
        m.exact_score = scores["exact"]

    except Exception as e:
        m.error = traceback.format_exc()

    return m


def run_all(cases: list[TestCase]) -> list[RunMetrics]:
    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] L1 {case.id}: {case.command[:40]}...")
        m = run_single(case)
        status = f"score={m.partial_score:.0%} tokens={m.total_tokens} {m.total_latency_ms:.0f}ms"
        if m.error:
            status = f"ERROR: {m.error[:60]}"
        print(f"         {status}")
        results.append(m)
    return results

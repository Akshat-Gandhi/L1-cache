"""
Generates a comparison report from L1 and RAG benchmark results.
Outputs: terminal summary + results/benchmark_YYYYMMDD_HHMMSS.json
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import statistics
from datetime import datetime
from pathlib import Path
from src.benchmark.metrics import RunMetrics


def _avg(vals: list[float]) -> float:
    return statistics.mean(vals) if vals else 0.0


def _group_by_field(metrics: list[RunMetrics], field: str) -> dict[str, list[RunMetrics]]:
    groups: dict[str, list[RunMetrics]] = {}
    for m in metrics:
        key = getattr(m, field)
        groups.setdefault(key, []).append(m)
    return groups


def generate(l1_results: list[RunMetrics], rag_results: list[RunMetrics],
             output_dir: Path | None = None) -> dict:
    l1 = [m for m in l1_results if not m.error]
    rag = [m for m in rag_results if not m.error]

    summary = {
        "generated_at": datetime.now().isoformat(),
        "test_cases": len(l1_results),
        "l1_errors": len([m for m in l1_results if m.error]),
        "rag_errors": len([m for m in rag_results if m.error]),
        "l1": _aggregate(l1),
        "rag": _aggregate(rag),
        "by_category": _by_category(l1, rag),
        "per_case": _per_case(l1_results, rag_results),
    }

    _print_report(summary)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = output_dir / f"benchmark_{ts}.json"
        out_path.write_text(json.dumps(summary, indent=2))
        print(f"\nResults saved → {out_path}")

    return summary


def _aggregate(metrics: list[RunMetrics]) -> dict:
    if not metrics:
        return {}
    return {
        "avg_total_latency_ms": _avg([m.total_latency_ms for m in metrics]),
        "avg_retrieval_latency_ms": _avg([m.retrieval_latency_ms for m in metrics]),
        "avg_llm_latency_ms": _avg([m.llm_latency_ms for m in metrics]),
        "avg_input_tokens": _avg([m.input_tokens for m in metrics]),
        "avg_output_tokens": _avg([m.output_tokens for m in metrics]),
        "avg_total_tokens": _avg([m.total_tokens for m in metrics]),
        "avg_api_calls": _avg([m.api_calls for m in metrics]),
        "avg_items_retrieved": _avg([m.items_retrieved for m in metrics]),
        "avg_partial_score": _avg([m.partial_score for m in metrics]),
        "avg_exact_score": _avg([m.exact_score for m in metrics]),
        "n": len(metrics),
    }


def _by_category(l1: list[RunMetrics], rag: list[RunMetrics]) -> dict:
    l1_cats = _group_by_field(l1, "category")
    rag_cats = _group_by_field(rag, "category")
    cats = sorted(set(list(l1_cats) + list(rag_cats)))
    return {
        cat: {
            "l1": _aggregate(l1_cats.get(cat, [])),
            "rag": _aggregate(rag_cats.get(cat, [])),
        }
        for cat in cats
    }


def _per_case(l1_results: list[RunMetrics], rag_results: list[RunMetrics]) -> list[dict]:
    rag_map = {m.test_case_id: m for m in rag_results}
    rows = []
    for l in l1_results:
        r = rag_map.get(l.test_case_id)
        rows.append({
            "id": l.test_case_id,
            "category": l.category,
            "l1_score": l.partial_score,
            "rag_score": r.partial_score if r else None,
            "l1_tokens": l.total_tokens,
            "rag_tokens": r.total_tokens if r else None,
            "l1_latency_ms": l.total_latency_ms,
            "rag_latency_ms": r.total_latency_ms if r else None,
            "l1_pages_read": l.items_retrieved,
            "rag_chunks": r.items_retrieved if r else None,
        })
    return rows


def _print_report(summary: dict) -> None:
    l1 = summary["l1"]
    rag = summary["rag"]

    def _fmt(val, fmt=".1f") -> str:
        if val is None:
            return "n/a"
        return format(val, fmt)

    print("\n" + "=" * 60)
    print("  TERMINAL WIKI BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  Test cases:       {summary['test_cases']}")
    print(f"  L1 errors:        {summary['l1_errors']}")
    print(f"  RAG errors:       {summary['rag_errors']}")
    print()
    print(f"{'Metric':<32} {'L1 Cache':>12} {'RAG':>12}  {'Winner':>8}")
    print("-" * 68)

    rows = [
        ("Accuracy (partial %)",    l1.get("avg_partial_score"), rag.get("avg_partial_score"), "higher"),
        ("Accuracy (exact %)",      l1.get("avg_exact_score"),   rag.get("avg_exact_score"),   "higher"),
        ("Total latency (ms)",      l1.get("avg_total_latency_ms"), rag.get("avg_total_latency_ms"), "lower"),
        ("Retrieval latency (ms)",  l1.get("avg_retrieval_latency_ms"), rag.get("avg_retrieval_latency_ms"), "lower"),
        ("LLM latency (ms)",        l1.get("avg_llm_latency_ms"), rag.get("avg_llm_latency_ms"), "lower"),
        ("Avg input tokens",        l1.get("avg_input_tokens"),   rag.get("avg_input_tokens"),   "lower"),
        ("Avg total tokens",        l1.get("avg_total_tokens"),   rag.get("avg_total_tokens"),   "lower"),
        ("Avg API calls",           l1.get("avg_api_calls"),      rag.get("avg_api_calls"),      "lower"),
        ("Items retrieved",         l1.get("avg_items_retrieved"),rag.get("avg_items_retrieved"),"lower"),
    ]

    for label, l1_val, rag_val, prefer in rows:
        is_pct = "%" in label
        multiplier = 100 if is_pct else 1
        l1_display = _fmt((l1_val or 0) * multiplier)
        rag_display = _fmt((rag_val or 0) * multiplier)

        winner = ""
        if l1_val is not None and rag_val is not None:
            if prefer == "higher":
                winner = "L1" if l1_val > rag_val else ("RAG" if rag_val > l1_val else "tie")
            else:
                winner = "L1" if l1_val < rag_val else ("RAG" if rag_val < l1_val else "tie")

        print(f"  {label:<30} {l1_display:>12} {rag_display:>12}  {winner:>8}")

    print("=" * 60)

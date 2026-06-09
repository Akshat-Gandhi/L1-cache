#!/usr/bin/env python3
"""
Terminal Wiki CLI

Usage:
  python cli.py query --command "systemctl start nginx" --exit-code 1
  python cli.py ingest --page errors/my-error --error "..." --fix "..."
  python cli.py seed [--dir raw/tldr-pages]
  python cli.py benchmark [--cases 5] [--output benchmark/results]
  python cli.py confirm --page errors/permission-denied --error "..." --fix "sudo ..."
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import argparse
from pathlib import Path


def cmd_query(args):
    from src.workflows.runtime import handle_error
    result = handle_error(
        command=args.command,
        stderr=args.stderr or "",
        context=args.context or [],
    )
    print(result.suggestion)
    if args.verbose:
        print(f"\n[pages_read={result.pages_read} tokens={result.input_tokens}+{result.output_tokens} latency={result.latency_ms:.0f}ms]", file=sys.stderr)


def cmd_ingest(args):
    from src.workflows.ingestion import ingest_new_error
    result = ingest_new_error(
        page_path=args.page,
        error=args.error,
        command=args.command or "",
        fix=args.fix or "",
    )
    if result.created:
        print(f"Created: {args.page}")
    else:
        print(f"Already exists: {args.page}")


def cmd_seed(args):
    from src.agents.seeder import SeederAgent
    agent = SeederAgent()
    tldr_dir = Path(args.dir) if args.dir else None
    results = agent.seed_directory(tldr_dir)
    print(f"Seeded {len(results)} pages.")


def cmd_benchmark(args):
    from src.benchmark.test_suite import TEST_CASES
    from src.benchmark.l1_runner import run_all as l1_run
    from src.benchmark.rag_runner import run_all as rag_run
    from src.benchmark.report import generate

    cases = TEST_CASES[:args.cases] if args.cases else TEST_CASES
    output_dir = Path(args.output) if args.output else None

    print(f"Running benchmark on {len(cases)} test cases...\n")

    print("--- L1 Cache ---")
    l1_results = l1_run(cases)

    print("\n--- RAG ---")
    rag_results = rag_run(cases)

    print()
    generate(l1_results, rag_results, output_dir=output_dir)


def cmd_confirm(args):
    from src.workflows.writeback import confirm_fix
    result = confirm_fix(page_path=args.page, error=args.error, fix=args.fix)
    if result.updated:
        print(f"Updated: {args.page}")
    else:
        print(f"No change: {args.page}")


def main():
    parser = argparse.ArgumentParser(description="Terminal Wiki CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # query
    p = sub.add_parser("query", help="Look up a fix for a terminal error")
    p.add_argument("--command", default="")
    p.add_argument("--stderr", default="")
    p.add_argument("--exit-code", type=int, default=1)
    p.add_argument("--context", nargs="*")
    p.add_argument("--verbose", action="store_true")

    # ingest
    p = sub.add_parser("ingest", help="Create a new wiki page for an error")
    p.add_argument("--page", required=True)
    p.add_argument("--error", required=True)
    p.add_argument("--command", default="")
    p.add_argument("--fix", default="")

    # seed
    p = sub.add_parser("seed", help="Bulk-seed wiki from tldr-pages")
    p.add_argument("--dir", default=None, help="Path to tldr .md files")

    # benchmark
    p = sub.add_parser("benchmark", help="Run L1 vs RAG benchmark")
    p.add_argument("--cases", type=int, default=0, help="Number of test cases (0=all)")
    p.add_argument("--output", default="benchmark/results", help="Output directory for JSON report")

    # confirm
    p = sub.add_parser("confirm", help="Mark a fix as confirmed, update wiki page")
    p.add_argument("--page", required=True)
    p.add_argument("--error", required=True)
    p.add_argument("--fix", required=True)

    args = parser.parse_args()
    {"query": cmd_query, "ingest": cmd_ingest, "seed": cmd_seed,
     "benchmark": cmd_benchmark, "confirm": cmd_confirm}[args.cmd](args)


if __name__ == "__main__":
    main()

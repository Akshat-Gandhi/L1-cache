import os
from pathlib import Path

WIKI_ROOT = Path(os.getenv("TERMINAL_WIKI_ROOT", Path(__file__).parent))
WIKI_DIR = WIKI_ROOT / "wiki"
RAW_DIR = WIKI_ROOT / "raw"
INDEX_PATH = WIKI_ROOT / "index.md"
LOG_PATH = WIKI_ROOT / "log.md"
AGENTS_PATH = WIKI_ROOT / "AGENTS.md"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("TERMINAL_WIKI_MODEL", "claude-sonnet-4-6")

# Benchmark settings
BENCHMARK_TOP_K = 5           # chunks retrieved by RAG
BENCHMARK_CHUNK_SIZE = 256    # tokens per RAG chunk
RAG_EMBED_MODEL = "all-MiniLM-L6-v2"

"""
RAG benchmark runner.
Chunks all wiki pages, embeds them with sentence-transformers, stores in ChromaDB.
For each test case: embed query, retrieve top-K chunks, send to Claude, record metrics.

This is the apples-to-apples comparison: same corpus, same Claude model, different retrieval.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import re
import traceback
import anthropic
from pathlib import Path

from src.benchmark.test_suite import TestCase, score_response
from src.benchmark.metrics import RunMetrics, Timer
from src.utils.wiki import read_agents_md, list_all_pages, read_wiki_page
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, BENCHMARK_TOP_K, BENCHMARK_CHUNK_SIZE, RAG_EMBED_MODEL


def _chunk_text(text: str, size: int = BENCHMARK_CHUNK_SIZE) -> list[str]:
    """Naive word-boundary chunking."""
    words = text.split()
    chunks, current = [], []
    for word in words:
        current.append(word)
        if len(current) >= size:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


class RAGIndex:
    """Lazy-initialized ChromaDB collection over all wiki pages."""

    def __init__(self):
        self._collection = None
        self._client_chroma = None
        self._embed_model = None

    def _ensure_built(self) -> None:
        if self._collection is not None:
            return

        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "RAG runner requires extra dependencies:\n"
                "  pip install chromadb sentence-transformers"
            )

        self._embed_model = SentenceTransformer(RAG_EMBED_MODEL)
        self._client_chroma = chromadb.Client()
        self._collection = self._client_chroma.create_collection("wiki")

        pages = list_all_pages()
        all_chunks, all_ids, all_metas = [], [], []
        for page in pages:
            content = read_wiki_page(page) or ""
            for i, chunk in enumerate(_chunk_text(content)):
                all_chunks.append(chunk)
                all_ids.append(f"{page}::{i}")
                all_metas.append({"page": page, "chunk_index": i})

        if not all_chunks:
            return

        embeddings = self._embed_model.encode(all_chunks, show_progress_bar=False).tolist()
        self._collection.add(documents=all_chunks, embeddings=embeddings,
                             ids=all_ids, metadatas=all_metas)

    def retrieve(self, query: str, k: int = BENCHMARK_TOP_K) -> list[dict]:
        """Returns list of {chunk, page, chunk_index} dicts."""
        self._ensure_built()
        if self._collection is None or self._collection.count() == 0:
            return []

        embedding = self._embed_model.encode([query], show_progress_bar=False).tolist()
        results = self._collection.query(query_embeddings=embedding, n_results=min(k, self._collection.count()))
        out = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            out.append({"chunk": doc, "page": meta["page"], "chunk_index": meta["chunk_index"]})
        return out


_INDEX = RAGIndex()


def run_single(case: TestCase) -> RunMetrics:
    m = RunMetrics(system="rag", test_case_id=case.id, category=case.category)

    try:
        # Retrieval
        with Timer() as retrieval_t:
            chunks = _INDEX.retrieve(f"{case.command} {case.stderr}")
        m.retrieval_latency_ms = retrieval_t.elapsed_ms
        m.items_retrieved = len(chunks)

        context_block = "\n\n---\n\n".join(
            f"[Source: {c['page']}]\n{c['chunk']}" for c in chunks
        )

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        system = read_agents_md()
        user_content = (
            f"Command: {case.command}\n"
            f"Error: {case.stderr}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Provide the fix."
        )

        with Timer() as llm_t:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
        m.llm_latency_ms = llm_t.elapsed_ms
        m.total_latency_ms = m.retrieval_latency_ms + m.llm_latency_ms
        m.api_calls = 1
        m.input_tokens = response.usage.input_tokens
        m.output_tokens = response.usage.output_tokens
        m.response_text = next((b.text for b in response.content if hasattr(b, "text")), "")

        scores = score_response(m.response_text, case)
        m.partial_score = scores["partial"]
        m.exact_score = scores["exact"]

    except Exception:
        m.error = traceback.format_exc()

    return m


def run_all(cases: list[TestCase]) -> list[RunMetrics]:
    print("  Building RAG index...")
    try:
        _INDEX._ensure_built()
        page_count = _INDEX._collection.count() if _INDEX._collection else 0
        print(f"  Index ready: {page_count} chunks")
    except RuntimeError as e:
        print(f"  {e}")
        return [RunMetrics(system="rag", test_case_id=c.id, category=c.category,
                           error=str(e)) for c in cases]

    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] RAG {case.id}: {case.command[:40]}...")
        m = run_single(case)
        status = f"score={m.partial_score:.0%} tokens={m.total_tokens} {m.total_latency_ms:.0f}ms"
        if m.error:
            status = f"ERROR: {m.error[:60]}"
        print(f"         {status}")
        results.append(m)
    return results

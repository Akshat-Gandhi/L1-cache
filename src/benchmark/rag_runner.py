"""
RAG benchmark runner — FAISS backend.

Chunks all wiki pages, embeds with sentence-transformers, stores in a FAISS
flat inner-product index (cosine similarity on normalized vectors).

For each test case: embed query → retrieve top-K chunks → send to Claude.
Same corpus, same Claude model as L1 runner — only the retrieval differs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import traceback
import numpy as np
import anthropic

from src.benchmark.test_suite import TestCase, score_response
from src.benchmark.metrics import RunMetrics, Timer
from src.utils.wiki import read_agents_md, list_all_pages, read_wiki_page
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, BENCHMARK_TOP_K, BENCHMARK_CHUNK_SIZE, RAG_EMBED_MODEL


def _chunk_text(text: str, size: int = BENCHMARK_CHUNK_SIZE) -> list[str]:
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


class FAISSIndex:
    """Lazy-built FAISS flat inner-product index over wiki chunks."""

    def __init__(self):
        self._index = None
        self._chunks: list[str] = []
        self._metadata: list[dict] = []
        self._model = None

    def _ensure_built(self) -> None:
        if self._index is not None:
            return

        try:
            import faiss
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError(
                "RAG runner requires extra dependencies:\n"
                "  pip install faiss-cpu sentence-transformers"
            )

        self._model = SentenceTransformer(RAG_EMBED_MODEL)

        pages = list_all_pages()
        for page in pages:
            content = read_wiki_page(page) or ""
            for i, chunk in enumerate(_chunk_text(content)):
                self._chunks.append(chunk)
                self._metadata.append({"page": page, "chunk_index": i})

        if not self._chunks:
            return

        embeddings = self._model.encode(self._chunks, show_progress_bar=False, normalize_embeddings=True)
        dim = embeddings.shape[1]

        self._index = faiss.IndexFlatIP(dim)           # cosine sim via normalized vectors
        self._index.add(embeddings.astype(np.float32))

    def retrieve(self, query: str, k: int = BENCHMARK_TOP_K) -> list[dict]:
        self._ensure_built()
        if self._index is None or self._index.ntotal == 0:
            return []

        q_emb = self._model.encode([query], normalize_embeddings=True)
        k_actual = min(k, self._index.ntotal)
        scores, indices = self._index.search(q_emb.astype(np.float32), k_actual)
        return [
            {"chunk": self._chunks[idx], "score": float(scores[0][j]), **self._metadata[idx]}
            for j, idx in enumerate(indices[0]) if idx >= 0
        ]

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)


_INDEX = FAISSIndex()


def run_single(case: TestCase) -> RunMetrics:
    m = RunMetrics(system="rag", test_case_id=case.id, category=case.category)

    try:
        query_text = f"{case.command} {case.stderr}"

        with Timer() as retrieval_t:
            chunks = _INDEX.retrieve(query_text)
        m.retrieval_latency_ms = retrieval_t.elapsed_ms
        m.items_retrieved = len(chunks)

        context_block = "\n\n---\n\n".join(
            f"[Source: {c['page']}  score={c['score']:.3f}]\n{c['chunk']}"
            for c in chunks
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
    print("  Building FAISS index...")
    try:
        _INDEX._ensure_built()
        print(f"  Index ready: {_INDEX.chunk_count} chunks across {len(list_all_pages())} pages")
    except RuntimeError as e:
        print(f"  {e}")
        return [RunMetrics(system="rag", test_case_id=c.id, category=c.category, error=str(e))
                for c in cases]

    results = []
    for i, case in enumerate(cases):
        print(f"  [{i+1}/{len(cases)}] RAG {case.id}: {case.command[:40]}...")
        m = run_single(case)
        status = f"score={m.partial_score:.0%} tokens={m.total_tokens} {m.total_latency_ms:.0f}ms"
        if m.error:
            status = f"ERROR: {m.error[:80]}"
        print(f"         {status}")
        results.append(m)
    return results

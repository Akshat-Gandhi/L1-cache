import time
from dataclasses import dataclass, field, asdict
from typing import Literal


@dataclass
class RunMetrics:
    system: Literal["l1_cache", "rag"]
    test_case_id: str
    category: str

    # Retrieval
    retrieval_latency_ms: float = 0.0
    items_retrieved: int = 0          # pages read (L1) or chunks (RAG)

    # LLM
    llm_latency_ms: float = 0.0
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    # Accuracy
    partial_score: float = 0.0       # 0–1, fraction of keywords matched
    exact_score: float = 0.0         # 0 or 1

    # Total
    total_latency_ms: float = 0.0
    response_text: str = ""
    error: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_tokens"] = self.total_tokens
        return d


class Timer:
    def __init__(self):
        self._start: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000

import os
import json
import subprocess
from dataclasses import dataclass, field
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0

    def add_usage(self, inp: int, out: int) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.api_calls += 1

    def merge(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.api_calls += other.api_calls

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseAgent:
    """
    Single-turn LLM caller.
    Auto-selects backend:
      - ANTHROPIC_API_KEY set  → anthropic SDK
      - not set                → claude -p subprocess (uses Claude Code session auth)
    """

    def __init__(self, model: str | None = None):
        self.model = model or CLAUDE_MODEL
        self._use_cli = not ANTHROPIC_API_KEY
        self._sdk_client = None

        if not self._use_cli:
            import anthropic
            self._sdk_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def _call_simple(self, system: str, user: str, max_tokens: int = 1024) -> tuple[str, Usage]:
        """
        Single-turn call. Returns (response_text, usage).
        Works identically via SDK or claude -p subprocess.
        """
        if self._use_cli:
            return self._call_cli(system, user)
        return self._call_sdk(system, user, max_tokens)

    # ------------------------------------------------------------------ #
    # Claude Code CLI backend                                              #
    # ------------------------------------------------------------------ #

    def _call_cli(self, system: str, user: str) -> tuple[str, Usage]:
        cmd = [
            "claude", "-p",
            "--system-prompt", system,
            "--output-format", "json",
            "--no-session-persistence",
        ]
        try:
            proc = subprocess.run(
                cmd,
                input=user,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude CLI timed out after 120s")

        if proc.returncode != 0:
            raise RuntimeError(f"claude CLI exited {proc.returncode}: {proc.stderr[:300]}")

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"claude CLI returned non-JSON: {proc.stdout[:200]}")

        if data.get("is_error"):
            raise RuntimeError(f"claude CLI error: {data.get('result', 'unknown')}")

        raw_usage = data.get("usage", {})
        usage = Usage()
        usage.add_usage(
            inp=raw_usage.get("input_tokens", 0),
            out=raw_usage.get("output_tokens", 0),
        )
        return data.get("result", ""), usage

    # ------------------------------------------------------------------ #
    # Anthropic SDK backend                                                #
    # ------------------------------------------------------------------ #

    def _call_sdk(self, system: str, user: str, max_tokens: int = 1024) -> tuple[str, Usage]:
        response = self._sdk_client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = next((b.text for b in response.content if hasattr(b, "text")), "")
        usage = Usage()
        usage.add_usage(response.usage.input_tokens, response.usage.output_tokens)
        return text, usage

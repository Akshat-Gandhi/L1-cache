import anthropic
from dataclasses import dataclass, field
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0

    def add(self, response_usage) -> None:
        self.input_tokens += response_usage.input_tokens
        self.output_tokens += response_usage.output_tokens
        self.api_calls += 1

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BaseAgent:
    def __init__(self, model: str | None = None):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = model or CLAUDE_MODEL

    def _call(self, system: str, messages: list, max_tokens: int = 1024,
              tools: list | None = None) -> tuple[anthropic.types.Message, Usage]:
        usage = Usage()
        kwargs = dict(model=self.model, max_tokens=max_tokens, system=system, messages=messages)
        if tools:
            kwargs["tools"] = tools
        response = self.client.messages.create(**kwargs)
        usage.add(response.usage)
        return response, usage

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass, field
from src.agents.base import BaseAgent, Usage
from src.utils.wiki import read_agents_md, read_wiki_page
from src.utils.index import read_index


READ_WIKI_TOOL = {
    "name": "read_wiki_page",
    "description": (
        "Read a wiki page by path. Call this after identifying relevant pages from the index. "
        "Path format: 'errors/permission-denied' or 'commands/systemctl' (no .md, no leading slash)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Wiki page path, e.g. 'errors/permission-denied'"
            }
        },
        "required": ["path"]
    }
}


@dataclass
class QueryResult:
    suggestion: str
    pages_read: list[str] = field(default_factory=list)
    new_page_hint: str | None = None   # populated if Claude flagged <!-- new-page: ... -->
    usage: Usage = field(default_factory=Usage)


class LookupAgent(BaseAgent):
    """
    Agentic tool-use loop:
    1. Claude receives error + index.md
    2. Claude calls read_wiki_page for relevant pages
    3. Claude synthesizes final answer
    """

    def query(self, error: str, command: str = "", context: list[str] | None = None) -> QueryResult:
        system = read_agents_md()
        index = read_index()
        context_block = "\n".join(context or [])

        user_content = (
            f"Command: {command}\n"
            f"Error output: {error}\n"
            + (f"Recent context:\n{context_block}\n" if context_block else "")
            + f"\nWiki Index:\n{index}\n\n"
            "Read the relevant wiki pages and return the fix."
        )

        messages = [{"role": "user", "content": user_content}]
        pages_read: list[str] = []
        total_usage = Usage()

        while True:
            response, usage = self._call(
                system=system,
                messages=messages,
                max_tokens=1024,
                tools=[READ_WIKI_TOOL]
            )
            total_usage.input_tokens += usage.input_tokens
            total_usage.output_tokens += usage.output_tokens
            total_usage.api_calls += usage.api_calls

            if response.stop_reason == "end_turn":
                suggestion = next(
                    (b.text for b in response.content if hasattr(b, "text")), ""
                )
                new_page_hint = _extract_new_page_hint(suggestion)
                return QueryResult(
                    suggestion=suggestion,
                    pages_read=pages_read,
                    new_page_hint=new_page_hint,
                    usage=total_usage,
                )

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        path = block.input.get("path", "")
                        pages_read.append(path)
                        content = read_wiki_page(path)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content if content else f"Page not found: {path}"
                        })
                messages.append({"role": "user", "content": tool_results})

            else:
                # Unexpected stop reason — surface whatever text we have
                suggestion = next(
                    (b.text for b in response.content if hasattr(b, "text")), ""
                )
                return QueryResult(suggestion=suggestion, pages_read=pages_read, usage=total_usage)


def _extract_new_page_hint(text: str) -> str | None:
    import re
    m = re.search(r"<!--\s*new-page:\s*([\w/.-]+)\s*-->", text)
    return m.group(1) if m else None

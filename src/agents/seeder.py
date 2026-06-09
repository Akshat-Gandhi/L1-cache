import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pathlib import Path
from dataclasses import dataclass
from src.agents.base import BaseAgent, Usage
from src.utils.wiki import write_wiki_page
from src.utils.index import rebuild_index
from src.utils import log
from config import RAW_DIR

SEEDER_SYSTEM = """\
You are converting a tldr-pages entry into a structured wiki page.

Output ONLY valid markdown in this exact schema:

# <command name in Title Case>

## One-liner
<one sentence, what this command does>

## Common Patterns
<the 2-4 most useful examples from tldr as a markdown list with exact commands>

## Errors & Fixes
<common errors for this command, if any — leave as "_Not yet documented._" if none known>

## Related
<empty for now>

## Session Notes

At the very end, on its own line:
INDEX: <10-word description for the wiki index>
"""


@dataclass
class SeedResult:
    page_path: str
    index_description: str
    usage: Usage


class SeederAgent(BaseAgent):

    def seed_from_tldr(self, tldr_file: Path) -> SeedResult | None:
        raw = tldr_file.read_text(encoding="utf-8", errors="replace")
        command_name = tldr_file.stem
        page_path = f"commands/{command_name}"

        content_raw, usage = self._call_simple(
            SEEDER_SYSTEM,
            f"tldr source:\n\n{raw}",
            max_tokens=1200,
        )
        content, index_desc = _split_index_line(content_raw)

        write_wiki_page(page_path, content)
        log.append("seed", page_path, command_name)
        return SeedResult(page_path=page_path, index_description=index_desc, usage=usage)

    def seed_directory(self, tldr_dir: Path | None = None) -> list[SeedResult]:
        source = tldr_dir or (RAW_DIR / "tldr-pages")
        files = sorted(source.glob("**/*.md"))
        results = []
        pairs = []
        for f in files:
            print(f"  Seeding {f.name}...")
            result = self.seed_from_tldr(f)
            if result:
                results.append(result)
                pairs.append((result.page_path, result.index_description))
        if pairs:
            rebuild_index(pairs)
        return results


def _split_index_line(raw: str) -> tuple[str, str]:
    lines = raw.splitlines()
    index_desc = "See this page for details"
    clean_lines = []
    for line in lines:
        if line.startswith("INDEX:"):
            index_desc = line.removeprefix("INDEX:").strip()
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip(), index_desc

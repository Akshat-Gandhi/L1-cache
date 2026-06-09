from pathlib import Path
from datetime import date
from config import WIKI_DIR, AGENTS_PATH

PAGE_TEMPLATE = """\
# {title}

## One-liner
{oneliner}

## Common Patterns
{patterns}

## Errors & Fixes
{errors_fixes}

## Related
{related}

## Session Notes
{session_notes}
"""


def wiki_path(page: str) -> Path:
    """Resolve a page path string like 'errors/permission-denied' to an absolute Path."""
    return WIKI_DIR / f"{page.lstrip('/')}.md"


def read_wiki_page(page: str) -> str | None:
    """Return page content or None if the page doesn't exist."""
    p = wiki_path(page)
    if not p.exists():
        return None
    return p.read_text()


def write_wiki_page(page: str, content: str) -> None:
    p = wiki_path(page)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def wiki_page_exists(page: str) -> bool:
    return wiki_path(page).exists()


def append_session_note(page: str, note: str) -> bool:
    """Append a confirmed fix note to a page's Session Notes section. Returns False if page missing."""
    content = read_wiki_page(page)
    if content is None:
        return False
    entry = f"- [{date.today()}] {note}"
    if "## Session Notes" in content:
        content = content.replace("## Session Notes\n", f"## Session Notes\n{entry}\n", 1)
    else:
        content += f"\n## Session Notes\n{entry}\n"
    write_wiki_page(page, content)
    return True


def render_new_page(title: str, oneliner: str = "", patterns: str = "",
                    errors_fixes: str = "", related: str = "", session_notes: str = "") -> str:
    return PAGE_TEMPLATE.format(
        title=title,
        oneliner=oneliner or "_Not yet documented._",
        patterns=patterns or "_Not yet documented._",
        errors_fixes=errors_fixes or "_Not yet documented._",
        related=related or "",
        session_notes=session_notes or "",
    )


def read_agents_md() -> str:
    return AGENTS_PATH.read_text()


def list_all_pages() -> list[str]:
    """Return all wiki page paths relative to wiki/, without .md extension."""
    return [
        str(p.relative_to(WIKI_DIR).with_suffix(""))
        for p in WIKI_DIR.rglob("*.md")
    ]

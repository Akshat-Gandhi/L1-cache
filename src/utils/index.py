import re
from pathlib import Path
from config import INDEX_PATH


def read_index() -> str:
    if not INDEX_PATH.exists():
        return ""
    return INDEX_PATH.read_text()


def add_entry(page: str, description: str) -> None:
    """
    Add or update a single entry in index.md.
    Entry format:  - [[page/path]] — description
    The entry is placed under the appropriate ## section header.
    """
    section = _section_for_page(page)
    entry_line = f"- [[{page}]] — {description}"

    content = INDEX_PATH.read_text() if INDEX_PATH.exists() else ""

    # If entry already exists, update it in place
    pattern = re.compile(rf"^- \[\[{re.escape(page)}\]\].*$", re.MULTILINE)
    if pattern.search(content):
        content = pattern.sub(entry_line, content)
        INDEX_PATH.write_text(content)
        return

    # If section header exists, append under it
    section_pattern = re.compile(rf"^## {re.escape(section)}$", re.MULTILINE)
    if section_pattern.search(content):
        content = section_pattern.sub(
            f"## {section}\n{entry_line}", content
        )
    else:
        # Create the section
        content = content.rstrip("\n") + f"\n\n## {section}\n{entry_line}\n"

    INDEX_PATH.write_text(content)


def remove_entry(page: str) -> None:
    if not INDEX_PATH.exists():
        return
    content = INDEX_PATH.read_text()
    pattern = re.compile(rf"^- \[\[{re.escape(page)}\]\].*\n?", re.MULTILINE)
    INDEX_PATH.write_text(pattern.sub("", content))


def _section_for_page(page: str) -> str:
    top = page.split("/")[0]
    return {"commands": "Commands", "errors": "Errors", "concepts": "Concepts"}.get(top, "Other")


def rebuild_index(pages_with_descriptions: list[tuple[str, str]]) -> None:
    """Full rebuild — used by the seeder after bulk ingestion."""
    sections: dict[str, list[str]] = {}
    for page, desc in sorted(pages_with_descriptions):
        section = _section_for_page(page)
        sections.setdefault(section, []).append(f"- [[{page}]] — {desc}")

    lines = ["# Terminal Wiki Index\n"]
    for section in ["Commands", "Errors", "Concepts", "Other"]:
        if section in sections:
            lines.append(f"## {section}")
            lines.extend(sections[section])
            lines.append("")

    INDEX_PATH.write_text("\n".join(lines))

from datetime import date
from config import LOG_PATH


def append(event_type: str, detail: str, extra: str = "") -> None:
    """
    Append one entry to log.md.
    Format: ## [YYYY-MM-DD] event_type | detail | extra
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    parts = [f"## [{today}]", event_type, detail]
    if extra:
        parts.append(extra)
    line = " | ".join(parts) + "\n"
    with LOG_PATH.open("a") as f:
        f.write(line)


def read_recent(n: int = 20) -> list[str]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text().splitlines()
    return [l for l in lines if l.startswith("## [")][-n:]

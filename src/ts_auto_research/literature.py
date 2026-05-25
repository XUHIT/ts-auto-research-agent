"""Read-only time-series literature indexing."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .io_utils import ensure_dir
from .paths import Workspace

SECTION_ALIASES = {
    "contribution": ["\u6838\u5fc3\u8d21\u732e\uff08\u4e00\u53e5\u8bdd\uff09", "\u6838\u5fc3\u8d21\u732e", "Contribution", "Main Contribution"],
    "keywords": ["\u5173\u952e\u8bcd\u6807\u7b7e", "\u5173\u952e\u8bcd", "Keywords", "Tags"],
    "limitations": ["\u5c40\u9650\u6027", "Limitations", "Weaknesses"],
}


def _extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def _extract_section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s+|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1).strip())[:1200]


def _first_section(text: str, names: list[str]) -> str:
    for name in names:
        value = _extract_section(text, name)
        if value:
            return value
    return ""


def parse_note(path: Path, source: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "title": _extract_title(text, path.stem.replace("_", " ")),
        "venue": path.parent.name,
        "path": str(path.relative_to(source)),
        "contribution": _first_section(text, SECTION_ALIASES["contribution"]),
        "keywords": _first_section(text, SECTION_ALIASES["keywords"]),
        "limitations": _first_section(text, SECTION_ALIASES["limitations"]),
    }


def build_index(workspace: Workspace, source: Path, limit: int | None = None) -> dict[str, Any]:
    source = source.expanduser().resolve()
    files = sorted(source.rglob("*.md"))
    if limit is not None:
        files = files[:limit]
    ensure_dir(workspace.literature)
    records = [parse_note(path, source) for path in files]
    with workspace.paper_index.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    context = summarize_context(records)
    workspace.selected_context.write_text(context, encoding="utf-8")
    return {"source": str(source), "count": len(records), "output": str(workspace.paper_index)}


def read_index(workspace: Workspace, limit: int | None = None) -> list[dict[str, Any]]:
    if not workspace.paper_index.exists():
        return []
    records: list[dict[str, Any]] = []
    with workspace.paper_index.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
            if limit is not None and len(records) >= limit:
                break
    return records


def summarize_context(records: list[dict[str, Any]], topic: str = "time series") -> str:
    venues: dict[str, int] = {}
    topic_hits = 0
    low_topic = topic.lower()
    for record in records:
        venues[record["venue"]] = venues.get(record["venue"], 0) + 1
        hay = " ".join(str(record.get(k, "")) for k in ["title", "contribution", "keywords"]).lower()
        if low_topic in hay:
            topic_hits += 1
    lines = ["# Selected Literature Context", "", f"Records: {len(records)}", f"Topic hits for `{topic}`: {topic_hits}", "", "## Venue Counts"]
    for venue, count in sorted(venues.items(), key=lambda item: (-item[1], item[0]))[:20]:
        lines.append(f"- {venue}: {count}")
    lines.append("")
    lines.append("## Representative Signals")
    for record in records[:10]:
        title = record.get("title", "[untitled]")
        contribution = record.get("contribution", "")
        lines.append(f"- **{title}**: {contribution[:180]}")
    return "\n".join(lines) + "\n"

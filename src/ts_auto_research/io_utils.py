"""Small IO helpers for human-readable protocol files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> Path:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def append_jsonl(path: Path, payload: dict[str, Any]) -> Path:
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _scalar_yaml(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text:
        return "''"
    if any(ch in text for ch in [":", "#", "\n", "{", "}", "[", "]"]):
        return json.dumps(text, ensure_ascii=False)
    return text


def to_yaml(payload: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(payload, dict):
        lines: list[str] = []
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_yaml(value, indent + 2))
            else:
                lines.append(f"{pad}{key}: {_scalar_yaml(value)}")
        return "\n".join(lines)
    if isinstance(payload, list):
        lines = []
        for item in payload:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{pad}- {_scalar_yaml(item)}")
        return "\n".join(lines)
    return f"{pad}{_scalar_yaml(payload)}"


def write_yaml(path: Path, payload: Any) -> Path:
    ensure_dir(path.parent)
    path.write_text(to_yaml(payload) + "\n", encoding="utf-8")
    return path

"""Tiny YAML reader for the project's simple config files.

This dependency-free reader supports the subset used by project.yaml and
profile.yaml: nested mappings, scalar values, empty arrays, and simple lists.
It is not intended to be a general YAML implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_simple_yaml(path: str | Path) -> dict[str, Any]:
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    for index, raw_line in enumerate(lines):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        if content.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"List item without list parent in {path}: {raw_line}")
            parent.append(_parse_scalar(content[2:].strip()))
            continue

        key, sep, value_text = content.partition(":")
        if not sep:
            raise ValueError(f"Invalid YAML line in {path}: {raw_line}")

        key = key.strip()
        value_text = value_text.strip()

        if value_text:
            _assign_mapping(parent, key, _parse_scalar(value_text))
            continue

        child = [] if _next_content_is_list(lines, index, indent) else {}
        _assign_mapping(parent, key, child)
        stack.append((indent, child))

    return root


def _assign_mapping(parent: Any, key: str, value: Any) -> None:
    if not isinstance(parent, dict):
        raise ValueError(f"Cannot assign key {key!r} to non-mapping parent")
    parent[key] = value


def _next_content_is_list(lines: list[str], current_index: int, current_indent: int) -> bool:
    for next_line in lines[current_index + 1 :]:
        stripped = next_line.split("#", 1)[0].rstrip()
        if not stripped.strip():
            continue
        next_indent = len(stripped) - len(stripped.lstrip(" "))
        if next_indent <= current_indent:
            return False
        return stripped.strip().startswith("- ")
    return False


def _parse_scalar(value: str) -> Any:
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value

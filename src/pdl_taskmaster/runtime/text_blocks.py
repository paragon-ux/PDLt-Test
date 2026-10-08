"""Plain string operations for reading model and program text.

No regular expressions: everything the harness takes from a model response or a
program's output is read with exact, inspectable string operations, so what is
recognised is exactly what is documented here.
"""

from __future__ import annotations

import json
from typing import Any

FENCE = "```"


def fenced_blocks(text: str, languages: tuple[str, ...]) -> list[str]:
    """Contents of ``` fenced blocks whose info string is one of ``languages``
    (case-insensitive), in order. A block opens on a line starting with ``` and
    closes at the next line that starts with ```. A line that only ends with ```
    closes it too (a fence stuck to the last line of code), unless a bare ``` line
    follows before the next opening fence: then it is text inside the block, such
    as a docstring that mentions a fence. A line starting with ``` and an info
    string opens the next block, so a block that was never closed ends there."""
    wanted = {language.lower() for language in languages}
    lines = (text or "").splitlines()
    # The next line after each one that starts with ```: "bare" (a closing fence), "info" (an opening one) or None.
    following: list[str | None] = [None] * len(lines)
    ahead: str | None = None
    for index in range(len(lines) - 1, -1, -1):
        following[index] = ahead
        stripped = lines[index].strip()
        if stripped.startswith(FENCE):
            ahead = "info" if stripped[len(FENCE):].strip() else "bare"
    blocks: list[str] = []
    current: list[str] | None = None
    keep = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if current is None:
            if stripped.startswith(FENCE):
                current, keep = [], stripped[len(FENCE):].strip().lower() in wanted
            continue
        starts = stripped.startswith(FENCE)
        if starts or (stripped.endswith(FENCE) and following[index] != "bare"):
            if not starts:
                current.append(line[: line.rfind(FENCE)])
            if keep:
                blocks.append("\n".join(current) + "\n")
            info = stripped[len(FENCE):].strip() if starts else ""
            current, keep = ([], info.lower() in wanted) if info else (None, False)
            continue
        current.append(line)
    return blocks


def witness_payload(line: str) -> str | None:
    """The text after a ``WITNESS:`` prefix on one stdout line, else None."""
    stripped = line.strip()
    if not stripped.startswith("WITNESS:"):
        return None
    return stripped[len("WITNESS:"):].strip()


def unfence_json(text: str) -> str:
    """A JSON reply wrapped in a ``` / ```json fence, without the fence."""
    stripped = text.strip()
    if not stripped.startswith(FENCE):
        return stripped
    first_newline = stripped.find("\n")
    inner = stripped[first_newline + 1:] if first_newline != -1 else ""
    if inner.rstrip().endswith(FENCE):
        inner = inner.rstrip()[: -len(FENCE)]
    return inner.strip()


def split_published_ir(text: str) -> tuple[str, dict[str, Any] | None]:
    """Split a published deliverable into its text and the Result IR the host
    appended after it as a final ```json block (session_engine._attach_result_ir)."""
    body = (text or "").rstrip()
    start = body.rfind("\n" + FENCE + "json\n")
    if start == -1 or not body.endswith(FENCE):
        return text or "", None
    try:
        ir = json.loads(body[start + len("\n" + FENCE + "json\n"): -len(FENCE)])
    except ValueError:
        return text or "", None
    return (body[:start].rstrip(), ir) if isinstance(ir, dict) else (text or "", None)


def words(text: str) -> list[str]:
    """Lowercased alphanumeric words (underscore counts as a letter)."""
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else " " for ch in (text or "").lower())
    return cleaned.split()

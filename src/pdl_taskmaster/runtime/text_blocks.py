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
    closes at the next line that starts or ends with ```."""
    wanted = {language.lower() for language in languages}
    blocks: list[str] = []
    current: list[str] | None = None
    keep = False
    for line in (text or "").splitlines():
        stripped = line.strip()
        if current is None:
            if stripped.startswith(FENCE):
                current, keep = [], stripped[len(FENCE):].strip().lower() in wanted
            continue
        if stripped.startswith(FENCE) or stripped.endswith(FENCE):
            if not stripped.startswith(FENCE):
                current.append(line[: line.rfind(FENCE)])
            if keep:
                blocks.append("\n".join(current) + "\n")
            current = None
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

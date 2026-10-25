"""CommonMark code blocks and literal readers for wire wrappers and program output."""

from __future__ import annotations

import json
from typing import Any

from markdown_it import MarkdownIt

FENCE = "```"


def fenced_blocks(text: str, languages: tuple[str, ...]) -> list[str]:
    """CommonMark fence contents, in order, selected by the first info-string word.

    The parser removes Markdown container/fence indentation. All remaining code
    content, including Python indentation, is returned without rewriting.
    """
    wanted = {language.lower() for language in languages}
    blocks: list[str] = []
    for token in MarkdownIt("commonmark").parse(text or ""):
        if token.type == "fence":
            info = token.info.split()
            if info and info[0].lower() in wanted:
                blocks.append(token.content)
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

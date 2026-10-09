"""A request index for scripted BOOTSTRAP replies (L100 v3).

The index's one rule rejects a reply with no ask found in the request, and the host retries
once. Tests that script BOOTSTRAP for some other purpose (routing, briefs, reasoning effort)
use this to send one ask taken from the request the call actually carries, so their call
sequences stay as they were.
"""
from __future__ import annotations

import json
from typing import Any


def request_of(projection_text: str) -> str:
    """The request a BOOTSTRAP call carries, from its projection (a prompt or a request body's input)."""
    projection, _ = json.JSONDecoder().raw_decode(projection_text[projection_text.index("{"):])

    def find(node: Any) -> str | None:
        if isinstance(node, dict):
            if "RAW_UNTRUSTED_CONTENT" in node:
                return node["RAW_UNTRUSTED_CONTENT"]
            node = list(node.values())
        if isinstance(node, list):
            for value in node:
                found = find(value)
                if found is not None:
                    return found
        return None

    text = find(projection) or ""
    return text.replace("<untrusted_user_input>", "").replace("</untrusted_user_input>", "").strip()


def ask_index(request: str) -> dict[str, Any]:
    """One ask: the request's first line."""
    line = next((line.strip() for line in request.splitlines() if line.strip()), request.strip())
    return {"asks": [line], "states": [], "exact": []}

"""Task entities for scripted BOOTSTRAP replies (L100 schema v2).

The entity rules reject a reply with no question quoted on an entity, or with a name the
request does not contain, and the host retries once. Tests that script BOOTSTRAP for some
other purpose (routing, briefs, reasoning effort) use this to send one target taken from
the request the call actually carries, so their call sequences stay as they were.
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


def target_entities(request: str) -> dict[str, Any]:
    """One target: the request's first word that is not a pronoun as its name, its first line as the question."""
    from pdl_taskmaster.runtime.task_entities import is_pronoun

    line = next((line.strip() for line in request.splitlines() if line.strip()), request.strip())
    name = next((word for word in line.split() if not is_pronoun(word.strip("?.,!"))), line)
    return {"groups": [], "entities": [{"name": name, "kind": "term", "unknown": line}]}

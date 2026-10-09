"""The host's checks on BOOTSTRAP's request index (ledger L100 v3; docs/plans/ENTITY_V3_DESIGN.md).

The index is three lists the model copies from the request: ``asks`` (the sentences or
clauses that ask for something), ``states`` (those that state what the task depends on) and
``exact`` (names and values whose spelling binds). The model links nothing to anything, and
the host never claims what a mention refers to.

Everything here is deterministic. ``violations`` holds the one rule enforced through the
single wire retry: at least one ask is found in the request. ``check`` keeps a span or value
only when it is one continuous piece of the request (``quotes.RequestText``), keeping the
request's own text, and counts what it drops.
"""
from __future__ import annotations

from typing import Any, Callable

from pdl_taskmaster.runtime.quotes import RequestText

NO_ASK = ("no ask is found word for word in the request: copy into asks each sentence or clause of the request "
          "that asks for something to be found, decided, written or produced, exactly as written")


def violations(index: dict[str, Any], sources: RequestText) -> list[str]:
    """Each way the reply breaks the index's one rule, as a sentence the retry feedback names."""
    if any(sources.locate(ask) is not None for ask in index.get("asks") or []):
        return []
    return [NO_ASK]


def check(index: dict[str, Any], sources: RequestText,
          sanitize: Callable[[str], str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """The index that survives the checks, as ``{"asks", "states", "exact"}``, and the events
    to record (name -> payload, nonzero only)."""
    dropped = {"asks": 0, "states": 0}

    def located(copy: object) -> str | None:
        found = sources.locate(copy)
        return None if found is None else sanitize(found).strip() or None

    def spans(key: str) -> list[str]:
        kept: list[str] = []
        for copy in index.get(key) or []:
            found = located(copy)
            if found is None:
                dropped[key] += 1
            elif found not in kept:
                kept.append(found)
        return kept

    exact: list[dict[str, str]] = []
    exact_dropped = 0
    for value in index.get("exact") or []:
        found = located(value.get("text"))
        if found is None:
            exact_dropped += 1
        elif all(found != kept["text"] for kept in exact):
            exact.append({"text": found, "kind": value.get("kind") or "identifier"})

    kept = {"asks": spans("asks"), "states": spans("states"), "exact": exact}
    events: dict[str, dict[str, Any]] = {}
    if dropped["asks"] or dropped["states"]:
        events["TASK_INDEX_SPAN_DROPPED"] = dict(dropped)
    if exact_dropped:
        events["TASK_INDEX_EXACT_DROPPED"] = {"count": exact_dropped}
    if not kept["asks"]:
        # Counted, never a session failure: the harness referees, it does not solve.
        events["TASK_INDEX_NO_ASK"] = {"states": len(kept["states"]), "exact": len(exact)}
    return kept, events


def empty(kept: dict[str, Any] | None) -> bool:
    return not kept or not (kept["asks"] or kept["states"] or kept["exact"])


def exact_names(kept: dict[str, Any] | None) -> tuple[str, ...]:
    """What the coverage check reads: the exact values, which a prompt body must spell exactly."""
    return tuple(value["text"] for value in (kept or {}).get("exact") or [])


def forwarded(kept: dict[str, Any] | None, *, with_states: bool) -> dict[str, Any] | None:
    """``TASK_INDEX`` as EXECUTE receives it, or None when nothing is kept. ``states`` is sent
    only to a stage that does not receive the request itself (the confirmed route)."""
    if empty(kept):
        return None
    out: dict[str, Any] = {"asks": list(kept["asks"])}
    if with_states:
        out["states"] = list(kept["states"])
    out["exact"] = [dict(value) for value in kept["exact"]]
    return out


def render(kept: dict[str, Any]) -> list[str]:
    """The drafting context's index lines: the asks, the statements, then the exact values."""
    lines: list[str] = []
    for key, head in (("asks", "asks:"), ("states", "states:")):
        if kept[key]:
            lines.append(head)
            lines += [f'  "{span}"' for span in kept[key]]
    if kept["exact"]:
        lines.append("exact values: " + "; ".join(f'"{value["text"]}" ({value["kind"]})' for value in kept["exact"]))
    return lines

"""The host's checks on BOOTSTRAP's task entities (ledger L100, docs/plans/ENTITY_REDESIGN.md).

Everything here is deterministic. An entity is kept only when its surface is one continuous
piece of the request; each quote in its relation passes the same test, and what is kept is
the request's own text (``quotes.RequestText``). Entities that name the same thing are
merged. ``distinction`` (implicit, undetermined, conflict) is BOOTSTRAP's one closed
judgment: it is dropped with the quote it is about, and later stages read it in the host's
fixed wording, labeled as a judgment.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from pdl_taskmaster.runtime.quotes import RequestText, fold_key
from pdl_taskmaster.runtime.wire_payloads import ENTITY_DISTINCTIONS, ENTITY_STATUSES

# The host's own wording for each distinction; the model only ever chooses the word.
DISTINCTION_READINGS = {
    "implicit": "to be worked out from what the request states; a stated value is not assumed to be the answer",
    "undetermined": "what the request states may not be enough to settle it",
    "conflict": "the quoted statements about it may contradict each other",
}
_PRECEDENCE = {None: 0, "implicit": 1, "undetermined": 2, "conflict": 3}  # a merge never hides a gap


def check(raw_entities: list[dict[str, Any]], sources: RequestText,
          sanitize: Callable[[str], str]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """The entities that survive the checks, and the events to record (name -> payload, nonzero only)."""
    counts: Counter[str] = Counter()
    dropped_values: list[str] = []
    checked: list[dict[str, Any]] = []
    for entity in raw_entities:
        surface = sources.locate(entity.get("surface"))
        if surface is None:
            counts["surface"] += 1
            continue
        for note in entity.get("dropped") or []:
            if note.startswith("distinction:"):
                counts["distinction"] += 1
                dropped_values.append(note.split(":", 1)[1])
            else:
                counts["text"] += 1
        relation = entity.get("relation") or {}
        status = entity.get("status") if entity.get("status") in ENTITY_STATUSES else "given"
        known: list[str] = []
        for quote in relation.get("known") or []:
            found = sources.locate(quote)
            if found is None:
                counts["quote_not_in_request"] += 1
            elif sanitize(found).strip() not in known:
                known.append(sanitize(found).strip())
        unknown = None
        if relation.get("unknown"):
            if status != "target":
                counts["unknown_on_given"] += 1
            else:
                found = sources.locate(relation["unknown"])
                if found is None:
                    counts["quote_not_in_request"] += 1
                else:
                    unknown = sanitize(found).strip()
        distinction = relation.get("distinction") if relation.get("distinction") in ENTITY_DISTINCTIONS else None
        if distinction and unknown is None:
            counts["distinction"] += 1
            dropped_values.append(f"{distinction} (no kept unknown)")
            distinction = None
        checked.append({
            "surface": surface,
            "kind": entity.get("kind") or "identifier",
            "status": status,
            "group": (entity.get("group") or "").strip() or None,
            "known": known, "unknown": unknown, "distinction": distinction,
        })

    merged: dict[str, dict[str, Any]] = {}
    for entity in checked:
        key = fold_key(entity["surface"])
        first = merged.get(key)
        if first is None:
            merged[key] = entity
            continue
        counts["merged"] += 1
        if entity["status"] == "target":
            first["status"] = "target"
        first["group"] = first["group"] or entity["group"]
        first["known"] += [q for q in entity["known"] if q not in first["known"]]
        first["unknown"] = first["unknown"] or entity["unknown"]
        if _PRECEDENCE[entity["distinction"]] > _PRECEDENCE[first["distinction"]]:
            first["distinction"] = entity["distinction"]

    kept = list(merged.values())
    for entity in kept:
        if entity["distinction"] == "conflict" and len(entity["known"]) < 2:
            counts["distinction"] += 1
            dropped_values.append("conflict (fewer than two known quotes)")
            entity["distinction"] = None
        if entity["status"] == "target" and entity["unknown"] is None:
            counts["unanchored"] += 1
        if entity["unknown"] is not None and entity["distinction"] is None:
            counts["distinction_missing"] += 1  # every target with an unknown takes one (no null fallback)

    events: dict[str, dict[str, Any]] = {}
    if counts["surface"]:
        events["TASK_ENTITY_DROPPED_UNSAFE"] = {"count": counts["surface"]}
    quotes = counts["quote_not_in_request"] + counts["unknown_on_given"]
    if quotes:
        events["TASK_ENTITY_QUOTE_DROPPED"] = {"count": quotes, "not_in_request": counts["quote_not_in_request"],
                                               "unknown_on_given": counts["unknown_on_given"]}
    if counts["distinction"]:
        events["TASK_ENTITY_DISTINCTION_DROPPED"] = {"count": counts["distinction"], "values": dropped_values}
    if counts["text"]:
        events["TASK_ENTITY_TEXT_DROPPED"] = {"count": counts["text"]}
    if counts["merged"]:
        events["TASK_ENTITY_MERGED"] = {"count": counts["merged"]}
    if counts["unanchored"]:
        events["TASK_ENTITY_TARGET_UNANCHORED"] = {"count": counts["unanchored"]}
    if counts["distinction_missing"]:
        events["TASK_ENTITY_DISTINCTION_MISSING"] = {"count": counts["distinction_missing"]}
    return kept, events


def reading(distinction: str) -> str:
    """The host's wording of a distinction, labeled as BOOTSTRAP's judgment."""
    return f"{distinction}: {DISTINCTION_READINGS[distinction]} (the extraction step's reading, not a fact)"


def forwarded(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """``TASK_ENTITIES`` as later stages receive it: five keys, the relation holding the quotes."""
    out = []
    for entity in entities:
        relation = None
        if entity["known"] or entity["unknown"]:
            relation = {"known": list(entity["known"]), "unknown": entity["unknown"],
                        "distinction": reading(entity["distinction"]) if entity["distinction"] else None}
        out.append({"surface": entity["surface"], "kind": entity["kind"], "status": entity["status"],
                    "group": entity["group"], "relation": relation})
    return out


def _relation_lines(entity: dict[str, Any], indent: str) -> list[str]:
    lines = []
    if entity["known"]:
        lines.append(f"{indent}stated: " + "; ".join(f'"{quote}"' for quote in entity["known"]))
    if entity["unknown"]:
        lines.append(f'{indent}asked: "{entity["unknown"]}"')
    if entity["distinction"]:
        lines.append(f"{indent}extraction step's reading: {DISTINCTION_READINGS[entity['distinction']]}")
    return lines


def render(entities: list[dict[str, Any]]) -> list[str]:
    """The drafting context's entity lines: each entity, its kind and role, then its quotes."""
    def head(entity: dict[str, Any]) -> str:
        return f"{entity['surface']} ({entity['kind']}) [{entity['status'].upper()}]"

    def same(a: dict[str, Any], b: dict[str, Any]) -> bool:
        return all(a[k] == b[k] for k in ("kind", "status", "known", "unknown", "distinction"))

    grouped: dict[str | None, list[dict[str, Any]]] = {}
    for entity in entities:
        grouped.setdefault(entity["group"], []).append(entity)
    lines: list[str] = []
    for group, items in grouped.items():
        if not group:
            for entity in items:
                lines.append(f"- {head(entity)}")
                lines += _relation_lines(entity, "    ")
            continue
        first = items[0]
        if all(same(entity, first) for entity in items):
            surfaces = ", ".join(entity["surface"] for entity in items)
            lines.append(f"- Group [{group}] [{first['status'].upper()}]: {surfaces} ({first['kind']})")
            lines += _relation_lines(first, "    ")
        else:
            lines.append(f"- Group [{group}]:")
            for entity in items:
                lines.append(f"  - {head(entity)}")
                lines += _relation_lines(entity, "      ")
    return lines

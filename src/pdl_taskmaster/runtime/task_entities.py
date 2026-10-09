"""The host's checks on BOOTSTRAP's task entities (ledger L100, schema v2; docs/plans/ENTITY_REDESIGN.md).

Everything here is deterministic. ``violations`` reads what the model wrote against the
entity rules: the first reply that breaks one is rejected with feedback naming each
violation (the single wire retry), and on the retry ``enforce`` drops only the offending
items. ``check`` then keeps a name, alias or quote only when it is one continuous piece
of the request (``quotes.RequestText``), keeping the request's own text; merges entities
that name the same thing; derives each entity's role (a target when the model wrote an
``unknown``); and applies ``distinction`` (implicit, undetermined, conflict), BOOTSTRAP's
one closed judgment, which later stages read in the host's fixed wording, labeled as a
judgment.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from pdl_taskmaster.runtime.quotes import RequestText, fold_key
from pdl_taskmaster.runtime.wire_payloads import ENTITY_DISTINCTIONS

# The host's own wording for each distinction; the model only ever chooses the word.
DISTINCTION_READINGS = {
    "implicit": "to be worked out from what the request states; a stated value is not assumed to be the answer",
    "undetermined": "what the request states may not be enough to settle it",
    "conflict": "the quoted statements about it may contradict each other",
}
_PRECEDENCE = {None: 0, "implicit": 1, "undetermined": 2, "conflict": 3}  # a merge never hides a gap

# English personal, possessive, reflexive, demonstrative and interrogative pronouns. A closed
# grammatical class, so this is schema validation, not a task word list (L100 rule 6 and (c);
# plan 4.1, ADR-0018). A pronoun is never a name, because what it refers to would have to be
# resolved by interpretation; as an alias it is tied to its referent. Matched against the whole
# name; single letters are exempt ("I" is also a symbol). English only.
PRONOUNS = frozenset({
    "i", "me", "my", "mine", "myself", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves", "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what",
})


def is_pronoun(name: object) -> bool:
    text = " ".join(str(name or "").split()).casefold()
    return len(text) > 1 and text in PRONOUNS


# --- the entity rules, on what the model wrote -------------------------------------------------

def _label(group: dict[str, Any], index: int) -> str:
    return f'group "{group["name"]}"' if group.get("name") else f"unnamed group {index}"


def _entity_problems(entity: dict[str, Any], where: str) -> list[str]:
    name = entity.get("name") or ""
    out = []
    if is_pronoun(name):
        out.append(f'{where}entity "{name}": a pronoun is never a name; list the thing it refers to and give '
                   'the pronoun as its alias')
    if not entity.get("known") and not entity.get("unknown"):
        out.append(f'{where}entity "{name}": it has no quote; every entity has at least one, in known or unknown')
    return out


def _group_problems(group: dict[str, Any], index: int, sources: RequestText) -> tuple[list[str], list[str]]:
    """(problems with the group itself, groups written inside it)."""
    label = _label(group, index)
    nested = [f"{label} contains another group ({inner}); a group holds entities only, one level"
              for inner in group.get("nested") or []]
    out = []
    name = group.get("name")
    if name and is_pronoun(name):
        out.append(f"{label}: a pronoun is never a name; set name to null and give the pronoun as an alias")
    elif name and sources.locate(name) is None:
        out.append(f"{label}: its name is not found word for word in the request")
    if not group.get("known"):
        out.append(f"{label}: it has no known quote stating the set")
    elif not name:
        quotes = RequestText(*group["known"])
        out += [f'{label}: member "{member.get("name")}" is not named in any of its known quotes'
                for member in group.get("members") or [] if quotes.locate(member.get("name")) is None]
    return out, nested


def violations(entities: dict[str, Any], sources: RequestText) -> list[str]:
    """Each way the reply breaks the entity rules, as a sentence naming the item."""
    out: list[str] = []
    for index, group in enumerate(entities.get("groups") or [], 1):
        problems, nested = _group_problems(group, index, sources)
        out += nested + problems
        for member in group.get("members") or []:
            out += _entity_problems(member, f"in {_label(group, index)}, ")
    for entity in entities.get("entities") or []:
        out += _entity_problems(entity, "")
    return out


def enforce(entities: dict[str, Any], sources: RequestText) -> tuple[dict[str, Any], list[str]]:
    """After the retry: drop only what breaks a rule. An entity that breaks one is dropped; a
    group that breaks one loses its label, and its members stay as entities."""
    reasons: list[str] = []
    groups: list[dict[str, Any]] = []
    loose: list[dict[str, Any]] = []
    for index, group in enumerate(entities.get("groups") or [], 1):
        problems, nested = _group_problems(group, index, sources)
        reasons += nested + problems
        members = []
        for member in group.get("members") or []:
            found = _entity_problems(member, f"in {_label(group, index)}, ")
            reasons += found
            if not found:
                members.append(member)
        if problems:
            loose += members
        else:
            groups.append({**group, "members": members, "nested": []})
    for entity in entities.get("entities") or []:
        found = _entity_problems(entity, "")
        reasons += found
        if not found:
            loose.append(entity)
    return {"groups": groups, "entities": loose}, reasons


# --- the host check ---------------------------------------------------------------------------

def _absorb(first: dict[str, Any], other: dict[str, Any]) -> None:
    """Merge ``other`` into ``first``: a target if either is, quotes combined, the stronger distinction."""
    if other["status"] == "target":
        first["status"] = "target"
    first["known"] += [q for q in other["known"] if q not in first["known"]]
    first["unknown"] = first["unknown"] or other["unknown"]
    if _PRECEDENCE[other["distinction"]] > _PRECEDENCE[first["distinction"]]:
        first["distinction"] = other["distinction"]
    first["alias"] += [a for a in other["alias"]
                       if a not in first["alias"] and fold_key(a) != fold_key(first["name"])]


def check(entities: dict[str, Any], sources: RequestText,
          sanitize: Callable[[str], str]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """The entities that survive the checks, as ``{"groups", "entities"}``, and the events to
    record (name -> payload, nonzero only)."""
    counts: Counter[str] = Counter()
    alias_drops: Counter[str] = Counter()
    dropped_values: list[str] = []

    def quote(copy: object) -> str | None:
        found = sources.locate(copy)
        return None if found is None else sanitize(found).strip()

    def quotes(written: list[str]) -> list[str]:
        kept: list[str] = []
        for copy in written or []:
            found = quote(copy)
            if found is None:
                counts["quote_not_in_request"] += 1
            elif found not in kept:
                kept.append(found)
        return kept

    def aliases(written: list[str], own_quotes: list[str]) -> list[str]:
        kept: list[str] = []
        for copy in written or []:
            found = quote(copy)
            if found is None:
                alias_drops["not_in_request"] += 1
            elif is_pronoun(found) and (not own_quotes or RequestText(*own_quotes).locate(found) is None):
                alias_drops["pronoun_outside_quotes"] += 1  # what shows who it means is its owner's quote
            elif found not in kept:
                kept.append(found)
        return kept

    def one(entity: dict[str, Any]) -> dict[str, Any] | None:
        name = sources.locate(entity.get("name"))
        if name is None:
            counts["name"] += 1
            return None
        for note in entity.get("dropped") or []:
            if note.startswith("distinction:"):
                counts["distinction"] += 1
                dropped_values.append(note.split(":", 1)[1])
            else:
                counts["text"] += 1
        known = quotes(entity.get("known") or [])
        written = entity.get("unknown")
        unknown = None
        if written:
            unknown = quote(written)
            if unknown is None:
                counts["quote_not_in_request"] += 1  # it stays a target: a slip never makes a target a given
        distinction = entity.get("distinction") if entity.get("distinction") in ENTITY_DISTINCTIONS else None
        if distinction and unknown is None:
            counts["distinction"] += 1
            dropped_values.append(f"{distinction} (no kept unknown)")
            distinction = None
        return {
            "name": sanitize(name).strip(),
            "kind": entity.get("kind") or "identifier",
            "status": "target" if written else "given",
            "alias": aliases(entity.get("alias") or [], [*known, *([unknown] if unknown else [])]),
            "known": known, "unknown": unknown, "distinction": distinction,
        }

    groups: list[dict[str, Any]] = []
    loose: list[dict[str, Any]] = []
    unnamed = 0
    for group in entities.get("groups") or []:
        members = [kept for kept in map(one, group.get("members") or []) if kept]
        name = sources.locate(group["name"]) if group.get("name") else None
        known = quotes(group.get("known") or [])
        anchored = name is not None or (bool(known) and all(
            RequestText(*known).locate(member["name"]) is not None for member in members))
        if (group.get("name") and name is None) or not anchored:
            counts["group"] += 1  # the label goes; its members stay as entities
            loose += members
            continue
        if not members:
            counts["group"] += 1
            continue
        label = sanitize(name).strip() if name else None
        if label is None:
            unnamed += 1
        groups.append({"name": label, "label": label or f"__g{unnamed}__",
                       "alias": aliases(group.get("alias") or [], known), "known": known, "members": members})
    loose += [kept for kept in map(one, entities.get("entities") or []) if kept]

    # Merge: one entity per thing, by name, then by an alias that is another entity's name.
    everyone = [member for group in groups for member in group["members"]] + loose
    removed: set[int] = set()
    by_key: dict[str, dict[str, Any]] = {}
    for entity in everyone:
        first = by_key.setdefault(fold_key(entity["name"]), entity)
        if first is not entity:
            _absorb(first, entity)
            removed.add(id(entity))
            counts["merged"] += 1
    for entity in everyone:
        if id(entity) in removed:
            continue
        kept_alias = []
        for alias in entity["alias"]:
            other = by_key.get(fold_key(alias))
            if other is None or other is entity or id(other) in removed:
                kept_alias.append(alias)
            elif other["kind"] == entity["kind"]:
                _absorb(entity, other)
                removed.add(id(other))
                by_key[fold_key(alias)] = entity
                counts["merged"] += 1
                kept_alias.append(alias)
            else:
                alias_drops["kind_mismatch"] += 1  # identity only: both entities stay
        entity["alias"] = kept_alias
    # A pronoun claimed by two owners is ambiguous: dropped from both.
    owners: dict[str, list[dict[str, Any]]] = {}
    for owner in [*groups, *(e for e in everyone if id(e) not in removed)]:
        for alias in owner["alias"]:
            if is_pronoun(alias):
                owners.setdefault(fold_key(alias).casefold(), []).append(owner)
    for key, claimed in owners.items():
        if len(claimed) > 1:
            for owner in claimed:
                before = len(owner["alias"])
                owner["alias"] = [a for a in owner["alias"] if fold_key(a).casefold() != key]
                alias_drops["ambiguous_pronoun"] += before - len(owner["alias"])

    kept_groups = []
    for group in groups:
        group["members"] = [m for m in group["members"] if id(m) not in removed]
        if group["members"]:
            kept_groups.append(group)
        else:
            counts["group"] += 1
    kept = {"groups": kept_groups, "entities": [e for e in loose if id(e) not in removed]}
    for entity in members_of(kept):
        if entity["distinction"] == "conflict" and len(entity["known"]) < 2:
            counts["distinction"] += 1
            dropped_values.append("conflict (fewer than two known quotes)")
            entity["distinction"] = None
        if entity["status"] == "target" and entity["unknown"] is None:
            counts["unanchored"] += 1
        if entity["unknown"] is not None and entity["distinction"] is None:
            counts["distinction_missing"] += 1  # every target with an unknown takes one (no null fallback)

    events: dict[str, dict[str, Any]] = {}
    if counts["name"]:
        events["TASK_ENTITY_DROPPED_UNSAFE"] = {"count": counts["name"]}
    if counts["quote_not_in_request"]:
        events["TASK_ENTITY_QUOTE_DROPPED"] = {"count": counts["quote_not_in_request"]}
    if counts["distinction"]:
        events["TASK_ENTITY_DISTINCTION_DROPPED"] = {"count": counts["distinction"], "values": dropped_values}
    if counts["text"]:
        events["TASK_ENTITY_TEXT_DROPPED"] = {"count": counts["text"]}
    if counts["merged"]:
        events["TASK_ENTITY_MERGED"] = {"count": counts["merged"]}
    if sum(alias_drops.values()):
        events["TASK_ENTITY_ALIAS_DROPPED"] = {"count": sum(alias_drops.values()), **dict(sorted(alias_drops.items()))}
    if counts["group"]:
        events["TASK_ENTITY_GROUP_DROPPED"] = {"count": counts["group"]}
    if counts["unanchored"]:
        events["TASK_ENTITY_TARGET_UNANCHORED"] = {"count": counts["unanchored"]}
    if counts["distinction_missing"]:
        events["TASK_ENTITY_DISTINCTION_MISSING"] = {"count": counts["distinction_missing"]}
    return kept, events


def members_of(kept: dict[str, Any]) -> list[dict[str, Any]]:
    """Every kept entity: each group's members, then the standalone entities."""
    return [member for group in kept["groups"] for member in group["members"]] + list(kept["entities"])


# --- what later stages receive -------------------------------------------------------------------

def reading(distinction: str) -> str:
    """The host's wording of a distinction, labeled as BOOTSTRAP's judgment."""
    return f"{distinction}: {DISTINCTION_READINGS[distinction]} (the extraction step's reading, not a fact)"


def _forwarded_entity(entity: dict[str, Any]) -> dict[str, Any]:
    return {"name": entity["name"], "kind": entity["kind"], "status": entity["status"], "alias": list(entity["alias"]),
            "known": list(entity["known"]), "unknown": entity["unknown"],
            "distinction": reading(entity["distinction"]) if entity["distinction"] else None}


def forwarded(kept: dict[str, Any]) -> list[dict[str, Any]]:
    """``TASK_ENTITIES`` as later stages receive it: each group, holding its members, then each
    standalone entity. A group the request does not name carries the host's label (``__g1__``)."""
    out: list[dict[str, Any]] = [
        {"group": group["label"], "alias": list(group["alias"]), "known": list(group["known"]),
         "members": [_forwarded_entity(member) for member in group["members"]]}
        for group in kept["groups"]
    ]
    return out + [_forwarded_entity(entity) for entity in kept["entities"]]


def _entity_lines(entity: dict[str, Any], indent: str) -> list[str]:
    lines = [f"{indent}- {entity['name']} ({entity['kind']}) [{entity['status'].upper()}]"]
    inner = indent + "    "
    if entity["alias"]:
        lines.append(f"{inner}also called: " + "; ".join(f'"{alias}"' for alias in entity["alias"]))
    if entity["known"]:
        lines.append(f"{inner}stated: " + "; ".join(f'"{quote}"' for quote in entity["known"]))
    if entity["unknown"]:
        lines.append(f'{inner}asked: "{entity["unknown"]}"')
    if entity["distinction"]:
        lines.append(f"{inner}extraction step's reading: {DISTINCTION_READINGS[entity['distinction']]}")
    return lines


def render(kept: dict[str, Any]) -> list[str]:
    """The drafting context's entity lines: each group with its members, then each standalone
    entity; every entity with its kind and role, then its quotes."""
    lines: list[str] = []
    for group in kept["groups"]:
        head = f"- group {group['label']}"
        if group["alias"]:
            head += " (also called " + ", ".join(f'"{alias}"' for alias in group["alias"]) + ")"
        names = ", ".join(m["name"] + (" [TARGET]" if m["status"] == "target" else "") for m in group["members"])
        lines.append(f"{head} {{ {names} }}")
        if group["known"]:
            lines.append("    stated: " + "; ".join(f'"{quote}"' for quote in group["known"]))
        for member in group["members"]:
            lines += _entity_lines(member, "  ")
    for entity in kept["entities"]:
        lines += _entity_lines(entity, "")
    return lines

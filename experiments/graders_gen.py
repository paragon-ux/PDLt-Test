"""Graders for the generated families whose catalogue graders are not parametric.

G-KK and G-HG copy the catalogue graders for 16-03 and 16-07 exactly, including
their regular expressions, with the expected answer read from the item's solution
file instead of being hard-coded. An isomorph is then graded the way its template
is, quirks included, and the gate's audit treats both the same way. G-SS, G-LS and
G-HP need no copy: their catalogue graders already read the instance from the
prompt.
"""
from __future__ import annotations

import re
from typing import Any

from graders import FAIL, MANUAL, PASS

ROLES = ("knight", "knave")


def grade_knights(corpus: str, solution: dict[str, Any]) -> tuple[str, str]:
    """As graders.grade_knights_and_knaves, for any names and expected roles."""
    low = corpus.lower()
    expected = {name.lower(): role for name, role in solution["answer"].items()}
    said = {name: {role for role in ROLES
                   if re.search(rf"\b{name}\b\s*(?:is|:|=|-)\s*(?:a\s+)?{role}\b", low)} for name in expected}
    if said == {name: {role} for name, role in expected.items()}:
        return PASS, ", ".join(f"{name.upper()} {role}" for name, role in expected.items())
    if any(roles == {other} for name, roles in said.items() for other in ROLES if other != expected[name]):
        return FAIL, f"wrong role stated: {said}"
    return MANUAL, f"roles stated: {said}"


def grade_house_owner(corpus: str, solution: dict[str, Any]) -> tuple[str, str]:
    """As graders.grade_house_grid, for any expected fish owner."""
    low = corpus.lower()
    expected = solution["answer"]["fish_owner"].lower()
    owners = {name for name in ("ana", "ben", "cleo")
              if re.search(rf"\b{name}\b[^.\n]{{0,40}}\bfish\b|\bfish\b[^.\n]{{0,40}}\b{name}\b"
                           rf"|\"fish_owner\"\s*:\s*\"{name}\"", low)}
    if owners == {expected}:
        return PASS, f"{expected.capitalize()} owns the fish"
    if owners and expected not in owners:
        return FAIL, f"fish owner stated as {sorted(owners)}"
    return MANUAL, f"fish owner unclear: {sorted(owners)}"

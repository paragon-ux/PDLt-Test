"""Graders for the generated families whose catalogue graders are not parametric.

G-KK uses the catalogue's manual adjudication for final roles and exhaustive
reasoning. G-HG copies the catalogue grader for 16-07 with the expected answer
read from the item's solution file. G-SS, G-LS and G-HP need no copy: their
catalogue graders already read the instance from the prompt.
"""
from __future__ import annotations

import re
from typing import Any

from graders import FAIL, MANUAL, PASS, grade_knights_and_knaves


def grade_knights(corpus: str, solution: dict[str, Any]) -> tuple[str, str]:
    """Keep generated deductions on the same adjudication path as the template."""
    return grade_knights_and_knaves(corpus, "")


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

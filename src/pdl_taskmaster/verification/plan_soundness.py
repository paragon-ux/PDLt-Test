"""Pseudocode Grammar Lint (PDL-05 / PDL-06 / PDL-08).

Deterministic harness-level validator that inspects Prompt and Response Plan
pseudocode before the review gate. It checks notation only:

- PDL-05: no invented fielded schema (``TASK:``, ``STEP 1:``, ``OUTPUT:``).
- PDL-06: no programming-language imitation via code fences.
- PDL-08: no deferral or drafting meta-markers ("deferred to execution", "TBD").

It never inspects which algorithm, tool, or method a plan chooses (GUARD-01,
GUARD-03, GUARD-04): an analytical derivation, a proof, and a code plan are all
equally valid.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_DEFERRAL_PATTERNS = re.compile(
    r"(?i)\b(?:(?:deferred|defer|postponed?|left|delegated?)\s+to\s+(?:the\s+)?execution(?:\s+stage|\s+phase)?|"
    r"TBD|to\s+be\s+determined(?:\s+at\s+execution)?|"
    r"(?:method|algorithm|approach|strategy)\s+(?:is\s+)?(?:undecided|left\s+open|determined\s+at\s+execution))\b"
)

_CONTROL_KEYWORDS = (
    "IF", "ELSE", "ENDIF", "WHILE", "ENDWHILE", "FOR", "ENDFOR",
    "REPEAT", "UNTIL", "CASE", "ENDCASE",
)

# A line opening with an all-caps label followed by a colon is an invented field.
_FIELDED_PREFIX = re.compile(
    r"^\s*(?:[-*]\s+)?(?!(?:" + "|".join(_CONTROL_KEYWORDS) + r")\b)([A-Z][A-Z0-9 _-]{1,24}):(?:\s|$)"
)

_CODE_FENCE = re.compile(r"^\s*```", re.MULTILINE)


@dataclass(frozen=True)
class PlanSoundnessResult:
    valid: bool
    violations: list[str]

    @property
    def feedback(self) -> str:
        if self.valid:
            return ""
        return "Pseudocode notation requirement: " + "; ".join(self.violations)


def validate_plan_soundness(
    plan_body: str,
    *,
    requires_verified_execution: bool = True,
) -> PlanSoundnessResult:
    """Lint pseudocode notation. ``requires_verified_execution`` is accepted for
    call-site compatibility and deliberately ignored: the lint is task-neutral."""
    text = plan_body or ""
    violations: list[str] = []

    if not text.strip():
        violations.append("Pseudocode is empty.")

    deferral = _DEFERRAL_PATTERNS.search(text)
    if deferral:
        violations.append(
            f"Contains deferral marker '{deferral.group(0).strip()}' (PDL-08); "
            "state the operations directly."
        )

    if _CODE_FENCE.search(text):
        violations.append("Contains a code fence (PDL-06); use ordinary structured English.")

    for line in text.splitlines():
        m = _FIELDED_PREFIX.match(line)
        if m:
            violations.append(
                f"Line begins with invented field label '{m.group(1)}:' (PDL-05); "
                "state each operation directly."
            )
            break

    return PlanSoundnessResult(valid=not violations, violations=violations)

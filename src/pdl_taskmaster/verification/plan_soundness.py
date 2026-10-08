"""Pseudocode Grammar Lint (PDL-05 / PDL-06 / PDL-08 / PLAN-10).

Deterministic harness-level validator that inspects Prompt and Response Plan
pseudocode before the review gate, on first drafts and on revisions. It checks
notation only, and it is the one place these rules are enforced: a violation
gets one redraft carrying the finding, never a wire failure and never a host
rewrite of the body (AUTH-05). A violation that survives the redraft is
published unchanged with a host note at the review gate naming each finding and
its line (``line_violations``).

- PDL-05: no invented fielded schema (``TASK:``, ``STEP 1:``, inline ``OUTPUT:``).
- PDL-06: no programming-language imitation via code fences.
- PDL-08: no deferral or drafting meta-markers ("deferred to execution", "TBD",
  "do not perform any computation; only describe the task").
- PLAN-10: no placeholder steps ("insert placeholders for the results").

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

# Drafting meta-rules: the artifact describing its own stage instead of the task.
_META_RULE_PATTERNS = re.compile(
    r"(?i)\b(?:"
    r"(?:do\s+not|never)\s+(?:perform|execute|calculate|compute|solve|do|produce|implement|write|code|create|build)\s+(?:any\s+|the\s+)?(?:actual\s+)?"
    r"(?:computation|computations|work|calculation|calculations|verification|task|search|result|data\s+structure|code|tests?|implementation)|"
    r"(?:do\s+not|never)\s+implement\b|"
    r"(?:only\s+(?:describe|specify|provide)|(?:describe|specify|provide)\s+only)\s+(?:the\s+)?(?:required\s+)?(?:task|result|output|deliverable|specification|spec|contracts?)|"
    r"without\s+performing\s+(?:any\s+|the\s+)?(?:actual\s+)?(?:computation|work|calculation|selection|search)|"
    r"no\s+(?:actual|algorithmic|substantive)\s+(?:computation|work|calculation)\s+(?:is\s+)?(?:performed|done)|"
    r"no\s+(?:code|code\s+emission|executable\s+code)\b|"
    r"(?:do\s+not|never)\s+(?:emit|generate|output)\s+code\b|"
    r"(?:contains?\s+)?no\s+executable\s+code\b|"
    r"(?:read|parse|examine|load|ingest|fetch|open)\s+(?:the\s+)?(?:task\s+specification|request\s+to\s+implement|available_execution_tools|confirmed_prompt_body|confirmed_plan_body|supplied_execution_input_source|result_ir|execution_contract)\b|"
    r"(?:at\s+this\s+stage|in\s+this\s+step)[;,]?\s*only\s+(?:specify|describe|state)"
    r")\b"
)

_PLACEHOLDER_PATTERNS = re.compile(
    r"(?i)\b(?:insert|leave|use)\s+placeholders?\s+for\s+(?:the\s+)?(?:substantive\s+)?(?:results?|values?|answers?|outputs?)\b"
)

# A field label in the middle of a line ("... OUTPUT: the list").
_INLINE_FIELD = re.compile(r"(?<=\S)\s+(OUTPUT|INCLUDE|INPUT|ACTION|RESULT|STATUS)\s*:\s")

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

    meta = _META_RULE_PATTERNS.search(text)
    if meta:
        violations.append(
            f"Contains drafting meta-rule '{meta.group(0).strip()}' (PDL-08); "
            "state what the result must be, not what this stage does."
        )

    placeholder = _PLACEHOLDER_PATTERNS.search(text)
    if placeholder:
        violations.append(
            f"Contains placeholder step '{placeholder.group(0).strip()}' (PLAN-10); "
            "state the operation that produces the result."
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
    else:
        inline = _INLINE_FIELD.search(text)
        if inline:
            violations.append(
                f"Contains inline field label '{inline.group(1)}:' (PDL-05); state each operation directly."
            )

    return PlanSoundnessResult(valid=not violations, violations=violations)


@dataclass(frozen=True)
class LineViolation:
    """One notation finding located on its line (1-based), for the host note at
    the review gate. ``text`` is the matched span, quoted back verbatim."""

    line: int
    clause: str
    kind: str
    text: str


def line_violations(body: str) -> list[LineViolation]:
    """Every notation finding in ``body`` with its line, every match on every line.

    A line-level view of the same patterns ``validate_plan_soundness`` uses (whose
    contract, one finding per pattern, is unchanged). It reports; it never edits
    the body (AUTH-05).
    """
    found: list[LineViolation] = []
    for number, line in enumerate((body or "").splitlines(), 1):
        for pattern, clause, kind in (
            (_DEFERRAL_PATTERNS, "PDL-08", "deferral"),
            (_META_RULE_PATTERNS, "PDL-08", "meta_rule"),
            (_PLACEHOLDER_PATTERNS, "PLAN-10", "placeholder"),
        ):
            for match in pattern.finditer(line):
                found.append(LineViolation(number, clause, kind, match.group(0).strip()))
        if _CODE_FENCE.match(line):
            found.append(LineViolation(number, "PDL-06", "fence", line.strip()))
        fielded = _FIELDED_PREFIX.match(line)
        if fielded:
            found.append(LineViolation(number, "PDL-05", "field_label", fielded.group(1) + ":"))
        else:
            for match in _INLINE_FIELD.finditer(line):
                found.append(LineViolation(number, "PDL-05", "field_label", match.group(1) + ":"))
    return found

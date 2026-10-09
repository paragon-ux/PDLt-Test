"""The representation of the confirmed route's two artifacts (experiment switch, ledger L97).

``pdl`` (the default) is the protocol as specified: Prompt Pseudocode and Response Plan
Pseudocode in PDL. ``nl`` writes the same two artifacts as natural-language prose, for the
PDL-versus-natural-language pilot, and changes nothing else:

- the format clauses (PDL-01 to PDL-08) are not shown;
- the artifacts are named "Prompt Interpretation" and "Response Plan" wherever the model
  reads their names (clauses, output-schema descriptions, drafting guidance, host feedback,
  System 1's fidelity question);
- the drafting guidance keeps every PROMPT and PLAN rule and every format-neutral operational
  rule, and replaces the notation rules with one prose-format rule;
- the host's notation lint skips its field-label check (PDL-05) and cites no PDL clause.

Stages, confirmation, authority (AUTH-03/04), EXECUTE's guidance, repairs and output grammar
are the same in both. The host shows the mode to the compiler as ``NL_REPRESENTATION_MODE``.
"""
from __future__ import annotations

import re

PDL = "pdl"
NL = "nl"
REPRESENTATIONS = (PDL, NL)

# Longest first: "Response Plan Pseudocode" before "Prompt Pseudocode".
_NL_TERMS = (
    ("RESPONSE_PLAN_PSEUDOCODE", "RESPONSE_PLAN"),
    ("PROMPT_PSEUDOCODE", "PROMPT_INTERPRETATION"),
    ("Response Plan Pseudocode", "Response Plan"),
    ("Prompt Pseudocode", "Prompt Interpretation"),
    ("prompt pseudocode", "prompt interpretation"),
)
_PDL_REFERENCE = re.compile(r",\s*PDL-0\d|\s*\(PDL-0\d(?:,\s*PDL-0\d)*\)")


def nl_terms(text: str) -> str:
    """The artifact names in ``text`` as the natural-language arm names them."""
    for old, new in _NL_TERMS:
        text = text.replace(old, new)
    return text


def is_format_clause(requirement_id: str) -> bool:
    """The PDL notation clauses, which the natural-language arm does not show."""
    return requirement_id.startswith("PDL-")


def _normative(pdl_guidance: str, prefix: str) -> str:
    lines = [nl_terms(line) for line in pdl_guidance.split("\n") if line.startswith(prefix)]
    return "\n".join(lines)


def nl_prompt_guidance(pdl_guidance: str) -> str:
    """DRAFT_PROMPT and REVISE_PROMPT guidance in the natural-language arm, from the PDL guidance."""
    return (
        "\n\nNORMATIVE GUIDELINES AND SPECIFICATION FOR THE PROMPT INTERPRETATION (PROMPT-01 to PROMPT-05):\n"
        + _normative(pdl_guidance, "PROMPT-")
        + "\n\nOPERATIONAL GUIDELINES FOR PROMPT DRAFTING:\n"
        "1. Write the prompt as a natural-language prompt interpretation in ordinary prose. Use clear sentences and "
        "paragraphs; ordinary headings or bullets are allowed for readability, but do not express it as pseudocode "
        "or as program-control-flow notation. Preserve the request's meaning; do not omit a constraint to make the "
        "text shorter.\n"
        "2. When the user asks to implement, write, develop, or create software, data structures, algorithms, or "
        "tests, state that the deliverable is to be implemented or created, and preserve the target language (e.g. "
        "'in Python') and interface contracts.\n"
        "3. The user prompt is the communicative frame, not a runtime data stream: do not describe reading the task "
        "specification or the request.\n"
        "4. Describe function parameters, mathematical constants, and data structure inputs as parameters to accept "
        "or take, not as streams to read; mention reading only for explicit runtime stream or file input.\n"
        "5. " + _PDL_REFERENCE.sub("", nl_terms(_item(pdl_guidance, "7. ")))
    )


def nl_plan_guidance(pdl_guidance: str) -> str:
    """DRAFT_PLAN and REVISE_PLAN guidance in the natural-language arm, from the PDL guidance."""
    return (
        "\n\nNORMATIVE GUIDELINES AND SPECIFICATION FOR THE RESPONSE PLAN (PLAN-01 to PLAN-10):\n"
        + _normative(pdl_guidance, "PLAN-")
        + "\n\nOPERATIONAL GUIDELINES FOR RESPONSE PLAN DRAFTING:\n"
        "1. Write the plan as a natural-language response plan: ordinary-language sequential instructions with "
        "clear conditions and dependencies. Ordinary headings or bullets are allowed, but do not express the plan "
        "as pseudocode or program-control-flow notation.\n"
        "2. " + _item(pdl_guidance, "3. ") + "\n"
        "3. " + _item(pdl_guidance, "4. ") + "\n"
        "4. " + _PDL_REFERENCE.sub("", nl_terms(_item(pdl_guidance, "5. ")))
    )


def _item(pdl_guidance: str, number: str) -> str:
    """One numbered operational guideline of the PDL guidance, without its number."""
    (line,) = [line for line in pdl_guidance.split("\n") if line.startswith(number)]
    return line[len(number):]

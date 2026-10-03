def _with_note(body: str, host_note: str | None) -> str:
    return f"{body}\n\n{host_note}" if host_note else body


def prompt_artifact(body: str, host_note: str | None = None) -> str:
    return f"Prompt Pseudocode\n\n{_with_note(body, host_note)}\n\nConfirm or correct this interpretation."


def plan_artifact(body: str, host_note: str | None = None) -> str:
    return f"Response Plan Pseudocode\n\n{_with_note(body, host_note)}\n\nConfirm or correct this response approach."


_LINT_NOTE_TAIL = {
    "meta_rule": "is a drafting meta-rule; /revise to remove it",
    "deferral": "is a deferral marker; /revise to state the operation instead",
    "placeholder": "is a placeholder step; /revise to state the operation that produces the result",
    "fence": "opens a fenced block; /revise to use structured English",
    "field_label": "is an invented field label; /revise to state the operation directly",
}


def lint_note(violations: list, fallback: list[str] | None = None) -> str:
    """Factual host note for pseudocode that still fails the notation lint after
    its one redraft: every finding with its line. The body itself is unchanged
    (AUTH-05); the user corrects it with /revise."""
    lines = []
    for v in violations:
        quoted = v.text if len(v.text) <= 80 else v.text[:77] + "..."
        lines.append(f'[host] {v.clause}: line {v.line} "{quoted}" {_LINT_NOTE_TAIL[v.kind]}')
    if not lines:
        lines = [f"[host] {finding}" for finding in fallback or []]
    return "\n".join(lines)


_ADVANCEMENT_FEEDBACK = {
    "solution_actions": "it adds no solution action or deduction beyond the prompt's own lines",
    "constraints_addressed": "it repeats or ignores the conditions that keep the task from being solved directly "
                             "instead of stating how the approach handles them",
    "advances": "it does not show how the result will be obtained",
}

_ADVANCEMENT_NOTE = {
    "solution_actions": "adds no step beyond the prompt's own",
    "constraints_addressed": "does not say how it handles the task's constraints",
    "advances": "does not show how the result will be reached",
}


def plan_advancement_feedback(failed: list[str]) -> str:
    """Operator correction for a plan that restates the prompt: which checks failed,
    never how to solve the task."""
    reasons = "; ".join(_ADVANCEMENT_FEEDBACK[c] for c in failed if c in _ADVANCEMENT_FEEDBACK)
    return (
        "Response plan requirement (PLAN-02, minimum sufficient procedure): the plan restates the confirmed "
        f"prompt instead of exposing an approach: {reasons}. State how the result will be obtained; do not "
        "state the result itself (PLAN-04)."
    )


def plan_advancement_note(failed: list[str]) -> str:
    """Factual host note at the plan review for a plan that still restates the prompt."""
    reasons = "; ".join(_ADVANCEMENT_NOTE[c] for c in failed if c in _ADVANCEMENT_NOTE)
    return f"[host] PLAN-02: this plan restates the prompt ({reasons}); /revise to ask for the approach"


def deferred_substantive() -> str:
    return "I’ll address that substantive task question after the current confirmations are complete."


def review_clarification() -> str:
    return "Please clarify how that message should affect the current review."


def waiting_input_guidance(description: str | None) -> str:
    """How to proceed while execution waits for input: never a dead end."""
    awaited = (description or "").strip() or "the input the execution asked for"
    return (
        f"The execution is waiting for input: {awaited}\n"
        "Reply with that input, use /revise <feedback> to change the task, or /stop to cancel."
    )


def provisional_note() -> str:
    """Factual note on a result whose witness no program run by the host reproduced."""
    return "[host] Witness not reproduced by a program run; unverified."


def literal_witness_note() -> str:
    """Factual note on a result whose printed witness values are literals in the program."""
    return "[host] Witness values are written into the program, not computed; unverified."


def cancelled() -> str:
    return "Cancelled."

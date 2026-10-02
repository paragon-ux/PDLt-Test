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


def cancelled() -> str:
    return "Cancelled."

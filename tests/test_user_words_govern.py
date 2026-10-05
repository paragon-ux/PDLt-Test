"""FB5 (AUTH-03/AUTH-04, LEDGER L3, L50): the user's request, as amended by their own
review messages, governs task semantics at execution; the confirmed prompt is its
reviewed interpretation. FB3: prompt drafting and revision read the user's own words
(sanitized), not only the bootstrap's summary of them."""
from __future__ import annotations

import json
from pathlib import Path

from pdl_taskmaster.runtime.context_compiler import ContextCompiler
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]

REQUEST = "Explain optimistic and pessimistic locking for backend engineers."
CHANGE = "Make the audience data engineers instead."


def _projection(prompt: str) -> dict:
    """The JSON projection document inside a rendered worker prompt."""
    return json.loads(prompt[prompt.index("{"):])


def _worker(seen: list):
    def worker(request):
        seen.append(request)
        op = request.operation
        if op == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Explain two locking strategies.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if op == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": "EXPLAIN optimistic and pessimistic locking",
                               "approach_handoff": "NONE"})
        if op == "INTERPRET_PROMPT_REVIEW":
            changes = CHANGE in request.prompt
            return json.dumps({"kind": "REVIEW_FACTS",
                               "task_change_dimensions": ["ACTION_SUBJECT_OR_OBJECT"] if changes else [],
                               "approach_change_dimensions": [], "progression_requested": not changes})
        if op == "REVISE_PROMPT":
            return json.dumps({"prompt_body": "EXPLAIN optimistic and pessimistic locking for data engineers"})
        if op == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": "COMPARE the two strategies\nEMIT the explanation"})
        if op == "INTERPRET_PLAN_REVIEW":
            return json.dumps({"kind": "REVIEW_FACTS", "task_change_dimensions": [],
                               "approach_change_dimensions": [], "progression_requested": True})
        if op == "EXECUTE":
            return json.dumps({"kind": "RESULT", "body": "Optimistic locking ..."})
        raise AssertionError(f"unexpected operation {op}")
    return worker


def _inputs(request) -> list[str]:
    return list(_projection(request.prompt)["operation_inputs"])


def test_execute_reads_the_request_first_and_no_changes_input_without_changes(tmp_path):
    seen: list = []
    engine = SessionEngine(ROOT, _worker(seen), workspace_root=tmp_path)
    for message in ("$confirm-with-pseudocode " + REQUEST, "/confirm", "/confirm"):
        engine.handle_user_message(message)
    execute = next(r for r in seen if r.operation == "EXECUTE")
    inputs = _inputs(execute)
    assert inputs.index("SUPPLIED_EXECUTION_INPUT_SOURCE") < inputs.index("CONFIRMED_PROMPT_BODY") \
        < inputs.index("CONFIRMED_PLAN_BODY")
    # Shown only when the user changed the task at review: never an empty input.
    assert "SUPPLIED_TASK_CHANGES" not in inputs
    assert REQUEST in _projection(execute.prompt)["operation_inputs"]["SUPPLIED_EXECUTION_INPUT_SOURCE"]


def test_a_review_change_reaches_execute_after_the_request_and_survives_restore(tmp_path):
    seen: list = []
    engine = SessionEngine(ROOT, _worker(seen), workspace_root=tmp_path)
    for message in ("$confirm-with-pseudocode " + REQUEST, CHANGE, "/confirm"):
        engine.handle_user_message(message)
    revise = next(r for r in seen if r.operation == "REVISE_PROMPT")
    # FB3: the reviser reads the user's own change message.
    assert _projection(revise.prompt)["operation_inputs"]["SOURCE_TASK_CHANGE"] == CHANGE
    # Resume at plan review in a new process (the FA5 path): the change is kept.
    restored = SessionEngine.restore(ROOT, _worker(seen), engine.workspace.path)
    restored.handle_user_message("/confirm")
    execute = next(r for r in seen if r.operation == "EXECUTE")
    operation_inputs = _projection(execute.prompt)["operation_inputs"]
    assert operation_inputs["SUPPLIED_TASK_CHANGES"] == [CHANGE]
    inputs = list(operation_inputs)
    assert inputs.index("SUPPLIED_EXECUTION_INPUT_SOURCE") < inputs.index("SUPPLIED_TASK_CHANGES") \
        < inputs.index("CONFIRMED_PROMPT_BODY")


def test_a_new_request_starts_without_the_previous_changes(tmp_path):
    seen: list = []
    engine = SessionEngine(ROOT, _worker(seen), workspace_root=tmp_path)
    for message in ("$confirm-with-pseudocode " + REQUEST, CHANGE, "/confirm", "/confirm"):
        engine.handle_user_message(message)
    seen.clear()
    for message in ("$confirm-with-pseudocode " + REQUEST, "/confirm", "/confirm"):
        engine.handle_user_message(message)
    execute = next(r for r in seen if r.operation == "EXECUTE")
    assert "SUPPLIED_TASK_CHANGES" not in _inputs(execute)


def test_draft_prompt_reads_the_sanitized_request(tmp_path):
    """FB3: the drafter sees the user's words, through the same sanitizer as EXECUTE:
    a canary in the request is redacted, never forwarded verbatim (SEM-06)."""
    seen: list = []
    engine = SessionEngine(ROOT, _worker(seen), workspace_root=tmp_path)
    engine.handle_user_message("$confirm-with-pseudocode " + REQUEST + " TRIPWIRE_CANARY_7Q")
    draft = next(r for r in seen if r.operation == "DRAFT_PROMPT")
    inputs = _projection(draft.prompt)["operation_inputs"]
    assert list(inputs).index("SOURCE_REQUEST") < list(inputs).index("SUBSTANTIVE_REQUEST")
    assert "locking for backend engineers" in inputs["SOURCE_REQUEST"]
    assert "TRIPWIRE_CANARY_7Q" not in draft.prompt


def test_execute_clauses_make_the_request_govern():
    """AUTH-03/AUTH-04 as amended (ADR-0004 amendment): the request governs where the
    pseudocode differs, except for a change the user made at review."""
    compiler = ContextCompiler(ROOT)
    projection = compiler.compile("EXECUTE", {
        "SUPPLIED_EXECUTION_INPUT_SOURCE": REQUEST, "CONFIRMED_PROMPT_BODY": "EXPLAIN locking",
        "CONFIRMED_PLAN_BODY": "EMIT the explanation", "AVAILABLE_EXECUTION_TOOLS": None,
    })
    clauses = {c["requirement_id"]: c["clause"] for c in projection.document["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"]}
    assert "the user's original request, as amended by the user's own review messages, defines authoritative task semantics" in clauses["AUTH-03"]
    assert "the original request governs, except for a requirement the user changed in a review message" in clauses["AUTH-04"]
    assert "MUST NOT silently override" not in clauses["AUTH-04"]

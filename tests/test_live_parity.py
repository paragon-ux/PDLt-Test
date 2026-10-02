"""Live REPL parity with the catalogue (A2, A3) and REPL defects (B1, B2), on the
engine with a scripted System 2 and a scripted System 1."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]


class ScriptedSys1:
    """System 1 stand-in: one (choice, confidence) per question name; unknown
    questions get a low-confidence answer that passes no gate."""

    is_configured, model = True, "fake-sys1"

    def __init__(self, **answers: tuple[str, float]):
        self.answers = {"route": ("APPLY_PROTOCOL", 0.97), "problem_class": ("STANDARD_EXECUTION", 0.97), **answers}
        self.requests: list = []

    def call(self, request):
        self.requests.append(request)
        name = next(iter(request.questions))
        choice, confidence = self.answers.get(name, ("UNSET", 0.3))
        others = [c for c in request.questions[name].choices if c != choice]
        probabilities = {choice: confidence, **{c: round((1 - confidence) / max(len(others), 1), 4) for c in others}}
        return {"answers": {name: {"choice": choice, "confidence": confidence, "probabilities": probabilities}}}, 1.0


class ScriptedWorker:
    """System 2 stand-in: per-operation replies (a list is consumed in order, the
    last reply repeats); every request is recorded."""

    DEFAULTS = {
        "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "The user asks for a result.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []},
        "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "COMPUTE the requested result", "approach_handoff": "NONE"},
        "REVISE_PROMPT": {"prompt_body": "COMPUTE the revised result"},
        "DRAFT_PLAN": {"neutral_plan_body": "DERIVE the result\nRETURN it"},
        "REVISE_PLAN": {"neutral_plan_body": "DERIVE the result again\nRETURN it"},
        "EXECUTE": {"kind": "RESULT", "body": "The result is 1/3."},
        "INTERPRET_EXECUTION_INPUT": {"kind": "UNRESOLVED"},
    }

    def __init__(self, **replies):
        self.replies = {**self.DEFAULTS, **replies}
        self.requests: list = []

    def __call__(self, request):
        self.requests.append(request)
        reply = self.replies[request.operation]
        if isinstance(reply, list):
            reply = reply.pop(0) if len(reply) > 1 else reply[0]
        if callable(reply):
            reply = reply(request)
        return reply if isinstance(reply, str) else json.dumps(reply)

    def calls(self, operation: str) -> list:
        return [r for r in self.requests if r.operation == operation]


def engine_with(tmp_path, worker: ScriptedWorker, sys1=None) -> SessionEngine:
    return SessionEngine(ROOT, worker, workspace_root=tmp_path, sys1_client=sys1)


def events(engine: SessionEngine, kind: str | None = None) -> list[dict]:
    found = []
    for path in sorted(engine.workspace.path.rglob("events.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if kind is None or event.get("kind") == kind:
                found.append(event)
    return found


def ask(engine: SessionEngine, text: str):
    return engine.handle_user_message("$confirm-with-pseudocode " + text)


# --------------------------------------------------------------------------- A2


def test_problem_class_event_records_verdict_confidence_and_gating(tmp_path):
    """A STANDARD verdict and a VERIFIED one below the floor both route standard;
    the event must say which it was."""
    engine = engine_with(tmp_path, ScriptedWorker(), ScriptedSys1(problem_class=("VERIFIED_EXECUTION", 0.6)))
    ask(engine, "a fully specified question")
    (event,) = events(engine, "PROBLEM_CLASS_CLASSIFIED")
    assert event["payload"]["requires_verified_execution"] is False
    assert event["payload"]["verdict"] == "VERIFIED_EXECUTION"
    assert event["payload"]["confidence"] == 0.6 and event["payload"]["passed_gating"] is False


def _grader_phrases() -> list[str]:
    import sys

    sys.path.insert(0, str(ROOT))
    import graders

    phrases: list[str] = []
    for name in ("_INFEASIBLE", "_NONEXISTENT", "_CUTOFF"):
        phrases.extend(getattr(graders, name))
    # Phrase lists written inline in the category-13 graders.
    phrases += ["impossible", "cannot", "can't", "no such algorithm", "does not exist", "not possible",
                "n log n", "lower bound", "doctor", "physician", "not able", "unable", "not a substitute",
                "not provide", "step budget", "could not be produced", "cannot be certified",
                "could not be certified"]
    return phrases


def _manifest_tag_phrases() -> list[str]:
    tags: set[str] = set()
    for line in (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            tags.update(t.lower() for t in json.loads(line)["tags"] if "-" in t)
    return sorted(tags)


def host_notes() -> list[str]:
    """Every host note a deliverable or review gate can carry, rendered."""
    from pdl_taskmaster.runtime import presentation

    from pdl_taskmaster.verification.plan_soundness import LineViolation

    kinds = ("meta_rule", "deferral", "placeholder", "fence", "field_label")
    lint = presentation.lint_note([LineViolation(1, "PDL-08", kind, "x") for kind in kinds])
    return [presentation.provisional_note(), *lint.splitlines(), presentation.waiting_input_guidance("x")]


def test_host_notes_satisfy_no_grader_phrase_and_name_no_manifest_tag():
    """A host note is factual, never a way to game a phrase grader: a note saying
    "unresolved" would turn any provisional result into an infeasibility pass."""
    import re

    for note in host_notes():
        low = note.lower()
        for phrase in _grader_phrases():
            assert phrase not in low, (note, phrase)
        for tag in _manifest_tag_phrases():
            assert not re.search(r"\b" + r"[\s_-]".join(map(re.escape, tag.split("-"))) + r"\b", low), (note, tag)


# --------------------------------------------------------------------------- A3

STICK_PROMPT = (
    "READ the problem statement\n"
    "CALCULATE the requested probability\n"
    "DO NOT perform the calculation.\n"
    "RETURN the probability as a simplified fraction"
)


def test_residual_meta_rule_is_published_unchanged_with_a_line_note(tmp_path):
    """Live stick sessions: the redraft kept "DO NOT perform the calculation", the
    engine logged PROMPT_LINT_UNRESOLVED and published it with no word to the user;
    the deliverable then refused to compute."""
    draft = {"kind": "PROMPT", "prompt_body": STICK_PROMPT, "approach_handoff": "NONE"}
    worker = ScriptedWorker(DRAFT_PROMPT=[draft])
    engine = engine_with(tmp_path, worker, ScriptedSys1())
    response = ask(engine, "a fully specified question")
    assert len(worker.calls("DRAFT_PROMPT")) == 2  # one redraft, as before
    assert engine.controller.state.current_prompt.body == STICK_PROMPT  # no host rewrite (AUTH-05)
    assert '[host] PDL-08: line 3 "DO NOT perform the calculation" is a drafting meta-rule; /revise to remove it' \
        in response.text
    assert response.text.index("[host]") > response.text.index("RETURN the probability")
    (event,) = events(engine, "PROMPT_LINT_UNRESOLVED")
    assert event["payload"]["lines"] == [
        {"line": 3, "clause": "PDL-08", "kind": "meta_rule", "text": "DO NOT perform the calculation"}
    ]
    assert event["payload"]["host_note"] is True


def test_every_residual_finding_is_named_with_its_line(tmp_path):
    body = "TASK: compute the value\nDERIVE it\nINSERT placeholders for the results\nTBD"
    worker = ScriptedWorker(DRAFT_PROMPT=[{"kind": "PROMPT", "prompt_body": body, "approach_handoff": "NONE"}])
    response = ask(engine_with(tmp_path, worker, ScriptedSys1()), "a task")
    notes = [line for line in response.text.splitlines() if line.startswith("[host]")]
    assert notes == [
        '[host] PDL-05: line 1 "TASK:" is an invented field label; /revise to state the operation directly',
        '[host] PLAN-10: line 3 "INSERT placeholders for the results" is a placeholder step; '
        "/revise to state the operation that produces the result",
        '[host] PDL-08: line 4 "TBD" is a deferral marker; /revise to state the operation instead',
    ]


def test_clean_redraft_carries_no_note(tmp_path):
    clean = {"kind": "PROMPT", "prompt_body": "CALCULATE the requested probability", "approach_handoff": "NONE"}
    dirty = {"kind": "PROMPT", "prompt_body": STICK_PROMPT, "approach_handoff": "NONE"}
    engine = engine_with(tmp_path, ScriptedWorker(DRAFT_PROMPT=[dirty, clean]), ScriptedSys1())
    response = ask(engine, "a task")
    assert "[host]" not in response.text and not events(engine, "PROMPT_LINT_UNRESOLVED")


def test_plan_path_names_residual_findings_too(tmp_path):
    plan = "DERIVE the value\nDO NOT perform the calculation\nRETURN it"
    worker = ScriptedWorker(DRAFT_PLAN=[{"neutral_plan_body": plan}])
    engine = engine_with(tmp_path, worker, ScriptedSys1())
    ask(engine, "a task")
    response = engine.handle_user_message("/confirm")
    assert len(worker.calls("DRAFT_PLAN")) == 2
    assert engine.controller.state.current_plan.body == plan
    assert '[host] PDL-08: line 2 "DO NOT perform the calculation" is a drafting meta-rule' in response.text
    (event,) = events(engine, "PLAN_LINT_UNRESOLVED")
    assert event["payload"]["operation"] == "DRAFT_PLAN" and event["payload"]["lines"][0]["line"] == 2


# --------------------------------------------------------------------------- B1

FIRST = "Report the strengths and weaknesses of this REPL"
SECOND = "are you capable of editing the readme of this repo? C:/repo/README.md"


def _bootstrap_echo(request):
    """BOOTSTRAP_ANALYSIS whose summary names the raw content it read."""
    raw = request.prompt.split('"RAW_UNTRUSTED_CONTENT"', 1)[-1][:400]
    marker = "readme" if "readme" in raw.lower() else ("nothing else" if "nothing else" in raw else "other")
    return {"kind": "ANALYSIS", "task_summary": f"The user asks about the {marker} matter in this message.",
            "approach_notes": "", "risk_notes": "", "task_entities": []}


def _two_turns(tmp_path, sys1, second=SECOND):
    worker = ScriptedWorker(BOOTSTRAP_ANALYSIS=_bootstrap_echo,
                            EXECUTE={"kind": "RESULT", "body": "Strengths: fast. Weaknesses: terse."})
    engine = engine_with(tmp_path, worker, sys1)
    for message in ("$confirm-with-pseudocode " + FIRST, "/confirm", "/confirm"):
        engine.handle_user_message(message)
    assert engine.controller.state.stage.value == "CLOSED_SUCCESS"
    first_calls = len(worker.requests)
    ask(engine, second)
    return engine, worker, worker.requests[first_calls:]


def test_follow_up_is_merged_with_the_previous_request(tmp_path):
    engine, _, calls = _two_turns(tmp_path, ScriptedSys1(follow_up=("FOLLOW_UP", 0.95)), "incorrect, try again")
    bootstrap = next(c for c in calls if c.operation == "BOOTSTRAP_ANALYSIS")
    assert FIRST in bootstrap.prompt and "incorrect, try again" in bootstrap.prompt
    assert "PREVIOUS_DELIVERABLE" in bootstrap.prompt
    (event,) = events(engine, "FOLLOW_UP_ROUTED")
    assert event["payload"] == {"verdict": "FOLLOW_UP", "confidence": 0.95, "passed_gating": True,
                                "merged": True, "fallback": None}


def test_new_request_starts_clean(tmp_path):
    """Session log: a question about the README was merged into the earlier REPL
    critique, and the drafted prompt carried both tasks."""
    sys1 = ScriptedSys1(follow_up=("NEW_REQUEST", 0.95))
    engine, worker, calls = _two_turns(tmp_path, sys1)
    bootstrap = next(c for c in calls if c.operation == "BOOTSTRAP_ANALYSIS")
    assert SECOND in bootstrap.prompt and FIRST not in bootstrap.prompt
    assert "PREVIOUS_DELIVERABLE" not in bootstrap.prompt and "Strengths: fast" not in bootstrap.prompt
    routed = [r.state["request"] for r in sys1.requests if "problem_class" in r.questions]
    assert routed[-1] == SECOND
    (event,) = events(engine, "FOLLOW_UP_ROUTED")
    assert event["payload"]["merged"] is False and event["payload"]["verdict"] == "NEW_REQUEST"
    assert event["payload"]["passed_gating"] is True and event["payload"]["confidence"] == 0.95
    # A narrowing correction is compiled from the correction alone and reaches
    # REVISE_PROMPT; neither the previous request nor its deliverable is there.
    revise_from = len(worker.requests)
    engine.handle_user_message("/revise edit the readme, nothing else")
    later = worker.requests[revise_from:]
    correction_read = next(c for c in later if c.operation == "BOOTSTRAP_ANALYSIS")
    assert "edit the readme, nothing else" in correction_read.prompt
    assert "PREVIOUS_DELIVERABLE" not in correction_read.prompt
    revise = next(c for c in later if c.operation == "REVISE_PROMPT")
    assert "readme matter" in revise.prompt
    assert FIRST not in revise.prompt and "Strengths: fast" not in revise.prompt


@pytest.mark.parametrize("sys1, fallback", [
    (None, "sys1_unavailable"),
    (ScriptedSys1(follow_up=("NEW_REQUEST", 0.6)), "below_floor"),
])
def test_without_a_gated_decision_the_message_is_merged(tmp_path, sys1, fallback):
    """Session 20261001-122654: the merge is the safe default."""
    engine, _, calls = _two_turns(tmp_path, sys1)
    bootstrap = next(c for c in calls if c.operation == "BOOTSTRAP_ANALYSIS")
    assert FIRST in bootstrap.prompt and SECOND in bootstrap.prompt
    (event,) = events(engine, "FOLLOW_UP_ROUTED")
    assert event["payload"]["merged"] is True and event["payload"]["fallback"] == fallback


# --------------------------------------------------------------------------- B2

ASK_FOR_FILE = {"kind": "REQUEST_INPUT", "body": "Please provide the current contents of README.md.",
                "expected_type": "text", "description": "the current contents of README.md"}


def _waiting(tmp_path, **replies):
    replies.setdefault("EXECUTE", [ASK_FOR_FILE, {"kind": "RESULT", "body": "Done."}])
    worker = ScriptedWorker(**replies)
    engine = engine_with(tmp_path, worker, ScriptedSys1())
    for message in ("$confirm-with-pseudocode add a smiley to README.md", "/confirm", "/confirm"):
        engine.handle_user_message(message)
    assert engine.controller.state.stage.value == "WAITING_INPUT"
    return engine, worker


def test_plain_reply_at_waiting_input_is_used_as_the_input(tmp_path):
    """Session log: every free-text reply got "Please clarify how that message
    should affect the current review." forever."""
    engine, worker = _waiting(tmp_path)
    reply = "you have to edit it without me providing the contents of the file"
    response = engine.handle_user_message(reply)
    assert response.text == "Done."
    executes = worker.calls("EXECUTE")
    assert len(executes) == 2 and reply in executes[1].prompt  # as SUPPLIED_EXECUTION_INPUT_SOURCE
    assert events(engine, "EXECUTION_INPUT_DEFAULTED")


def test_waiting_input_never_repeats_a_dead_end(tmp_path):
    from pdl_taskmaster.runtime import presentation

    engine, worker = _waiting(tmp_path, EXECUTE=[ASK_FOR_FILE])
    for message in ("this is a test", "ok", "still testing"):
        response = engine.handle_user_message(message)
        assert response.text != presentation.review_clarification()
        assert engine.controller.state.stage.value == "WAITING_INPUT"
    assert len(worker.calls("EXECUTE")) == 4  # each reply was offered as the input


def test_interpretation_failure_at_waiting_input_still_uses_the_reply(tmp_path):
    engine, worker = _waiting(tmp_path, INTERPRET_EXECUTION_INPUT="not json at all")
    assert engine.handle_user_message("here are the contents").text == "Done."


@pytest.mark.parametrize("message", ["/confirm", "   "])
def test_waiting_input_guidance_says_how_to_proceed(tmp_path, message):
    engine, worker = _waiting(tmp_path)
    before = len(worker.requests)
    response = engine.handle_user_message(message)
    assert "the current contents of README.md" in response.text
    assert "/revise <feedback>" in response.text and "/stop" in response.text
    assert len(worker.requests) == before  # no model call, no exception


def test_revise_at_waiting_input_changes_the_task(tmp_path):
    """/revise mapped to REVISE_APPROACH, which WAITING_INPUT does not allow:
    the REPL printed a ControllerError."""
    engine, worker = _waiting(tmp_path)
    response = engine.handle_user_message("/revise only describe the edit")
    assert engine.controller.state.stage.value == "PROMPT_REVIEW"
    assert response.text.startswith("Prompt Pseudocode") and worker.calls("REVISE_PROMPT")


def test_unresolved_review_clarification_is_waiting_input_guidance(tmp_path):
    from pdl_taskmaster.controller.mechanical_controller import NextAction, Transition

    engine, _ = _waiting(tmp_path)
    response = engine._apply_transition(Transition(NextAction.REQUEST_REVIEW_CLARIFICATION), "x", [])
    assert "waiting for input" in response.text

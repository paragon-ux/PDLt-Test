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
    return [presentation.provisional_note(), *lint.splitlines()]


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

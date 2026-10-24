"""Task-type conformance kit (L124 D4): structural and behavioural checks a task type, built-in or outside, runs
against itself. Offline: a scripted worker and a scripted System 1 drive real sessions; no model is called.

    from pdl_taskmaster.extensions.conformance import check_task_type

    report = check_task_type(my_declaration, sample={"body": "...", "result_ir": {...}})
    assert report.ok, report

A task type that checks a witness supplies a sample deliverable: an EXECUTE result whose program prints a witness its
verifier accepts. Every other task type may rely on the default sample, a plain text deliverable.
"""
from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_SAMPLE = {"body": "A deliverable that states the requested result."}
PROBE_REQUEST = "Carry out the stated task on the given inputs."
LEVELS = ("unverified", "contract_checked", "host_verified")


@dataclass
class Check:
    name: str
    problems: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


@dataclass
class ConformanceReport:
    subject: str
    checks: list[Check] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)

    def problems(self) -> list[str]:
        return [f"{c.name}: {p}" for c in self.checks for p in c.problems]

    def __str__(self) -> str:
        lines = [f"task type {self.subject}: {'conforms' if self.ok else 'does not conform'}"]
        for check in self.checks:
            lines.append(f"  {'pass' if check.passed else 'FAIL'}  {check.name}")
            lines.extend(f"        - {p}" for p in check.problems)
        return "\n".join(lines)


class ScriptedSys1:
    """System 1 that lets every request through Phase 0 and answers each classification as told:
    ``answers`` maps a question name to (choice, confidence). Other questions get an answer outside their choices,
    which every recipe treats as undecided. Records each request."""

    is_configured = True
    model = "scripted-sys1"

    def __init__(self, answers: Mapping[str, tuple[str, float]] | None = None):
        self.answers = dict(answers or {})
        self.requests: list[dict[str, Any]] = []

    def call(self, request: Any) -> tuple[dict[str, Any], float]:
        name = next(iter(request.questions))
        self.requests.append(request.to_dict())
        if name == "route":
            choice, confidence, other = "APPLY_PROTOCOL", 0.97, "BYPASS"
        elif name in self.answers:
            choice, confidence = self.answers[name]
            other = next((c for c in request.questions[name].choices if c != choice), "OTHER")
        else:
            choice, confidence, other = "UNDECIDED", 0.97, "OTHER"
        return {"answers": {name: {"choice": choice, "confidence": confidence,
                                   "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}}}, 1.0


class ScriptedWorker:
    """Answers every operation of both routes; EXECUTE and EXECUTE_UNCONFIRMED return ``execute``. Records each
    request's operation and full prompt."""

    def __init__(self, execute: Mapping[str, Any], sys1: Any = None, **attributes: Any):
        self.execute = dict(execute)
        self.sys1_client = sys1
        self.requests: list[tuple[str, str]] = []
        for name, value in attributes.items():
            setattr(self, name, value)

    def call(self, request: Any) -> Any:
        from pdl_taskmaster.providers.base import WorkerResult

        self.requests.append((request.operation, request.prompt))
        result = {"kind": "RESULT", **self.execute}
        replies = {
            "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "The user states a task to carry out.",
                                   "approach_notes": "", "risk_notes": "", "task_entities": []},
            "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "CARRY OUT the stated task\nRETURN the result",
                             "approach_handoff": "NONE"},
            "DRAFT_PLAN": {"neutral_plan_body": "PERFORM the task\nEMIT the result"},
            "EXECUTE": result,
            "EXECUTE_UNCONFIRMED": {"interpretation": "CARRY OUT the stated task", "approach": "PERFORM the task",
                                    **result},
        }
        return WorkerResult(json.dumps(replies[request.operation]))


def run_session(category: str | None, route: str, execute: Mapping[str, Any], *, sys1: Any = None,
                session_dir: Path | None = None, **worker_attributes: Any) -> tuple[Any, ScriptedWorker]:
    """One request through a session pinned to ``category`` on ``route``, every review confirmed. Returns the last
    TurnResult and the worker."""
    from pdl_taskmaster.api import Session

    worker = ScriptedWorker(execute, sys1 if sys1 is not None else ScriptedSys1(), **worker_attributes)
    with ExitStack() as stack:
        folder = session_dir or Path(stack.enter_context(tempfile.TemporaryDirectory())) / "session"
        with Session.open(worker, folder, no_review=route == "unconfirmed", task_type=category,
                          mode="protocol") as session:
            return session.run(PROBE_REQUEST, confirm=True), worker


def _text_of(classification: Any) -> list[str]:
    if isinstance(classification, Mapping) and isinstance(classification.get("criterion"), str):
        return [classification["criterion"].strip()]
    return []


def check_task_type(subject: Mapping[str, Any] | str, *, sample: Mapping[str, Any] | None = None) -> ConformanceReport:
    """Run every check against a declaration (registered for the duration, then removed) or a registered
    category."""
    from pdl_taskmaster.extensions import task_types
    from pdl_taskmaster.extensions.profiles import ProfileViolation

    registry = task_types.REGISTRY
    with registry.scoped():
        if isinstance(subject, str):
            declaration = registry.get(subject).declaration if subject in registry else None
            report = ConformanceReport(subject)
            if declaration is None:
                report.checks.append(Check("profile", [f"no task type {subject!r} is registered"]))
                return report
        else:
            declaration = subject
            report = ConformanceReport(str(declaration.get("category")) if isinstance(declaration, Mapping)
                                       else repr(declaration))
        structural = Check("profile")
        report.checks.append(structural)
        try:
            task_type = registry.register(declaration, replace=True)
        except ProfileViolation as exc:
            structural.problems.extend(exc.problems)
            return report
        report.checks.append(_classification(task_type))
        if task_type.requires_witness and sample is None:
            report.checks.append(Check("sample", ["a task type that checks a witness supplies a sample deliverable "
                                                  "whose program prints a witness its verifier accepts"]))
            return report
        texts = _text_of(declaration["prompt"]["classification"])
        for route in sorted(task_type.routes):
            report.checks.append(_route(task_type, route, dict(sample or DEFAULT_SAMPLE), texts))
        if task_type.requires_witness:
            report.checks.append(_unreproduced(task_type, sorted(task_type.routes)[0], dict(sample)))
        return report


def _classification(task_type: Any) -> Check:
    """A recipe is asked, selects its own category when sure, and nothing when unsure or failing."""
    from pdl_taskmaster.extensions import task_types

    check = Check("classification")
    if task_type.recipe is None:
        return check
    route = sorted(task_type.routes)[0]
    question = next(iter(task_type.recipe.build_request({"request": PROBE_REQUEST}).questions))
    others = [t for t in task_types.REGISTRY.classified(route) if t is not task_type]
    # Earlier recipes answer that the request is not theirs, so this one is asked.
    quiet = {next(iter(t.recipe.build_request({"request": PROBE_REQUEST}).questions)): ("UNDECIDED", 0.97)
             for t in others}
    sure = task_types.select(PROBE_REQUEST, ScriptedSys1({**quiet, question: (task_type.selects, 0.97)}), route)
    if sure.task_type is not task_type:
        check.problems.append(f"a sure classification ({task_type.selects!r}, 0.97) selected "
                              f"{sure.task_type.category!r}")
    unsure = task_types.select(PROBE_REQUEST, ScriptedSys1({**quiet, question: (task_type.selects, 0.6)}), route)
    if unsure.task_type is task_type:
        check.problems.append("a classification below the floor (0.6) selected it")
    failing = task_types.select(PROBE_REQUEST, ScriptedSys1(quiet), route)  # its question gets no valid answer
    if failing.task_type is task_type:
        check.problems.append("an undecided classification selected it")
    return check


def _route(task_type: Any, route: str, sample: dict[str, Any], texts: list[str]) -> Check:
    """The sample closes on this route with a published result; only declared operations run; no classification
    text reaches the solver; the provenance names the category and claims no more than the binding allows."""
    check = Check(f"route:{route}")
    try:
        result, worker = run_session(task_type.category, route, sample)
    except Exception as exc:
        check.problems.append(f"the session failed ({type(exc).__name__}: {exc})")
        return check
    if result.stage not in ("CLOSED_SUCCESS", "CLOSED_UNVERIFIED"):
        check.problems.append(f"the sample did not close with a published result: stage {result.stage}, exit "
                              f"{result.exit_status}; text: {(result.text or '')[:300]}")
        return check
    stray = sorted({op for op, _ in worker.requests} - task_type.operations)
    if stray:
        check.problems.append(f"operations outside the declaration ran: {stray}")
    for text in texts:
        if any(text in prompt for _, prompt in worker.requests):
            check.problems.append("classification text reached a solver request (GUARD-01)")
    record = result.provenance or {}
    verification = record.get("verification") or {}
    if verification.get("problem_class") != task_type.category:
        check.problems.append(f"provenance names problem class {verification.get('problem_class')!r}")
    ceiling = "host_verified" if task_type.requires_witness else "contract_checked"
    if LEVELS.index(verification.get("level", "unverified")) > LEVELS.index(ceiling):
        check.problems.append(f"provenance claims {verification.get('level')} above {ceiling}")
    if task_type.requires_witness and verification.get("level") != "host_verified":
        check.problems.append(f"the sample's witness was not host-verified (level {verification.get('level')}); "
                              "a sample prints a witness its verifier accepts")
    return check


def _unreproduced(task_type: Any, route: str, sample: dict[str, Any]) -> Check:
    """A witness no program printed is never host-verified, whatever the verifier says."""
    check = Check("unreproduced-witness")
    ir = dict(sample.get("result_ir") or {})
    ir["witness"] = {"polarity": "positive", "data": {"stated": "only in the Result IR"}}
    probe = {"body": "The result is stated without a program.", "result_ir": ir}
    try:
        result, _ = run_session(task_type.category, route, probe, max_repairs=0)
    except Exception as exc:
        check.problems.append(f"the session failed ({type(exc).__name__}: {exc})")
        return check
    level = ((result.provenance or {}).get("verification") or {}).get("level")
    if result.stage == "CLOSED_SUCCESS" and level == "host_verified":
        check.problems.append("a witness stated only in the Result IR closed host_verified")
    return check

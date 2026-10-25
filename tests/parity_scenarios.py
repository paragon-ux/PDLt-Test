"""Scenarios for the task-type parity check (L124 D2): each runs one built-in task type through a session and
records what the worker and System 1 received, the stage and exit status after each message, the events and the
provenance. ``tests/fixtures/task_type_parity.json`` originated before task types were wired into the engine.
SG-02 refreshes only worker fingerprints for the authorized CommonMark capability text, after verifying exact
historical equivalence with only that text reversed. Other baseline fields remain unchanged. Regeneration
requires reviewing intentional request changes; it is not an automatic response to a failing parity test.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "task_type_parity.json"
# The interpreter the fixture was recorded under. The sandbox declares the host's own interpreter in what the
# worker and System 1 receive (sandbox.PYTHON_VERSION feeds only those declarations, never which interpreter runs),
# so the hashes below key that declaration to this version, as recorded replay re-keys its prompts
# (providers/fixtures.py). Everything else in the request is hashed as sent, and the programs run on this host.
FIXTURE_PYTHON = "3.11"
# Provenance fields the parity comparison leaves out: the running package's version, which the test checks
# against pdl_taskmaster.__version__ instead of against the version the fixture was recorded at.
RELEASE_DEPENDENT = ("pdlt_version",)

PROMPT = "COMPUTE the answer to the stated task\nRETURN the answer"
PLAN = "DERIVE the answer\nEMIT the answer"
REQUEST = "Solve the stated task."
POSITIVE = ("import json\nvalues = [a * b for a in range(2, 5) for b in range(3, 6)]\n"
            "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'largest': max(values)}}))")
NEGATIVE = ("import json\nnodes = 0\nfor x in range(27):\n    nodes += 1\n"
            "print('WITNESS: ' + json.dumps({'polarity': 'negative', 'basis': 'search', "
            "'search_exhausted': True, 'nodes_explored': nodes, 'method': 'enumeration'}))")
IR = {"files": [], "reconciliation": [
    {"requirement": "R1", "status": "satisfied", "evidence": {"path": "execution://body"}},
    {"requirement": "R2", "status": "satisfied", "evidence": {"path": "execution://body"}}], "open_defects": []}
BRIEF = {"kind": "RESULT", "approach": "Multiply each pair of the given ranges and keep the largest product.",
         "data_structures": ["the running largest product"],
         "step_estimate": {"iterations": 9, "steps_per_iteration": 10, "basis": "one iteration per pair"},
         "invariants": ["the running value is the largest product seen so far"],
         "self_checks": ["recompute the largest product directly"], "execution_entities": []}


def _as_recorded(text: str) -> str:
    """The text with this host's interpreter declaration keyed to the fixture's (FIXTURE_PYTHON)."""
    from pdl_taskmaster.verification.sandbox import PYTHON_VERSION

    return text.replace(f"Python {PYTHON_VERSION} ", f"Python {FIXTURE_PYTHON} ")


def _sha(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(_as_recorded(text).encode("utf-8")).hexdigest()[:16]


def _manifest_as_recorded(request) -> dict:
    """The manifest with its projection digest recomputed over the re-keyed projection document. The digest the
    engine wrote is checked first: it must be the digest of the document as sent."""
    manifest = dict(request.manifest)
    document = json.dumps(request.projection.document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert manifest["projection_sha256"] == hashlib.sha256(document.encode("utf-8")).hexdigest()
    manifest["projection_sha256"] = hashlib.sha256(_as_recorded(document).encode("utf-8")).hexdigest()
    return manifest


def comparable(record: dict) -> dict:
    """A scenario's record without the release-dependent provenance fields."""
    provenance = record.get("provenance")
    if not provenance:
        return record
    return {**record, "provenance": {k: v for k, v in provenance.items() if k not in RELEASE_DEPENDENT}}


class Sys1:
    """System 1 that lets every request through Phase 0, answers the problem class as told, and records each
    request it receives."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, problem_class: str, confidence: float = 0.97):
        self.problem_class, self.confidence = problem_class, confidence
        self.requests: list[dict] = []

    def call(self, request):
        name = next(iter(request.questions))
        self.requests.append({"question": name, "request": _sha(request.to_dict())})
        choice = "APPLY_PROTOCOL" if name == "route" else self.problem_class
        other = "BYPASS" if name == "route" else (
            "STANDARD_EXECUTION" if choice == "VERIFIED_EXECUTION" else "VERIFIED_EXECUTION")
        confidence = 0.97 if name == "route" else self.confidence
        return {"answers": {name: {"choice": choice, "confidence": confidence,
                                   "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}}}, 1.0


class Worker:
    """Answers each operation; records each request as its operation and hashes of its prompt and projection."""

    def __init__(self, execute: dict, sys1: Sys1 | None, **attributes):
        from pdl_taskmaster.providers.base import WorkerResult

        self._result = WorkerResult
        self.execute = execute
        self.sys1_client = sys1
        self.requests: list[dict] = []
        for name, value in attributes.items():
            setattr(self, name, value)

    def call(self, request):
        manifest = getattr(request, "manifest", None)
        self.requests.append({"operation": request.operation, "prompt": _sha(request.prompt),
                              "manifest": _sha(_manifest_as_recorded(request)) if manifest is not None else None})
        replies = {
            "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "The user states a task to solve.",
                                   "approach_notes": "", "risk_notes": "", "task_entities": []},
            "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"},
            "DRAFT_PLAN": {"neutral_plan_body": PLAN},
            "DRAFT_EXECUTE": BRIEF,
            "EXECUTE": self.execute,
            "EXECUTE_UNCONFIRMED": {"kind": "RESULT", "interpretation": "COMPUTE the stated answer",
                                    "approach": "RUN the computation", **self.execute},
        }
        return self._result(json.dumps(replies[request.operation]))


def _result(body: str, ir: bool = True) -> dict:
    return {"kind": "RESULT", "body": body, **({"result_ir": IR} if ir else {})}


SCENARIOS = {
    # name: (problem class or None for no System 1, confidence, review route?, EXECUTE reply, worker attributes,
    #        messages: "run" = run(REQUEST, confirm=True), "send" = send(REQUEST))
    "standard-confirmed": ("STANDARD_EXECUTION", 0.97, True, _result("The answer is 42.", ir=False), {}, ["run"]),
    "standard-at-review": ("STANDARD_EXECUTION", 0.97, True, _result("The answer is 42.", ir=False), {}, ["send"]),
    "standard-unconfirmed": ("STANDARD_EXECUTION", 0.97, False, _result("The answer is 42.", ir=False), {},
                             ["send"]),
    "no-system-1": (None, 0.0, True, _result("The answer is 42.", ir=False), {}, ["run"]),
    "verified-below-floor": ("VERIFIED_EXECUTION", 0.6, True, _result("The answer is 42.", ir=False), {}, ["run"]),
    "verified-host-verified": ("VERIFIED_EXECUTION", 0.97, True, _result(POSITIVE), {}, ["run"]),
    "verified-negative": ("VERIFIED_EXECUTION", 0.97, True, _result(NEGATIVE), {}, ["run"]),
    "verified-cancelled": ("VERIFIED_EXECUTION", 0.97, True, _result("The answer is 42."), {"max_repairs": 1},
                           ["run"]),
    "verified-unconfirmed-brief": ("VERIFIED_EXECUTION", 0.97, False, _result(POSITIVE), {"draft_execute": True},
                                   ["send"]),
    "verified-confirmed-brief": ("VERIFIED_EXECUTION", 0.97, True, _result(POSITIVE), {"draft_execute": True},
                                 ["run"]),
}


def run(name: str, session_dir: Path) -> dict:
    from pdl_taskmaster.api import Session

    problem_class, confidence, review, execute, attributes, messages = SCENARIOS[name]
    sys1 = Sys1(problem_class, confidence) if problem_class else None
    worker = Worker(execute, sys1, **attributes)
    steps = []
    with Session.open(worker, session_dir, repo_root=ROOT, no_review=not review, mode="protocol") as session:
        for message in messages:
            result = session.run(REQUEST, confirm=True) if message == "run" else session.send(REQUEST)
            steps.append({"stage": result.stage, "exit_status": result.exit_status, "closed": result.closed,
                          "review": result.review, "refused": result.refused})
        workspace = session.host.engine.workspace
        events = [e["kind"] for e in workspace.read_events()] if workspace is not None else []
        provenance = dict(result.provenance or {})
    provenance.pop("closed_at_utc", None)
    return {"worker": worker.requests, "sys1": sys1.requests if sys1 else None, "steps": steps, "events": events,
            "provenance": provenance or None}


def run_all() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        return {name: run(name, Path(tmp) / name) for name in SCENARIOS}


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    if ".".join(map(str, sys.version_info[:2])) != FIXTURE_PYTHON:
        raise SystemExit(f"record the fixture under Python {FIXTURE_PYTHON} (FIXTURE_PYTHON), or change it with it")
    first, second = run_all(), run_all()
    assert first == second, "the scenarios are not deterministic"
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(first, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE} ({len(first)} scenarios)")

"""System 1 predicts step complexity; the prediction selects a step budget that the
sandbox enforces deterministically and that the solver is told."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.providers.sys1.recipes.execution_profile import ExecutionProfileRecipe
from pdl_taskmaster.runtime.session_engine import SessionEngine
from pdl_taskmaster.verification import sandbox as sandbox_module
from pdl_taskmaster.verification.sandbox import ExecutionBudget, ExecutionSandbox

ROOT = Path(__file__).resolve().parents[1]


def _answer(choice: str, confidence: float = 0.97) -> dict:
    other = "WITHIN_10M_STEPS" if choice != "WITHIN_10M_STEPS" else "WITHIN_100M_STEPS"
    return {"choice": choice, "confidence": confidence,
            "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}


class PredictingSys1:
    is_configured = True
    model = "fake-sys1"

    def __init__(self, prediction: str | None, confidence: float = 0.97):
        self.prediction, self.confidence = prediction, confidence

    def call(self, request):
        name = next(iter(request.questions))
        if name == "route":
            return {"answers": {name: _answer("APPLY_PROTOCOL")}}, 1.0
        if name == "execution_profile":
            if self.prediction is None:
                raise RuntimeError("sys1 down")
            return {"answers": {name: _answer(self.prediction, self.confidence)}}, 1.0
        return {"answers": {name: {"choice": "STANDARD_EXECUTION", "confidence": 0.97,
                                   "probabilities": {"STANDARD_EXECUTION": 0.97, "VERIFIED_EXECUTION": 0.03}}}}, 1.0


def _session(tmp_path, sys1, execute_body: str = "done"):
    executes: list = []

    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "A task.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": "COMPUTE the result", "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": "DERIVE the result"})
        executes.append(req)
        return json.dumps({"kind": "RESULT", "body": execute_body})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1)
    for message in ("$confirm-with-pseudocode compute it", "/confirm", "/confirm"):
        engine.handle_user_message(message)
    return engine, executes, list(engine.workspace._events)


def _dist(**probs: float) -> dict:
    labels = {"k100": "WITHIN_100K_STEPS", "m10": "WITHIN_10M_STEPS", "m100": "WITHIN_100M_STEPS", "beyond": "BEYOND_100M_STEPS"}
    probabilities = {labels[k]: v for k, v in probs.items()}
    top = max(probabilities, key=probabilities.get)
    return {"choice": top, "confidence": probabilities[top], "probabilities": probabilities}


@pytest.mark.parametrize(
    "answer, prediction, tier",
    [
        (_dist(k100=0.95, m10=0.05), "WITHIN_100K_STEPS", "MINIMAL"),
        (_dist(k100=0.5, m10=0.5), "WITHIN_10M_STEPS", "STANDARD"),  # split mass resolves upward
        (_dist(k100=0.6, m10=0.2, m100=0.2), "WITHIN_100M_STEPS", "HEAVY_COMPUTE"),
        (_dist(m100=0.9, beyond=0.1), "WITHIN_100M_STEPS", "HEAVY_COMPUTE"),
        (_dist(k100=0.25, m10=0.25, m100=0.25, beyond=0.25), "BEYOND_100M_STEPS", "HEAVY_COMPUTE"),
        ({"choice": "WITHIN_100K_STEPS", "confidence": 0.9}, "WITHIN_100K_STEPS", "MINIMAL"),
        ({"choice": "WITHIN_100K_STEPS", "confidence": 0.5}, "WITHIN_10M_STEPS", "STANDARD"),
        ({"choice": "HEAVY", "confidence": 0.99, "probabilities": {"HEAVY": 0.99}}, "WITHIN_10M_STEPS", "STANDARD"),
        ({}, "WITHIN_10M_STEPS", "STANDARD"),
    ],
)
def test_weighted_prediction_grants_the_smallest_sufficient_budget(answer, prediction, tier):
    recipe = ExecutionProfileRecipe()
    result = recipe.parse_response({"answers": {"execution_profile": answer}})
    assert recipe.map_to_wire(result) == {"prediction": prediction, "tier": tier}


def test_solver_is_told_the_predicted_step_budget(tmp_path):
    engine, executes, events = _session(tmp_path, PredictingSys1("BEYOND_100M_STEPS"))
    routed = next(e for e in events if e["kind"] == "EXECUTION_PROFILE_ROUTED")["payload"]
    assert routed["predicted_steps"] == "BEYOND_100M_STEPS" and routed["passed_gating"]
    assert routed["tier"] == "HEAVY_COMPUTE" and routed["step_limit"] == 100_000_000
    assert "at most 100,000,000 steps" in executes[0].prompt


@pytest.mark.parametrize("sys1", [None, PredictingSys1(None)])
def test_absent_system1_means_standard(tmp_path, sys1):
    engine, executes, _ = _session(tmp_path, sys1)
    assert engine._execution_budget.tier == "STANDARD"
    assert "at most 10,000,000 steps" in executes[0].prompt


def test_sandbox_enforces_the_routed_step_budget(tmp_path, monkeypatch):
    monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, "STANDARD", ExecutionBudget("STANDARD", 100_000, 30, 256 << 20))
    monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, "HEAVY_COMPUTE", ExecutionBudget("HEAVY_COMPUTE", 5_000_000, 30, 256 << 20))
    body = "t = 0\nfor i in range(100000):\n    t += i\nprint(t)"
    runs = {}
    for prediction in ("WITHIN_10M_STEPS", "WITHIN_100M_STEPS"):
        _, _, events = _session(tmp_path / prediction, PredictingSys1(prediction), execute_body=body)
        runs[prediction] = next(e for e in events if e["kind"] == "SANDBOX_RUN")["payload"]
    assert runs["WITHIN_10M_STEPS"]["step_budget_exceeded"] and not runs["WITHIN_10M_STEPS"]["timed_out"]
    assert not runs["WITHIN_100M_STEPS"]["step_budget_exceeded"] and runs["WITHIN_100M_STEPS"]["exit_code"] == 0


@pytest.mark.parametrize(
    "code",
    [
        "while True: pass",  # one-line loop
        "try:\n    while True: pass\nexcept BaseException:\n    pass",  # the program cannot catch the stop
        "import sys\ntry:\n    sys.settrace(None)\nexcept PermissionError:\n    pass\nwhile True: pass",
        "import threading\nt = threading.Thread(target=lambda: [0 for _ in iter(int, 1)])\nt.start(); t.join()",
    ],
)
def test_step_budget_cannot_be_evaded(code):
    run = ExecutionSandbox().run_code(code, step_limit=100_000, timeout=20)
    assert run.step_budget_exceeded and not run.timed_out


def test_step_budget_is_deterministic():
    code = "print(sum(i * i for i in range(20000)))"
    counts = []
    for limit in (60_000, 200_000):
        counts.append(ExecutionSandbox().run_code(code, step_limit=limit).step_budget_exceeded)
    assert counts == [True, False]
    assert ExecutionSandbox().run_code(code, step_limit=200_000).stdout.strip() == str(sum(i * i for i in range(20000)))


def test_host_declared_tools_are_not_overridden(tmp_path):
    declared = [{"name": "custom", "description": "host-provided"}]
    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None,
                           available_execution_tools=declared)
    engine.workspace = engine._new_workspace()
    engine._route_execution_profile("anything")
    assert engine.available_execution_tools == declared


def test_minimal_tier_is_declared_and_enforced(tmp_path):
    engine, executes, events = _session(tmp_path, PredictingSys1("WITHIN_100K_STEPS", 0.95),
                                        execute_body="t = 0\nfor i in range(10**6):\n    t += i")
    routed = next(e for e in events if e["kind"] == "EXECUTION_PROFILE_ROUTED")["payload"]
    assert routed["tier"] == "MINIMAL" and routed["distribution"]["WITHIN_100K_STEPS"] == 0.95
    assert "at most 100,000 steps" in executes[0].prompt
    assert next(e for e in events if e["kind"] == "SANDBOX_RUN")["payload"]["step_budget_exceeded"]


def test_imports_do_not_consume_the_step_budget():
    """Importing the standard library is not the task's complexity (json alone was ~94k steps)."""
    code = "import json, dataclasses, typing, re, fractions\nprint('WITNESS: ' + json.dumps({'a': 1}))"
    run = ExecutionSandbox().run_code(code, step_limit=1_000)
    assert run.success and run.stdout.strip() == 'WITNESS: {"a": 1}'


def test_program_code_run_through_library_calls_is_counted():
    sandbox = ExecutionSandbox()
    assert sandbox.run_code("sorted(range(5000), key=lambda x: -x)", step_limit=5_000).step_budget_exceeded
    assert sandbox.run_code("exec('for i in range(5000): pass')", step_limit=5_000).step_budget_exceeded


def test_system1_sees_the_task_and_the_sandbox(tmp_path):
    class Recording(PredictingSys1):
        def call(self, request):
            if "execution_profile" in request.questions:
                self.state = request.state
            return super().call(request)

    sys1 = Recording("WITHIN_10M_STEPS")
    _session(tmp_path, sys1)
    state = sys1.state
    assert state["request"] == "compute it"
    assert "standard library only" in state["execution_environment"]
    assert "network access is disabled" in state["execution_environment"]
    assert "program's own code" in state["step_definition"]
    assert "WITHIN_100K_STEPS grants 100,000 steps" in state["step_budgets"]

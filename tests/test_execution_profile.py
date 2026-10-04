"""System 1 predicts step complexity; the prediction selects a step budget that the
sandbox enforces deterministically and that the solver is told."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.providers.sys1.recipes.execution_profile import ExecutionProfileRecipe
from pdl_taskmaster.runtime.result_ir import render_instructions
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
    return engine, executes, list(engine.workspace.read_events())


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
        (_dist(k100=0.6, m10=0.2, m100=0.2), "WITHIN_10M_STEPS", "STANDARD"),  # 85% needs 3 magnitudes: diffuse
        (_dist(m100=0.9, beyond=0.1), "WITHIN_100M_STEPS", "HEAVY_COMPUTE"),
        (_dist(k100=0.25, m10=0.25, m100=0.25, beyond=0.25), "WITHIN_10M_STEPS", "STANDARD"),
        (_dist(k100=0.26, m10=0.39, m100=0.17, beyond=0.18), "WITHIN_10M_STEPS", "STANDARD"),  # run 1522 01-01
        (_dist(k100=0.1, m100=0.2, beyond=0.7), "BEYOND_100M_STEPS", "HEAVY_COMPUTE"),
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
                self.states = getattr(self, "states", []) + [request.state]
            return super().call(request)

    sys1 = Recording("WITHIN_10M_STEPS")
    _session(tmp_path, sys1)
    state = sys1.states[0]
    assert "procedure" not in state
    assert state["request"] == "compute it"
    assert "standard library only" in state["execution_environment"]
    assert "network access is disabled" in state["execution_environment"]
    assert "program's own code" in state["step_definition"]
    assert "WITHIN_100K_STEPS grants 100,000 steps" in state["step_budgets"]


class PlanPredictingSys1(PredictingSys1):
    """Predicts one magnitude from the request and another from the confirmed plan."""

    def __init__(self, request_prediction: str, plan_prediction: str | None):
        super().__init__(request_prediction)
        self.plan_prediction, self.states = plan_prediction, []

    def call(self, request):
        if "execution_profile" in request.questions:
            self.states.append(request.state)
            if "procedure" in request.state:
                if self.plan_prediction is None:
                    raise RuntimeError("sys1 down")
                return {"answers": {"execution_profile": _answer(self.plan_prediction)}}, 1.0
        return super().call(request)


def test_plan_time_prediction_sees_the_confirmed_prompt_and_plan(tmp_path):
    sys1 = PlanPredictingSys1("WITHIN_10M_STEPS", "WITHIN_10M_STEPS")
    _session(tmp_path, sys1)
    assert len(sys1.states) == 2
    assert sys1.states[1]["request"] == "COMPUTE the result"
    assert sys1.states[1]["procedure"] == "DERIVE the result"
    assert "standard library only" in sys1.states[1]["execution_environment"]


def test_plan_time_prediction_can_raise_the_budget(tmp_path):
    engine, executes, events = _session(tmp_path, PlanPredictingSys1("WITHIN_10M_STEPS", "WITHIN_100M_STEPS"))
    routed = next(e for e in events if e["kind"] == "PLAN_PROFILE_ROUTED")["payload"]
    assert routed["request_tier"] == "STANDARD" and routed["plan_tier"] == "HEAVY_COMPUTE"
    assert routed["budget_raised"] and routed["tier"] == "HEAVY_COMPUTE"
    assert engine._execution_budget.tier == "HEAVY_COMPUTE"
    assert "at most 100,000,000 steps" in executes[0].prompt


@pytest.mark.parametrize("plan_prediction", ["WITHIN_100K_STEPS", None])
def test_plan_time_prediction_never_lowers_the_budget(tmp_path, plan_prediction):
    engine, executes, events = _session(tmp_path, PlanPredictingSys1("WITHIN_10M_STEPS", plan_prediction))
    routed = next(e for e in events if e["kind"] == "PLAN_PROFILE_ROUTED")["payload"]
    assert not routed["budget_raised"] and routed["tier"] == "STANDARD"
    assert "at most 10,000,000 steps" in executes[0].prompt


def test_plan_time_prediction_is_not_shown_to_the_solver(tmp_path):
    _, executes, _ = _session(tmp_path, PlanPredictingSys1("WITHIN_10M_STEPS", "WITHIN_100M_STEPS"))
    for token in ("WITHIN_100M_STEPS", "PLAN_PROFILE", "predicted"):
        assert token not in executes[0].prompt


def test_sandbox_reports_steps_used_without_showing_them_to_the_program():
    run = ExecutionSandbox().run_code("t = 0\nfor i in range(1000):\n    t += i\nprint(t)", step_limit=100_000)
    assert run.success and run.stdout == "499500\n" and run.stderr == ""
    assert 1000 < run.steps_used < 20_000
    over = ExecutionSandbox().run_code("while True:\n    pass", step_limit=1000)
    assert over.step_budget_exceeded and over.steps_used == 1001
    assert ExecutionSandbox().run_code("print(1)").steps_used is None


class VerifiedPredictingSys1(PredictingSys1):
    """Classifies the task as needing verified execution and returns a fixed step distribution."""

    def __init__(self, distribution: dict):
        super().__init__("WITHIN_10M_STEPS")
        self.distribution = distribution

    def call(self, request):
        name = next(iter(request.questions))
        if name == "execution_profile":
            top = max(self.distribution, key=self.distribution.get)
            return {"answers": {name: {"choice": top, "confidence": self.distribution[top],
                                       "probabilities": self.distribution}}}, 1.0
        if name == "problem_class":
            return {"answers": {name: {"choice": "VERIFIED_EXECUTION", "confidence": 0.97,
                                       "probabilities": {"VERIFIED_EXECUTION": 0.97, "STANDARD_EXECUTION": 0.03}}}}, 1.0
        return super().call(request)


def test_budget_gate_refuses_uncertifiable_beyond_budget_tasks(tmp_path):
    """More likely than not beyond the largest budget, certified result required, no verifier: refuse."""
    calls: list = []
    sys1 = VerifiedPredictingSys1({"BEYOND_100M_STEPS": 0.65, "WITHIN_10M_STEPS": 0.35})
    engine = SessionEngine(ROOT, lambda r: calls.append(r) or "", workspace_root=tmp_path, sys1_client=sys1)
    response = engine.handle_user_message("$confirm-with-pseudocode find the exact optimum")
    assert response.refused and "100,000,000" in response.text and "certif" in response.text
    assert calls == []  # System 2 never ran
    assert any(e["kind"] == "BUDGET_REFUSAL" for e in engine.workspace.read_events())


@pytest.mark.parametrize("p_beyond", [0.2, 0.5])
def test_budget_gate_needs_more_likely_than_not(tmp_path, p_beyond):
    sys1 = VerifiedPredictingSys1({"BEYOND_100M_STEPS": p_beyond, "WITHIN_10M_STEPS": 1 - p_beyond})
    engine, executes, events = _session(tmp_path, sys1)
    assert not engine.refused and executes
    assert not any(e["kind"] == "BUDGET_REFUSAL" for e in events)


def test_budget_gate_does_not_apply_to_standard_tasks(tmp_path):
    sys1 = PredictingSys1("BEYOND_100M_STEPS", 0.97)
    engine, executes, _ = _session(tmp_path, sys1)
    assert not engine.refused and executes


def test_activation_route_sees_the_execution_environment(tmp_path):
    class Recording(PredictingSys1):
        def call(self, request):
            if "route" in request.questions:
                self.state = request.state
                self.criteria = request.questions["route"].criteria
            return super().call(request)

    sys1 = Recording("WITHIN_10M_STEPS")
    _session(tmp_path, sys1)
    assert "standard library only" in sys1.state["execution_environment"]
    assert "execution_environment does not provide" in sys1.criteria["BLOCKED_BY_HIGHER_PRIORITY"]


def _scripted_model(execute_replies: list[dict], executes: list):
    """A model whose drafts are fixed and whose EXECUTE replies are scripted."""
    replies = list(execute_replies)

    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "A task.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": "COMPUTE the result", "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": "DERIVE the result"})
        executes.append(req)
        return json.dumps(replies.pop(0))

    return model_call


def _verified_session(tmp_path, prediction: str, execute_replies: list[dict]):
    """A verified-execution session whose EXECUTE replies are scripted."""
    executes: list = []
    model_call = _scripted_model(execute_replies, executes)
    dist = {prediction: 0.97, "WITHIN_10M_STEPS" if prediction != "WITHIN_10M_STEPS" else "WITHIN_100K_STEPS": 0.03}
    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=VerifiedPredictingSys1(dist))
    for message in ("$confirm-with-pseudocode compute it", "/confirm", "/confirm"):
        engine.handle_user_message(message)
    return engine, executes, list(engine.workspace.read_events())


_IR = {"files": [], "reconciliation": [{"requirement": "R1", "status": "satisfied", "evidence": {"path": "execution://body"}}],
       "open_defects": []}
_NO_WITNESS = {"kind": "RESULT", "body": "The answer is 9.", "result_ir": _IR}
_STOPPED = {"kind": "RESULT", "body": "while True:\n    pass", "result_ir": _IR}
_GOOD = {"kind": "RESULT", "body": "print('WITNESS: {\"answer\": 9}')", "result_ir": _IR}


def test_heavy_tier_allows_two_repairs_each_with_the_latest_findings(tmp_path, monkeypatch):
    monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, "HEAVY_COMPUTE",
                        ExecutionBudget("HEAVY_COMPUTE", 50_000, 30, 256 << 20, repairs=2))
    engine, executes, events = _verified_session(tmp_path, "WITHIN_100M_STEPS", [_NO_WITNESS, _STOPPED, _GOOD])
    assert len(executes) == 3 and engine.controller.state.stage.value == "CLOSED_SUCCESS"
    assert "no program that ran successfully" in executes[1].prompt
    assert "[STEP_BUDGET_EXCEEDED] Python block 1 was stopped after 50,000 steps" in executes[2].prompt
    assert "The next attempt has the same budget of 50,000 steps" in executes[2].prompt
    assert "STEP_BUDGET_EXCEEDED" not in executes[1].prompt  # each repair: the latest findings
    attempts = next(e for e in events if e["kind"] == "EXECUTION_ATTEMPTS")["payload"]
    # attempt 1 ran no program: its repair is uncounted; attempt 2 ran: counted
    assert attempts == {"attempts": 3, "repairs_used": 1, "unmeasured_repairs": 1, "repairs_allowed": 2,
                        "tier": "HEAVY_COMPUTE"}


def test_standard_and_minimal_tiers_allow_one_repair(tmp_path):
    for prediction in ("WITHIN_100K_STEPS", "WITHIN_10M_STEPS"):
        engine, executes, events = _verified_session(tmp_path / prediction, prediction,
                                                     [_STOPPED, _STOPPED, _GOOD])
        assert len(executes) == 2 and engine.controller.state.stage.value == "CLOSED_CANCELLED"
        attempts = next(e for e in events if e["kind"] == "EXECUTION_ATTEMPTS")["payload"]
        assert attempts["repairs_used"] == attempts["repairs_allowed"] == 1
        assert attempts["unmeasured_repairs"] == 0


def test_attempt_without_a_program_does_not_use_up_the_tier_repair(tmp_path):
    """Runs 2026-09-30 01-01: 4 of 9 runs spent their only repair on an attempt with
    no runnable program, then the measured attempt had no repair left."""
    engine, executes, events = _verified_session(tmp_path, "WITHIN_10M_STEPS", [_NO_WITNESS, _STOPPED, _GOOD])
    assert len(executes) == 3 and engine.controller.state.stage.value == "CLOSED_SUCCESS"
    repairs = [e["payload"] for e in events if e["kind"] == "VERIFICATION_REPAIR"]
    assert [r["counted"] for r in repairs] == [False, True]
    attempts = next(e for e in events if e["kind"] == "EXECUTION_ATTEMPTS")["payload"]
    assert attempts["repairs_used"] == 1 and attempts["unmeasured_repairs"] == 1


def test_uncounted_repairs_are_capped_at_one(tmp_path):
    engine, executes, events = _verified_session(tmp_path, "WITHIN_10M_STEPS", [_NO_WITNESS] * 4)
    assert len(executes) == 3 and engine.controller.state.stage.value == "CLOSED_CANCELLED"
    attempts = next(e for e in events if e["kind"] == "EXECUTION_ATTEMPTS")["payload"]
    assert attempts["repairs_used"] == 1 and attempts["unmeasured_repairs"] == 1


def test_repair_budgets_are_per_tier_and_fixed():
    assert {t: b.repairs for t, b in sandbox_module.EXECUTION_BUDGETS.items()} == {
        "MINIMAL": 1, "STANDARD": 1, "HEAVY_COMPUTE": 2,
    }


def _routed_to_plan_review(tmp_path, executes: list):
    """A verified-execution task routed to the MINIMAL tier, stopped at the plan review."""
    sys1 = VerifiedPredictingSys1({"WITHIN_100K_STEPS": 0.97, "WITHIN_10M_STEPS": 0.03})
    model_call = _scripted_model([_GOOD], executes)
    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1)
    for message in ("$confirm-with-pseudocode compute it", "/confirm"):
        engine.handle_user_message(message)
    assert engine.controller.state.stage == Stage.PLAN_REVIEW and not executes
    return engine.workspace.path, model_call, sys1


def test_restored_session_executes_as_system1_routed_it(tmp_path):
    """/confirm at the plan review in a later process: the restored engine executed in
    standard mode under the STANDARD budget, skipping the Result IR contract, witness
    verification and the repair loop System 1 had routed the task to."""
    executes: list = []
    workspace_path, model_call, sys1 = _routed_to_plan_review(tmp_path, executes)

    resumed = SessionEngine.restore(ROOT, model_call, workspace_path, sys1_client=sys1)
    resumed.handle_user_message("/confirm")
    (execute,) = executes
    inputs = execute.projection.document["operation_inputs"]
    assert [r for r in execute.manifest["requirement_ids"] if r.startswith("RS-")]  # Result IR mode
    verified_channel = render_instructions(repo_root=ROOT, requires_verified_execution=True)
    assert verified_channel in inputs["REQUIRED_TASK_INPUTS"]  # with the witness instructions
    minimal = sandbox_module.EXECUTION_BUDGETS["MINIMAL"]
    assert inputs["AVAILABLE_EXECUTION_TOOLS"] == resumed.sandbox.describe(minimal)
    assert "at most 100,000 steps" in inputs["AVAILABLE_EXECUTION_TOOLS"][0]["description"]


def test_restored_session_keeps_host_declared_tools(tmp_path):
    executes: list = []
    workspace_path, model_call, sys1 = _routed_to_plan_review(tmp_path, executes)
    declared = [{"name": "custom", "description": "host-provided"}]
    resumed = SessionEngine.restore(ROOT, model_call, workspace_path, sys1_client=sys1,
                                    available_execution_tools=declared)
    assert resumed._execution_budget.tier == "MINIMAL"
    assert resumed.available_execution_tools == declared

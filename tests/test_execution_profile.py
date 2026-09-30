"""System 1 routes a resource tier; the sandbox enforces it and the solver is told it."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.providers.sys1.recipes.execution_profile import ExecutionProfileRecipe
from pdl_taskmaster.runtime.session_engine import SessionEngine
from pdl_taskmaster.verification import sandbox as sandbox_module
from pdl_taskmaster.verification.sandbox import ExecutionBudget

ROOT = Path(__file__).resolve().parents[1]


def _answer(choice: str, confidence: float = 0.97) -> dict:
    other = "STANDARD" if choice != "STANDARD" else "HEAVY_COMPUTE"
    return {"choice": choice, "confidence": confidence,
            "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}


class TieredSys1:
    is_configured = True
    model = "fake-sys1"

    def __init__(self, tier: str | None, confidence: float = 0.97):
        self.tier, self.confidence = tier, confidence

    def call(self, request):
        name = next(iter(request.questions))
        if name == "route":
            return {"answers": {name: _answer("APPLY_PROTOCOL")}}, 1.0
        if name == "execution_profile":
            if self.tier is None:
                raise RuntimeError("sys1 down")
            return {"answers": {name: _answer(self.tier, self.confidence)}}, 1.0
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


@pytest.mark.parametrize(
    "answer, tier",
    [(_answer("HEAVY_COMPUTE"), "HEAVY_COMPUTE"), (_answer("LARGE_MEMORY"), "LARGE_MEMORY"),
     (_answer("HEAVY_COMPUTE", 0.6), "STANDARD"), (_answer("SYMBOLIC_ONLY"), "STANDARD"), ({}, "STANDARD")],
)
def test_recipe_routes_only_known_gated_tiers(answer, tier):
    recipe = ExecutionProfileRecipe()
    result = recipe.parse_response({"answers": {"execution_profile": answer}})
    assert recipe.map_to_wire(result)["tier"] == tier


def test_solver_is_told_the_routed_budget(tmp_path):
    engine, executes, events = _session(tmp_path, TieredSys1("HEAVY_COMPUTE"))
    routed = next(e for e in events if e["kind"] == "EXECUTION_PROFILE_ROUTED")["payload"]
    assert routed == {"tier": "HEAVY_COMPUTE", "passed_gating": True, "timeout_seconds": 90.0, "memory_mb": 512}
    assert "90-second time limit and a 512 MB memory limit" in executes[0].prompt


@pytest.mark.parametrize("sys1", [None, TieredSys1(None), TieredSys1("HEAVY_COMPUTE", 0.5)])
def test_absent_or_uncertain_system1_means_standard(tmp_path, sys1):
    engine, executes, events = _session(tmp_path, sys1)
    assert engine._execution_budget.tier == "STANDARD"
    assert "15-second time limit and a 256 MB memory limit" in executes[0].prompt


def test_sandbox_enforces_the_routed_budget(tmp_path, monkeypatch):
    monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, "STANDARD", ExecutionBudget("STANDARD", 1.0, 256 << 20))
    monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, "HEAVY_COMPUTE", ExecutionBudget("HEAVY_COMPUTE", 4.0, 256 << 20))
    body = "import time\ntime.sleep(2)\nprint('finished')"
    runs = {}
    for tier in ("STANDARD", "HEAVY_COMPUTE"):
        _, _, events = _session(tmp_path / tier, TieredSys1(tier), execute_body=body)
        runs[tier] = next(e for e in events if e["kind"] == "SANDBOX_RUN")["payload"]
    assert runs["STANDARD"]["timed_out"] and runs["STANDARD"]["tier"] == "STANDARD"
    assert not runs["HEAVY_COMPUTE"]["timed_out"] and runs["HEAVY_COMPUTE"]["exit_code"] == 0


def test_host_declared_tools_are_not_overridden(tmp_path):
    declared = [{"name": "custom", "description": "host-provided"}]
    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None,
                           available_execution_tools=declared)
    engine.workspace = engine._new_workspace()
    engine._route_execution_profile("anything")
    assert engine.available_execution_tools == declared

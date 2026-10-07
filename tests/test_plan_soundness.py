from __future__ import annotations

from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe
from pdl_taskmaster.verification.plan_soundness import (
    PlanSoundnessResult,
    validate_plan_soundness,
)


def test_problem_class_recipe_is_system1_only():
    recipe = ProblemClassRecipe()
    assert recipe.name == "problem-class"
    # No deterministic keyword fast path exists at all (GUARD-02)
    assert not hasattr(recipe, "classify_text_deterministic")

    req = recipe.build_request({"request": "Find whether an assignment exists"})
    assert "problem_class" in req.questions
    assert "VERIFIED_EXECUTION" in req.questions["problem_class"].choices


def test_lint_rejects_deferral_markers():
    for plan in (
        "SOLVE the task\nThe method is deferred to execution",
        "COMPUTE the answer\nDetails TBD",
    ):
        result = validate_plan_soundness(plan)
        assert not result.valid
        assert any("PDL-08" in v for v in result.violations)


def test_lint_rejects_fielded_prefixes_and_code_fences():
    fielded = validate_plan_soundness("TASK: reverse a string\nOUTPUT: the reversed string")
    assert not fielded.valid
    assert any("PDL-05" in v for v in fielded.violations)

    fenced = validate_plan_soundness("WRITE the function\n```python\ndef f(): ...\n```")
    assert not fenced.valid
    assert any("PDL-06" in v for v in fenced.violations)

    empty = validate_plan_soundness("   ")
    assert not empty.valid


def test_lint_allows_control_keywords_with_colons():
    plan = "FOR each record:\n  ADD the amount to the total\nENDFOR"
    assert validate_plan_soundness(plan).valid


def test_lint_is_method_neutral_for_every_task_class():
    analytical = "DEDUCE the relationship between the quantities\nEMIT the resulting expression"
    procedural = "IMPLEMENT the function\nRETURN the result"
    vague = "Ponder the properties\nConclude"
    for plan in (analytical, procedural, vague):
        for flag in (True, False):
            result = validate_plan_soundness(plan, requires_verified_execution=flag)
            assert isinstance(result, PlanSoundnessResult)
            assert result.valid, (plan, flag, result.violations)


def test_notation_violation_gets_one_redraft_with_the_finding(tmp_path):
    """A plan carrying a drafting meta-rule is redrafted once with the lint finding;
    the host never edits the body itself."""
    import json
    from pathlib import Path

    from pdl_taskmaster.runtime.session_engine import SessionEngine

    plans = ["SPLIT the string\nDo not perform any computation; only describe the required result.",
             "SPLIT the string into palindromes\nRETURN the minimum number of cuts"]
    calls = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "A task.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": "PARTITION the string", "approach_handoff": "NONE"})
        return json.dumps({"neutral_plan_body": plans.pop(0)})

    engine = SessionEngine(Path(__file__).resolve().parents[1], model_call, workspace_root=tmp_path, sys1_client=None)
    engine.handle_user_message("$confirm-with-pseudocode partition it")
    response = engine.handle_user_message("/confirm")
    drafts = [c for c in calls if c.operation == "DRAFT_PLAN"]
    assert len(drafts) == 2 and "PDL-08" in drafts[1].prompt
    assert engine.controller.state.current_plan.body == "SPLIT the string into palindromes\nRETURN the minimum number of cuts"
    retry = next(e for e in engine.workspace.read_events() if e["kind"] == "PLAN_LINT_RETRY")["payload"]
    assert retry["operation"] == "DRAFT_PLAN"
    assert "Do not perform" not in response.text


def test_plan_prompt_echo_is_recorded_as_telemetry(tmp_path):
    import json
    from pathlib import Path

    from pdl_taskmaster.runtime.session_engine import SessionEngine

    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "A task.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": "SORT the list.\nRETURN the median",
                               "approach_handoff": "NONE"})
        return json.dumps({"neutral_plan_body": "sort the list\nRETURN the median."})

    engine = SessionEngine(Path(__file__).resolve().parents[1], model_call, workspace_root=tmp_path, sys1_client=None)
    engine.handle_user_message("$confirm-with-pseudocode median")
    engine.handle_user_message("/confirm")
    echo = next(e for e in engine.workspace.read_events() if e["kind"] == "PLAN_PROMPT_ECHO")["payload"]
    assert echo["identical"] is True and echo["copied_line_ratio"] == 1.0


def test_lint_rejects_implementation_prohibitions_and_metatask_reading():
    """PDL-08 & PDL-09: reject negative execution prohibitions and metatask ingestion."""
    bad_snippets = [
        "PROVIDE only the specification; do not implement the data structure or the tests.",
        "ENSURE the specification contains no executable code, only method contracts",
        "DO NOT implement the algorithm; only describe the steps",
        "NEVER implement the requested class",
        "READ the task specification for a recursive-descent calculator",
        "READ the request to implement a write-ahead log in Python",
    ]
    for text in bad_snippets:
        result = validate_plan_soundness(text)
        assert not result.valid, f"Expected violation for: {text}"
        assert any("PDL-08" in v for v in result.violations), f"Expected PDL-08 violation for: {text}"

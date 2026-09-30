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

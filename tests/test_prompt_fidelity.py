"""Unit tests for PromptFidelityRecipe and prompt fidelity semantic gating."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.providers.sys1.recipes.prompt_fidelity import CHECKS, PromptFidelityRecipe
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]


def test_prompt_fidelity_recipe_structure():
    recipe = PromptFidelityRecipe()
    assert recipe.name == "prompt-fidelity"
    assert recipe.min_confidence == 0.80

    req = recipe.build_request(
        {
            "source_request": "Solve the 4-coloring problem for wheel graph W_11.",
            "drafted_prompt": "IMPLEMENT 4-coloring without computing a specific coloring solution.",
        }
    )
    assert req.state["source_request"] == "Solve the 4-coloring problem for wheel graph W_11."
    assert list(req.questions) == list(CHECKS)
    for q in CHECKS:
        assert req.questions[q].choices == ["true", "false"]


def test_prompt_fidelity_recipe_verdicts():
    recipe = PromptFidelityRecipe()

    # Confident true across all checks -> FAITHFUL
    resp_faithful = {
        "answers": {
            k: {
                "choice": "true",
                "confidence": 0.95,
                "probabilities": {"true": 0.95, "false": 0.05},
            }
            for k in CHECKS
        }
    }
    res = recipe.parse_response(resp_faithful)
    assert res.verdict == "FAITHFUL"
    assert res.passed_gating is True

    # Confident false on no_evasion -> UNPROMPTED_EVASION
    resp_evasive = {
        "answers": {
            "no_evasion": {
                "choice": "false",
                "confidence": 0.92,
                "probabilities": {"true": 0.08, "false": 0.92},
            },
            "complete_coverage": {
                "choice": "true",
                "confidence": 0.90,
                "probabilities": {"true": 0.90, "false": 0.10},
            },
        }
    }
    res_evasive = recipe.parse_response(resp_evasive)
    assert res_evasive.verdict == "UNPROMPTED_EVASION"
    assert res_evasive.passed_gating is True

    # Confident false on complete_coverage -> INCOMPLETE_COVERAGE
    resp_incomplete = {
        "answers": {
            "no_evasion": {
                "choice": "true",
                "confidence": 0.92,
                "probabilities": {"true": 0.92, "false": 0.08},
            },
            "complete_coverage": {
                "choice": "false",
                "confidence": 0.91,
                "probabilities": {"true": 0.09, "false": 0.91},
            },
        }
    }
    res_incomplete = recipe.parse_response(resp_incomplete)
    assert res_incomplete.verdict == "INCOMPLETE_COVERAGE"
    assert res_incomplete.passed_gating is True

    # Confident false on no_answer_leakage -> ANSWER_LEAKAGE
    resp_leakage = {
        "answers": {
            "no_evasion": {
                "choice": "true",
                "confidence": 0.92,
                "probabilities": {"true": 0.92, "false": 0.08},
            },
            "complete_coverage": {
                "choice": "true",
                "confidence": 0.91,
                "probabilities": {"true": 0.91, "false": 0.09},
            },
            "no_answer_leakage": {
                "choice": "false",
                "confidence": 0.93,
                "probabilities": {"true": 0.07, "false": 0.93},
            },
        }
    }
    res_leakage = recipe.parse_response(resp_leakage)
    assert res_leakage.verdict == "ANSWER_LEAKAGE"
    assert res_leakage.passed_gating is True

    # Low confidence -> UNCERTAIN
    resp_uncertain = {
        "answers": {
            "no_evasion": {
                "choice": "true",
                "confidence": 0.55,
                "probabilities": {"true": 0.55, "false": 0.45},
            },
            "complete_coverage": {
                "choice": "true",
                "confidence": 0.90,
                "probabilities": {"true": 0.90, "false": 0.10},
            },
            "no_answer_leakage": {
                "choice": "true",
                "confidence": 0.90,
                "probabilities": {"true": 0.90, "false": 0.10},
            },
        }
    }
    res_uncertain = recipe.parse_response(resp_uncertain)
    assert res_uncertain.verdict == "UNCERTAIN"
    assert res_uncertain.passed_gating is False


class MockFidelityJudge:
    is_configured = True
    model = "mock-jev"

    def __init__(self, choices: dict[str, str] | None = None, confidence: float = 0.95):
        self.choices = choices or {k: "true" for k in CHECKS}
        self.confidence = confidence
        self.calls = []

    def call(self, request):
        self.calls.append(request)
        names = list(request.questions)
        if names[0] == "route":
            return {"answers": {"route": {"choice": "APPLY_PROTOCOL", "confidence": 0.97, "probabilities": {"APPLY_PROTOCOL": 0.97}}}}, 1.0
        if names[0] == "problem_class":
            return {"answers": {"problem_class": {"choice": "STANDARD_EXECUTION", "confidence": 0.97, "probabilities": {"STANDARD_EXECUTION": 0.97}}}}, 1.0
        answers = {}
        for q in request.questions:
            c = self.choices.get(q, "true")
            answers[q] = {
                "choice": c,
                "confidence": self.confidence,
                "probabilities": {c: self.confidence, "false" if c == "true" else "true": 1 - self.confidence},
            }
        return {"answers": answers}, 1.0


def test_prompt_fidelity_gate_triggers_redraft_on_evasion(tmp_path):
    judge = MockFidelityJudge(choices={"no_evasion": "false", "complete_coverage": "true"})
    calls = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({
                "kind": "ANALYSIS",
                "task_summary": "Coloring task",
                "approach_notes": "",
                "risk_notes": "",
                "task_entities": [],
            })
        if req.operation == "DRAFT_PROMPT":
            if len([c for c in calls if c.operation == "DRAFT_PROMPT"]) == 1:
                return json.dumps({
                    "kind": "PROMPT",
                    "prompt_body": "FIND 4-coloring without computing a specific solution",
                    "approach_handoff": "NONE",
                })
            # Second attempt
            judge.choices = {"no_evasion": "true", "complete_coverage": "true"}
            return json.dumps({
                "kind": "PROMPT",
                "prompt_body": "COMPUTE a valid 4-coloring for wheel graph W_11",
                "approach_handoff": "NONE",
            })
        return json.dumps({"neutral_plan_body": "DETERMINE coloring"})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=judge)
    response = engine.handle_user_message("$confirm-with-pseudocode solve W_11 coloring")

    draft_calls = [c for c in calls if c.operation == "DRAFT_PROMPT"]
    assert len(draft_calls) == 2
    assert "OPERATOR CORRECTION" in draft_calls[1].prompt
    assert "PROMPT-01" in draft_calls[1].prompt
    assert engine.controller.state.current_prompt.body == "COMPUTE a valid 4-coloring for wheel graph W_11"


def test_prompt_fidelity_gate_triggers_redraft_on_incomplete_coverage(tmp_path):
    judge = MockFidelityJudge(choices={"no_evasion": "true", "complete_coverage": "false"})
    calls = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({
                "kind": "ANALYSIS",
                "task_summary": "Topological sort with cycle",
                "approach_notes": "",
                "risk_notes": "",
                "task_entities": [],
            })
        if req.operation == "DRAFT_PROMPT":
            if len([c for c in calls if c.operation == "DRAFT_PROMPT"]) == 1:
                return json.dumps({
                    "kind": "PROMPT",
                    "prompt_body": "IMPLEMENT topological sort",
                    "approach_handoff": "NONE",
                })
            # Second attempt includes full coverage
            judge.choices = {"no_evasion": "true", "complete_coverage": "true"}
            return json.dumps({
                "kind": "PROMPT",
                "prompt_body": "IMPLEMENT topological sort and report exact cycle nodes when detected",
                "approach_handoff": "NONE",
            })
        return json.dumps({"neutral_plan_body": "SORT DAG"})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=judge)
    response = engine.handle_user_message("$confirm-with-pseudocode topological sort with cycle")

    draft_calls = [c for c in calls if c.operation == "DRAFT_PROMPT"]
    assert len(draft_calls) == 2
    assert "OPERATOR CORRECTION" in draft_calls[1].prompt
    assert "silently drops or omits" in draft_calls[1].prompt
    assert engine.controller.state.current_prompt.body == "IMPLEMENT topological sort and report exact cycle nodes when detected"


def test_prompt_fidelity_gate_triggers_redraft_on_answer_leakage(tmp_path):
    judge = MockFidelityJudge(choices={"no_evasion": "true", "complete_coverage": "true", "no_answer_leakage": "false"})
    calls = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({
                "kind": "ANALYSIS",
                "task_summary": "Sibling count riddle",
                "approach_notes": "",
                "risk_notes": "",
                "task_entities": [],
            })
        if req.operation == "DRAFT_PROMPT":
            if len([c for c in calls if c.operation == "DRAFT_PROMPT"]) == 1:
                return json.dumps({
                    "kind": "PROMPT",
                    "prompt_body": "DEFINE result as 5\nOUTPUT result",
                    "approach_handoff": "NONE",
                })
            # Second attempt stays neutral
            judge.choices = {"no_evasion": "true", "complete_coverage": "true", "no_answer_leakage": "true"}
            return json.dumps({
                "kind": "PROMPT",
                "prompt_body": "CALCULATE the sibling count based on relationship constraints\nOUTPUT the result",
                "approach_handoff": "NONE",
            })
        return json.dumps({"neutral_plan_body": "COMPUTE sibling count"})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=judge)
    response = engine.handle_user_message("$confirm-with-pseudocode sibling riddle")

    draft_calls = [c for c in calls if c.operation == "DRAFT_PROMPT"]
    assert len(draft_calls) == 2
    assert "OPERATOR CORRECTION" in draft_calls[1].prompt
    assert "preselects or leaks substantive answers" in draft_calls[1].prompt
    assert "PROMPT-02" in draft_calls[1].prompt
    assert engine.controller.state.current_prompt.body == "CALCULATE the sibling count based on relationship constraints\nOUTPUT the result"

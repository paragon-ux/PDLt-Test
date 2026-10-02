"""ProblemClass Sys1 Decision Recipe (P0).

Classifies whether an incoming request requires verified execution (a specific,
checkable result for fully specified, concrete inputs) or standard execution.
Verified execution asks for a witness; it never requires code (GUARD-03): a
non-code deliverable's model witness is accepted and marked provisional.
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

class ProblemClassRecipe(Sys1Recipe):
    """Evaluates whether an incoming request requires verified execution."""

    @property
    def name(self) -> str:
        return "problem-class"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        task_text = state.get("request", "") or state.get("task_summary", "")
        instruction = as_decision_instruction(
            "Classify whether this task requires verified execution: does it ask for a specific, checkable "
            "result for fully specified, concrete inputs, or is it standard execution?"
        )
        criteria = {
            "VERIFIED_EXECUTION": (
                "The task asks for a specific, checkable result for fully specified, concrete inputs: whether a "
                "structure satisfying stated constraints exists, an optimal or constrained structure, or a single "
                "exact value such as a count, a probability, an expected value or another number."
            ),
            "STANDARD_EXECUTION": (
                "The task is programming, drafting, text manipulation, explanation, a proof, or open-ended "
                "analysis, or its answer is a formula in symbolic parameters rather than a value for concrete "
                "inputs."
            ),
        }
        question = Sys1Question(
            instructions=instruction,
            criteria=criteria,
            choices=["VERIFIED_EXECUTION", "STANDARD_EXECUTION"],
        )
        return Sys1Request(
            state={"request": task_text},
            questions={"problem_class": question},
        )

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        answers = response_body.get("answers", {})
        ans = answers.get("problem_class", {})
        gating = evaluate_confidence_gate(ans, confidence_floor=self.min_confidence)
        choice = gating.choice or "STANDARD_EXECUTION"
        status = "ready" if gating.passed else "review"
        return RecipeResult(
            status=status,
            verdict=choice,
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=gating.passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {
            "requires_verified_execution": result.verdict == "VERIFIED_EXECUTION",
            "confidence": result.confidence,
        }

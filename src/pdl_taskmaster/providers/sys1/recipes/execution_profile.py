"""ExecutionProfile Sys1 Decision Recipe (TARGET_ARCHITECTURE §5).

System 1 predicts the step complexity of a request: the order of magnitude of
Python bytecode steps that carrying it out exactly would take. The prediction
selects a fixed step budget (verification/sandbox.py EXECUTION_BUDGETS) that the
sandbox enforces deterministically and that AVAILABLE_EXECUTION_TOOLS declares to
System 2. System 1 decides resources only: never the answer, the method, or
whether code is written.
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

# Predicted step magnitude -> budget tier. A prediction beyond the largest budget
# is granted the largest budget and recorded; the step counter decides the outcome.
PREDICTION_TIERS = {
    "WITHIN_10M_STEPS": "STANDARD",
    "WITHIN_100M_STEPS": "HEAVY_COMPUTE",
    "BEYOND_100M_STEPS": "HEAVY_COMPUTE",
}


class ExecutionProfileRecipe(Sys1Recipe):
    """Predicts step complexity; absent or uncertain evidence means the standard budget."""

    @property
    def name(self) -> str:
        return "execution-profile"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        question = Sys1Question(
            instructions=as_decision_instruction(
                "Predict how many elementary computation steps (Python bytecode instructions) carrying out this "
                "request exactly would take, for the most direct correct computation."
            ),
            criteria={
                "WITHIN_10M_STEPS": (
                    "At most about ten million steps, including requests that need no computation beyond "
                    "writing, explaining, or reasoning."
                ),
                "WITHIN_100M_STEPS": "More than ten million and at most about one hundred million steps.",
                "BEYOND_100M_STEPS": "More than about one hundred million steps.",
            },
            choices=list(PREDICTION_TIERS),
        )
        return Sys1Request(state={"request": state.get("request", "")}, questions={"execution_profile": question})

    def parse_response(self, response_body: dict[str, Any], *, duration_ms: float = 0.0) -> RecipeResult:
        answer = response_body.get("answers", {}).get("execution_profile", {})
        gating = evaluate_confidence_gate(answer, confidence_floor=self.min_confidence)
        known = gating.choice in PREDICTION_TIERS
        passed = gating.passed and known
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=gating.choice if known else "WITHIN_10M_STEPS",
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        prediction = result.verdict if result.passed_gating else "WITHIN_10M_STEPS"
        return {"prediction": prediction, "tier": PREDICTION_TIERS[prediction]}

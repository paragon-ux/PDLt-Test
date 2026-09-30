"""ExecutionProfile Sys1 Decision Recipe (TARGET_ARCHITECTURE §5).

System 1 predicts the step complexity of a request: the order of magnitude of
Python bytecode steps that carrying it out exactly would take. The prediction
selects a fixed step budget (verification/sandbox.py EXECUTION_BUDGETS) that the
sandbox enforces deterministically and that AVAILABLE_EXECUTION_TOOLS declares to
System 2. System 1 decides resources only: never the answer, the method, or
whether code is written.

The labels are ordered magnitudes, so the decision is weighted, not argmax: the
granted budget is the smallest one System 1 believes suffices with cumulative
probability of at least BUDGET_QUANTILE. Probability split between neighbouring
magnitudes resolves to the upper one instead of failing a confidence gate. An
oversized budget is avoided on purpose: it would let work pass that the task's
complexity does not justify.
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

# Ordered predicted magnitudes -> budget tier. A prediction beyond the largest
# budget is granted the largest budget and recorded; the step counter decides.
PREDICTION_TIERS = {
    "WITHIN_100K_STEPS": "MINIMAL",
    "WITHIN_10M_STEPS": "STANDARD",
    "WITHIN_100M_STEPS": "HEAVY_COMPUTE",
    "BEYOND_100M_STEPS": "HEAVY_COMPUTE",
}
BUDGET_QUANTILE = 0.85
FALLBACK_PREDICTION = "WITHIN_10M_STEPS"  # no usable evidence: the standard budget


def budget_prediction(probabilities: dict[str, float]) -> str | None:
    """Smallest magnitude whose cumulative probability reaches BUDGET_QUANTILE, or
    None when the distribution carries no usable evidence."""
    known = {label: max(0.0, float(probabilities.get(label, 0.0))) for label in PREDICTION_TIERS}
    total = sum(known.values())
    if total <= 0.0:
        return None
    cumulative = 0.0
    for label in PREDICTION_TIERS:
        cumulative += known[label] / total
        if cumulative >= BUDGET_QUANTILE - 1e-9:
            return label
    return list(PREDICTION_TIERS)[-1]


class ExecutionProfileRecipe(Sys1Recipe):
    """Predicts step complexity; absent evidence means the standard budget."""

    @property
    def name(self) -> str:
        return "execution-profile"

    @property
    def min_confidence(self) -> float:
        return BUDGET_QUANTILE

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        question = Sys1Question(
            instructions=as_decision_instruction(
                "Given the execution environment and step definition in the state, predict how many steps a "
                "program carrying out this request exactly would take, for the most direct correct computation."
            ),
            criteria={
                "WITHIN_100K_STEPS": (
                    "At most about one hundred thousand steps, including requests that need no computation "
                    "beyond writing, explaining, or reasoning."
                ),
                "WITHIN_10M_STEPS": "More than one hundred thousand and at most about ten million steps.",
                "WITHIN_100M_STEPS": "More than ten million and at most about one hundred million steps.",
                "BEYOND_100M_STEPS": "More than about one hundred million steps.",
            },
            choices=list(PREDICTION_TIERS),
        )
        # Recipe state: the task and the sandbox it would run in (Axiom 1: System 1
        # routes the sandbox conditions, so it must see them).
        from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

        budgets = "; ".join(
            f"{label} grants {EXECUTION_BUDGETS[tier].step_limit:,} steps" for label, tier in PREDICTION_TIERS.items()
        )
        return Sys1Request(
            state={"request": state.get("request", ""), **(state.get("environment") or {}), "step_budgets": budgets},
            questions={"execution_profile": question},
        )

    def parse_response(self, response_body: dict[str, Any], *, duration_ms: float = 0.0) -> RecipeResult:
        answer = response_body.get("answers", {}).get("execution_profile", {})
        gating = evaluate_confidence_gate(answer, confidence_floor=self.min_confidence)  # telemetry only
        probabilities = dict(gating.probabilities)
        if not probabilities and gating.choice in PREDICTION_TIERS:
            probabilities = {gating.choice: gating.confidence}
            if gating.confidence < BUDGET_QUANTILE:
                probabilities = {}
        prediction = budget_prediction(probabilities)
        passed = prediction is not None
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=prediction or FALLBACK_PREDICTION,
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=passed,
            probabilities=probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        prediction = result.verdict if result.passed_gating else FALLBACK_PREDICTION
        return {"prediction": prediction, "tier": PREDICTION_TIERS[prediction]}

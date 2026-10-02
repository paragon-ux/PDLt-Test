"""FollowUp Sys1 Decision Recipe.

Decides whether a message that arrives after a closed turn continues or refers to
the previous request (a follow-up, worked from both) or is a new, independent
request (worked from the message alone).
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

CHOICES = ("FOLLOW_UP", "NEW_REQUEST")


class FollowUpRecipe(Sys1Recipe):
    """Evaluates whether a message continues the previous request or starts a new one."""

    @property
    def name(self) -> str:
        return "follow-up"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        instruction = as_decision_instruction(
            "Does this message continue, correct or refer to the previous request, "
            "or is it a new, independent request?"
        )
        criteria = {
            "FOLLOW_UP": (
                "The message continues, corrects, narrows, retries or refers to the previous request or its "
                "result: it asks to try again, says the result was wrong, asks for the result in another form, "
                "or cannot be understood without the previous request."
            ),
            "NEW_REQUEST": (
                "The message is a complete request that can be understood and carried out without the previous "
                "request: it concerns a different subject, file or task, even when it is phrased as a question."
            ),
        }
        question = Sys1Question(instructions=instruction, criteria=criteria, choices=list(CHOICES))
        return Sys1Request(
            state={"previous_request": state.get("previous_request", ""), "message": state.get("message", "")},
            questions={"follow_up": question},
        )

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        answers = response_body.get("answers", {})
        ans = answers.get("follow_up", {})
        gating = evaluate_confidence_gate(ans, confidence_floor=self.min_confidence)
        # An answer outside the two choices passes no gate.
        passed = gating.passed and gating.choice in CHOICES
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=gating.choice or "FOLLOW_UP",
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {
            "follow_up": not (result.passed_gating and result.verdict == "NEW_REQUEST"),
            "confidence": result.confidence,
        }

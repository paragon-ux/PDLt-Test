"""ExecutionProfile Sys1 Decision Recipe (TARGET_ARCHITECTURE §5).

Routes a request to a resource tier. The tier selects a fixed sandbox budget
(verification/sandbox.py EXECUTION_BUDGETS) that the sandbox enforces and that
AVAILABLE_EXECUTION_TOOLS declares to System 2. System 1 decides resources only:
it never decides the answer, the method, or whether code should be written.
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

TIERS = ("STANDARD", "HEAVY_COMPUTE", "LARGE_MEMORY")


class ExecutionProfileRecipe(Sys1Recipe):
    """Selects the resource tier for a request; absent or uncertain evidence means STANDARD."""

    @property
    def name(self) -> str:
        return "execution-profile"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        question = Sys1Question(
            instructions=as_decision_instruction(
                "Classify the computing resources that fully carrying out this request would need."
            ),
            criteria={
                "STANDARD": (
                    "Seconds of computation and modest memory suffice, or the request needs no computation "
                    "beyond writing, explaining, or reasoning."
                ),
                "HEAVY_COMPUTE": (
                    "Carrying out the request exactly may take minutes of CPU time, for example exploring a very "
                    "large space of candidates or running a long numerical computation."
                ),
                "LARGE_MEMORY": (
                    "Carrying out the request needs to hold large data in memory at once, on the order of "
                    "gigabytes."
                ),
            },
            choices=list(TIERS),
        )
        return Sys1Request(state={"request": state.get("request", "")}, questions={"execution_profile": question})

    def parse_response(self, response_body: dict[str, Any], *, duration_ms: float = 0.0) -> RecipeResult:
        answer = response_body.get("answers", {}).get("execution_profile", {})
        gating = evaluate_confidence_gate(answer, confidence_floor=self.min_confidence)
        choice = gating.choice if gating.choice in TIERS else "STANDARD"
        passed = gating.passed and gating.choice in TIERS
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=choice,
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {"tier": result.verdict if result.passed_gating else "STANDARD"}

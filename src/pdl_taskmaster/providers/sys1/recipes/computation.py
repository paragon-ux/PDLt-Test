"""Computation Sys1 Decision Recipe.

Decides whether producing a request's deliverable is, or needs, an algorithm or a
calculation: writing, fixing or implementing a program or an algorithm, searching or
enumerating possibilities, or working out a number, count or other value from given
quantities. It gates one thing: whether the model drafts an execution brief before it
executes (DRAFT_EXECUTE, ADR-0013 P6). It never decides whether code is written, how,
or what the answer is (GUARD-01, GUARD-03, GUARD-04).

A deliverable that is writing, an explanation, a design, an argument, or a proof or
derivation whose answer is a formula in symbolic parameters is not computational
(GUARD-03.2). Below the confidence floor, or on any error, the answer is that the task
is not computational and no brief is drafted: the brief is an addition, so doubt leaves
the task as it was.
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

COMPUTATIONAL = "ALGORITHMIC_OR_COMPUTATIONAL"
OTHER = "OTHER"


class ComputationRecipe(Sys1Recipe):
    """Evaluates whether an incoming request asks for an algorithm or a calculation."""

    @property
    def name(self) -> str:
        return "computation"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        task_text = state.get("request", "") or state.get("task_summary", "")
        question = Sys1Question(
            instructions=as_decision_instruction(
                "Classify the deliverable this request asks for: is producing it a matter of an algorithm "
                "or a calculation, or is it something else?"
            ),
            criteria={
                COMPUTATIONAL: (
                    "Producing the deliverable means writing, fixing or implementing a program or an "
                    "algorithm, searching or enumerating possibilities, or working out a number, a count, "
                    "a probability or another value from given quantities."
                ),
                OTHER: (
                    "The deliverable is writing, an explanation, a summary, a description, a design or an "
                    "argument; a proof or a derivation whose answer is a formula in symbolic parameters; a "
                    "decision, a refusal or a conversational reply. Any computation in it is incidental."
                ),
            },
            choices=[COMPUTATIONAL, OTHER],
        )
        return Sys1Request(state={"request": task_text}, questions={"computation": question})

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        answer = (response_body.get("answers") or {}).get("computation", {})
        gating = evaluate_confidence_gate(answer, confidence_floor=self.min_confidence)
        known = gating.choice in (COMPUTATIONAL, OTHER)  # an answer to some other question is no answer
        passed = gating.passed and known
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=gating.choice if known else OTHER,
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {"computational": result.verdict == COMPUTATIONAL, "confidence": result.confidence}

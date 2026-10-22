"""Working-notes neutrality recipe (Sys1, L147).

Decides whether the unconfirmed route's working notes (``interpretation`` and ``approach``) state how the task is
read and the method that will produce the result, or already state the result the deliverable is to establish
(UNC-03). The confirmed route asks the same question of its prompt and plan (``prompt_fidelity``,
``plan_advancement``).

Adheres to GUARD-01, GUARD-02, GUARD-04: no regex pattern matching, no task keywords, one System 1 decision with
tripartite confidence gating (ADR-0012).
"""

from __future__ import annotations

from typing import Any

from pdl_taskmaster.providers.sys1.gating import binary_entropy, evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

CHECK = "no_conclusion"
CHOICES = ("true", "false")
CONFIDENCE_FLOOR = 0.80

_BINARY_ENTROPY_CEILING = binary_entropy((1 + CONFIDENCE_FLOOR) / 2) + 1e-9


class WorkingNotesRecipe(Sys1Recipe):
    """Evaluates whether unconfirmed working notes leave the substantive result to the deliverable."""

    @property
    def name(self) -> str:
        return "working-notes"

    @property
    def min_confidence(self) -> float:
        return CONFIDENCE_FLOOR

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        question = Sys1Question(
            instructions=as_decision_instruction(
                "Compare the working notes (interpretation and approach) with the user's source request. Do the "
                "notes state only how the task is read and the method that will produce the result, without "
                "stating, assuming or previewing the substantive result the deliverable is to establish (its "
                "answer, value, count, expression, choice or verdict) (UNC-03)? Naming what is to be computed, "
                "derived or decided is neutral, and so is restating a value, claim or condition the request itself "
                "gives. Stating what the result is or will be is a conclusion."
            ),
            criteria={
                "true": "The notes state the reading of the task and the method, and leave the substantive result "
                        "to the deliverable.",
                "false": "The notes state, assume or derive the substantive result before the deliverable.",
            },
            choices=list(CHOICES),
        )
        return Sys1Request(
            state={
                "source_request": state.get("source_request", ""),
                "interpretation": state.get("interpretation", ""),
                "approach": state.get("approach", ""),
            },
            questions={CHECK: question},
        )

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        gate = evaluate_confidence_gate(
            (response_body.get("answers") or {}).get(CHECK, {}),
            confidence_floor=self.min_confidence,
            entropy_ceiling=_BINARY_ENTROPY_CEILING,
        )
        passed = gate.passed and gate.choice in CHOICES
        if not passed:
            verdict = "UNCERTAIN"
        elif gate.choice == "false":
            verdict = "PRE_CONCLUSIVE"
        else:
            verdict = "NEUTRAL"
        channel = {
            "choice": gate.choice,
            "confidence": round(gate.confidence, 4),
            "margin": round(gate.margin, 4),
            "entropy": round(gate.entropy, 4),
            "passed": gate.passed,
        }
        return RecipeResult(
            status="ready" if passed else "review",
            verdict=verdict,
            confidence=gate.confidence,
            margin=gate.margin,
            entropy=gate.entropy,
            passed_gating=passed,
            probabilities=gate.probabilities,
            duration_ms=duration_ms,
            labels={"channels": {CHECK: channel}},
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {
            "verdict": result.verdict,
            "confidence": result.confidence,
            "margin": result.margin,
            "entropy": result.entropy,
            "passed_gating": result.passed_gating,
            "channels": (result.labels or {}).get("channels", {}),
        }

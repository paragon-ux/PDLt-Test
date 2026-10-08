"""Prompt Semantic Fidelity and Anti-Evasion Recipe (Sys1).

Evaluates whether Prompt Pseudocode faithfully directs downstream execution to
compute and deliver what the user requested, rather than injecting unprompted
negative withholding clauses that command execution to evade, omit, or
placeholderize deliverables (e.g. 'without computing', 'without providing actual content'),
or silently omitting material requirements/deliverables (PROMPT-01).

Adheres strictly to GUARD-01, GUARD-02, GUARD-04: no regex pattern matching, no
hardcoded entity or task keywords, pure System 1 semantic classification with
tripartite confidence gating (ADR-0012).
"""

from __future__ import annotations

import math
from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

CHECKS = ("no_evasion", "complete_coverage")
CHOICES = ("true", "false")
CONFIDENCE_FLOOR = 0.80


def _binary_entropy(p: float) -> float:
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


_BINARY_ENTROPY_CEILING = _binary_entropy((1 + CONFIDENCE_FLOOR) / 2) + 1e-9


class PromptFidelityRecipe(Sys1Recipe):
    """Evaluates whether drafted Prompt Pseudocode avoids unprompted evasion and covers all requested deliverables."""

    @property
    def name(self) -> str:
        return "prompt-fidelity"

    @property
    def min_confidence(self) -> float:
        return CONFIDENCE_FLOOR

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        questions = {
            "no_evasion": Sys1Question(
                instructions=as_decision_instruction(
                    "Compare the drafted prompt pseudocode against the user's source request. Does the prompt "
                    "direct execution to compute and produce what the user requested, rather than commanding "
                    "execution to withhold, omit, avoid computing, or placeholderize the requested deliverable, "
                    "solutions, or concrete values? If the user explicitly requested an abstract schema, interface "
                    "contract, or templates without concrete data, answer true."
                ),
                criteria={
                    "true": "The prompt directs execution to compute, solve, or deliver what the user requested, "
                            "without injecting unprompted negative withholding directives.",
                    "false": "The prompt commands downstream execution to avoid computing, omit answers, or "
                             "placeholderize deliverables when the user requested the actual deliverable.",
                },
                choices=list(CHOICES),
            ),
            "complete_coverage": Sys1Question(
                instructions=as_decision_instruction(
                    "Compare the drafted prompt pseudocode against the user's source request. Does the prompt "
                    "preserve all material deliverables, functional capabilities, and explicit constraints "
                    "requested by the user, without silently omitting or dropping parts of the requested work "
                    "(e.g. omitting required functions, test suites, edge case handling, or secondary deliverables)? "
                    "If the prompt preserves all requested deliverables, answer true."
                ),
                criteria={
                    "true": "The prompt covers all material requirements and deliverables from the user request.",
                    "false": "The prompt silently drops, omits, or truncates material deliverables or capabilities "
                             "requested by the user.",
                },
                choices=list(CHOICES),
            ),
        }
        return Sys1Request(
            state={
                "source_request": state.get("source_request", ""),
                "drafted_prompt": state.get("drafted_prompt", ""),
            },
            questions=questions,
        )

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        answers = response_body.get("answers", {})
        labels: dict[str, bool | None] = {}
        gated: dict[str, bool] = {}
        min_conf = 1.0
        failed: list[str] = []
        for key in CHECKS:
            gating = evaluate_confidence_gate(
                answers.get(key, {}),
                confidence_floor=self.min_confidence,
                entropy_ceiling=_BINARY_ENTROPY_CEILING,
            )
            passed = gating.passed and gating.choice in CHOICES
            gated[key] = passed
            labels[key] = (gating.choice == "true") if passed else None
            min_conf = min(min_conf, gating.confidence)
            if passed and gating.choice == "false":
                failed.append(key)

        if failed:
            if "no_evasion" in failed:
                verdict = "UNPROMPTED_EVASION"
            else:
                verdict = "INCOMPLETE_COVERAGE"
        elif all(labels.get(k) is True for k in CHECKS):
            verdict = "FAITHFUL"
        else:
            verdict = "UNCERTAIN"

        passed_gating = verdict != "UNCERTAIN"
        return RecipeResult(
            status="ready" if passed_gating else "review",
            verdict=verdict,
            confidence=min_conf,
            margin=0.0,
            entropy=0.0,
            passed_gating=passed_gating,
            probabilities={},
            duration_ms=duration_ms,
            labels={"checks": labels, "failed": failed, "gated": gated},
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        labels = result.labels or {}
        return {
            "verdict": result.verdict,
            "failed_checks": list(labels.get("failed", [])),
            "confidence": result.confidence,
            "passed_gating": result.passed_gating,
        }

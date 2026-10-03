"""PlanAdvancement Sys1 Decision Recipe.

Decides whether a drafted Response Plan exposes an approach (PLAN-02, minimum
sufficient procedure) or only restates the confirmed Prompt Pseudocode. Three
task-neutral checks, each its own question so a failure names which one:

- solution_actions: the plan adds a solution action or deduction the prompt does
  not already state (rewording, reordering, splitting a prompt line, or adding
  record/output bookkeeping adds none);
- constraints_addressed: the plan says how the approach handles the conditions
  that keep the task from being solved directly;
- advances: a reader of the plan learns how the result will be obtained.

A fourth question asks whether the confirmed prompt already states the method; when
it confidently does, a plan that adds nothing is not rejected (PLAN-02 asks only for
enough procedure to judge the approach, and the prompt already exposes it).

The checks never ask for the result itself: PLAN-04 forbids a plan that answers
the request. Nothing here names a method, algorithm or problem class (GUARD-01,
GUARD-04), and no decision text reaches the drafting model; the host forwards only
which check failed.
"""

from __future__ import annotations

import math
from typing import Any

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

CHECKS = ("solution_actions", "constraints_addressed", "advances")
# Not a check on the plan: when the confirmed prompt already states how the result is
# obtained, a plan has nothing to add and is not rejected for restating it.
PROMPT_STATES_METHOD = "prompt_states_method"
CHOICES = ("true", "false")


def _binary_entropy(p: float) -> float:
    return -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


# The review-time floor, as for ReviewFacetsRecipe.
CONFIDENCE_FLOOR = 0.80
# For a two-choice question System 1's confidence is the top-two margin, and the
# margin and normalized entropy are both functions of the top probability, so the
# tripartite gate (ADR-0012) reduces to one floor. The default entropy ceiling (0.35)
# would silently require a top probability of about 0.935; the ceiling here is the
# entropy at the floor's top probability, so the confidence floor is the binding check.
_BINARY_ENTROPY_CEILING = _binary_entropy((1 + CONFIDENCE_FLOOR) / 2) + 1e-9


class PlanAdvancementRecipe(Sys1Recipe):
    """Evaluates whether a response plan advances beyond the confirmed prompt."""

    @property
    def name(self) -> str:
        return "plan-advancement"

    @property
    def min_confidence(self) -> float:
        return CONFIDENCE_FLOOR

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        questions = {
            "solution_actions": Sys1Question(
                instructions=as_decision_instruction(
                    "Compare the response plan with the confirmed prompt. Does the plan contain at least one "
                    "concrete solution action or deduction that the prompt does not already state? Rewording a "
                    "prompt line, reordering prompt lines, splitting a prompt line into one line per item or "
                    "input (read each input, determine each part), and adding steps that only read, record, "
                    "note, store, format or output something are not solution actions. Naming an action without "
                    "its content (devise a strategy, apply the appropriate method, analyze the problem, use logic "
                    "to deduce the answer) is not a solution action either: the plan must say what the strategy "
                    "or deduction is."
                ),
                criteria={
                    "true": "The plan states at least one action or deduction, with its content, beyond the prompt's "
                            "own lines, that works toward the result.",
                    "false": "Every plan line restates, rewords, reorders or splits the prompt per item, names an "
                             "action without its content, or only reads, records, notes, stores, formats or outputs.",
                },
                choices=list(CHOICES),
            ),
            "constraints_addressed": Sys1Question(
                instructions=as_decision_instruction(
                    "Identify the conditions in the confirmed prompt that keep the task from being solved "
                    "directly (unknowns, ambiguities, adversarial or unreliable parts, limits on what may be "
                    "used). Does the plan say how its approach handles each of them? Repeating that a condition "
                    "exists does not handle it. If the prompt has no such condition, answer true."
                ),
                criteria={
                    "true": "The plan states how the approach copes with each condition that makes the task "
                            "non-trivial, or the task has no such condition.",
                    "false": "At least one such condition is only repeated or ignored by the plan.",
                },
                choices=list(CHOICES),
            ),
            "advances": Sys1Question(
                instructions=as_decision_instruction(
                    "Would a reader of the plan learn how the requested result will be obtained, beyond what the "
                    "confirmed prompt already says? A plan does not need to state the result itself, and should "
                    "not."
                ),
                criteria={
                    "true": "The plan shows how the result will be reached.",
                    "false": "The plan restates the task: it says what to obtain but not how.",
                },
                choices=list(CHOICES),
            ),
            PROMPT_STATES_METHOD: Sys1Question(
                instructions=as_decision_instruction(
                    "Look only at the confirmed prompt. Does it already state how the result will be obtained: "
                    "the method, the key steps or the deductions, so that a plan could add nothing beyond "
                    "following it? A prompt that only says to determine, deduce, explain or solve something, "
                    "without saying how, does not state the method."
                ),
                criteria={
                    "true": "The prompt itself states how the result is reached.",
                    "false": "The prompt states what to obtain but not how.",
                },
                choices=list(CHOICES),
            ),
        }
        return Sys1Request(
            state={
                "confirmed_prompt": state.get("confirmed_prompt", ""),
                "response_plan": state.get("response_plan", ""),
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
        for key in (*CHECKS, PROMPT_STATES_METHOD):
            gating = evaluate_confidence_gate(
                answers.get(key, {}), confidence_floor=self.min_confidence, entropy_ceiling=_BINARY_ENTROPY_CEILING
            )
            passed = gating.passed and gating.choice in CHOICES
            gated[key] = passed
            labels[key] = (gating.choice == "true") if passed else None
            if key in CHECKS:
                min_conf = min(min_conf, gating.confidence)
        failed = [key for key in CHECKS if labels[key] is False]
        if failed and labels[PROMPT_STATES_METHOD] is True:
            verdict = "PROMPT_STATES_METHOD"  # nothing for the plan to add: not a restating plan
            failed = []
        elif failed:
            verdict = "RESTATES"  # one confident failure is enough
        elif all(labels[key] is True for key in CHECKS):
            verdict = "ADVANCES"
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
        checks = dict(labels.get("checks", {}))
        return {
            "verdict": result.verdict,
            "failed_checks": list(labels.get("failed", [])),
            "checks": {k: v for k, v in checks.items() if k in CHECKS},
            "prompt_states_method": checks.get(PROMPT_STATES_METHOD),
        }

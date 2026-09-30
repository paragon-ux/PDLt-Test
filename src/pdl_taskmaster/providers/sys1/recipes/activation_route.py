"""ActivationRoute Sys1 Decision Recipe (ADR-0020).

Evaluates whether an initial user request requires the protocol, can bypass,
discusses protocol operation, or must be immediately refused due to environmental,
scope, or policy boundaries.

Environment settings (policy scope, offline sandbox, knowledge cutoff) are recipe
STATE routed by System 1; there is no keyword or year pattern matching (GUARD-02).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

def _env_value(env: dict[str, Any], key: str, var: str, default: str) -> Any:
    """Explicit environment state wins (including falsy values such as False)."""
    value = env.get(key)
    return value if value is not None else os.environ.get(var, default)


class ActivationRouteRecipe(Sys1Recipe):
    """Evaluates whether an initial user request requires the protocol or can bypass."""

    @property
    def name(self) -> str:
        return "activation-route"

    @property
    def min_confidence(self) -> float:
        return 0.85

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        request_text = state.get("request", "")
        env = state.get("env") or {}
        sandbox_network = _env_value(env, "sandbox_network", "PDLT_SANDBOX_NETWORK", "false")
        policy_scope = _env_value(env, "policy_scope", "PDLT_POLICY_SCOPE", "technical")
        knowledge_cutoff = _env_value(env, "knowledge_cutoff", "PDLT_KNOWLEDGE_CUTOFF", "2024-06")

        instruction = as_decision_instruction(
            "Determine the correct routing for this user message: does it request substantive technical work "
            "requiring protocol governance, discuss protocol operation, bypass, or must it be refused immediately "
            "due to environmental or policy bounds?"
        )
        criteria = {
            "APPLY_PROTOCOL": "The message requests substantive task work, analysis, problem solving, or deliverables within supported technical scope.",
            "PROTOCOL_DISCUSSION": "The message asks questions about how the harness or protocol works without requesting substantive task work.",
            "BYPASS": "The message is a pure greeting, farewell, or meta-interaction requiring no substantive work.",
            "BLOCKED_BY_HIGHER_PRIORITY": (
                "The message must be refused immediately because, given the environment state, it falls outside "
                "the stated policy_scope, requires network access while sandbox_network is disabled, or depends on "
                "events occurring after the stated knowledge_cutoff, which cannot be known without live search."
            ),
        }
        question = Sys1Question(
            instructions=instruction,
            criteria=criteria,
            choices=["APPLY_PROTOCOL", "PROTOCOL_DISCUSSION", "BYPASS", "BLOCKED_BY_HIGHER_PRIORITY"],
        )
        return Sys1Request(
            state={
                "request": request_text,
                "sandbox_network": sandbox_network,
                "policy_scope": policy_scope,
                "knowledge_cutoff": knowledge_cutoff,
            },
            questions={"route": question},
        )

    def parse_response(
        self, response_body: dict[str, Any], *, duration_ms: float = 0.0
    ) -> RecipeResult:
        answers = response_body.get("answers", {})
        ans = answers.get("route", {})
        gating = evaluate_confidence_gate(ans, confidence_floor=self.min_confidence)
        choice = gating.choice or "APPLY_PROTOCOL"
        status = "ready" if gating.passed else "review"
        metadata = dict(response_body.get("metadata", {}))

        if choice == "BLOCKED_BY_HIGHER_PRIORITY":
            refusal_response = ans.get("response") or ans.get("refusal_response") or (
                "This request exceeds the supported policy and environmental scope boundaries of this system."
            )
            metadata["refusal_response"] = refusal_response

        return RecipeResult(
            status=status,
            verdict=choice,
            confidence=gating.confidence,
            margin=gating.margin,
            entropy=gating.entropy,
            passed_gating=gating.passed,
            probabilities=gating.probabilities,
            duration_ms=duration_ms,
            metadata=metadata,
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        route = result.verdict if result.passed_gating else "APPLY_PROTOCOL"
        response = None
        if route == "BLOCKED_BY_HIGHER_PRIORITY":
            response = (
                result.metadata.get("refusal_response")
                or "This request exceeds the supported policy and environmental scope boundaries of this system."
            )
        return {
            "route": route,
            "response": response,
        }

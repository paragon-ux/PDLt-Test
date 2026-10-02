"""Unit tests for Sys1 Decision Recipes (Phase 2)."""

from __future__ import annotations

import pytest

from pdl_taskmaster.providers.sys1.recipes.activation_route import ActivationRouteRecipe
from pdl_taskmaster.providers.sys1.recipes.confirmation_match import ConfirmationMatchRecipe
from pdl_taskmaster.providers.sys1.recipes.review_facets import ReviewFacetsRecipe


def test_confirmation_match_agrees() -> None:
    recipe = ConfirmationMatchRecipe()
    req = recipe.build_request({"proposal": "Prompt Pseudocode...", "response": "confirm"})
    assert "confirmation" in req.questions
    assert "agrees" in req.questions["confirmation"].choices

    backend_response = {
        "answers": {
            "confirmation": {
                "choice": "agrees",
                "confidence": 0.98,
                "probabilities": {"agrees": 0.98, "rejects": 0.01, "unclear": 0.01},
            }
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=12.5)
    assert result.status == "ready"
    assert result.verdict == "agrees"
    assert result.passed_gating is True

    wire = recipe.map_to_wire(result)
    assert wire["kind"] == "REVIEW_FACTS"
    assert wire["progression_requested"] is True
    assert wire["task_change_dimensions"] == []
    assert wire["approach_change_dimensions"] == []


def test_confirmation_match_rejects() -> None:
    recipe = ConfirmationMatchRecipe()
    backend_response = {
        "answers": {
            "confirmation": {
                "choice": "rejects",
                "confidence": 0.95,
                "probabilities": {"agrees": 0.02, "rejects": 0.95, "unclear": 0.03},
            }
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=10.0)
    assert result.status == "ready"
    assert result.verdict == "rejects"
    wire = recipe.map_to_wire(result)
    assert wire["kind"] == "CANCEL"


def test_confirmation_match_unclear_falls_to_review() -> None:
    recipe = ConfirmationMatchRecipe()
    backend_response = {
        "answers": {
            "confirmation": {
                "choice": "unclear",
                "confidence": 0.92,
                "probabilities": {"agrees": 0.04, "rejects": 0.04, "unclear": 0.92},
            }
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=10.0)
    assert result.status == "review"
    assert result.verdict == "unclear"


def test_review_facets_separates_task_and_approach() -> None:
    recipe = ReviewFacetsRecipe()
    req = recipe.build_request({
        "artifact_kind": "plan",
        "content": "Step 1... Step 2...",
        "feedback": "you have to plan your response now",
    })
    assert len(req.questions) == 4
    assert "revises_task" in req.questions
    assert "revises_approach" in req.questions

    # Simulate Sys1 classifying feedback about the plan as revises_approach=true, revises_task=false
    backend_response = {
        "answers": {
            "revises_task": {
                "choice": "false",
                "confidence": 0.95,
                "probabilities": {"true": 0.05, "false": 0.95},
            },
            "revises_approach": {
                "choice": "true",
                "confidence": 0.94,
                "probabilities": {"true": 0.94, "false": 0.06},
            },
            "requests_clarification": {
                "choice": "false",
                "confidence": 0.99,
                "probabilities": {"true": 0.01, "false": 0.99},
            },
            "is_acknowledgment": {
                "choice": "false",
                "confidence": 0.99,
                "probabilities": {"true": 0.01, "false": 0.99},
            },
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=18.0)
    assert result.status == "ready"
    assert result.verdict == "revise_approach"
    assert result.labels["revises_task"] is False
    assert result.labels["revises_approach"] is True

    wire = recipe.map_to_wire(result)
    assert wire["kind"] == "REVIEW_FACTS"
    assert wire["task_change_dimensions"] == []
    assert wire["approach_change_dimensions"] == ["JUSTIFICATION_PROCEDURE"]
    assert wire["progression_requested"] is False


def test_activation_route_recipe() -> None:
    recipe = ActivationRouteRecipe()
    req = recipe.build_request({"request": "Partition the string racecar into palindromes."})
    assert "route" in req.questions
    assert "BLOCKED_BY_HIGHER_PRIORITY" in req.questions["route"].choices

    backend_response = {
        "answers": {
            "route": {
                "choice": "APPLY_PROTOCOL",
                "confidence": 0.99,
                "probabilities": {"APPLY_PROTOCOL": 0.99, "PROTOCOL_DISCUSSION": 0.005, "BYPASS": 0.005},
            }
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=15.0)
    assert result.status == "ready"
    assert result.verdict == "APPLY_PROTOCOL"

    wire = recipe.map_to_wire(result)
    assert wire["route"] == "APPLY_PROTOCOL"
    assert wire["response"] is None


def test_activation_route_state_carries_environment_settings(monkeypatch) -> None:
    monkeypatch.setenv("PDLT_POLICY_SCOPE", "technical")
    monkeypatch.setenv("PDLT_SANDBOX_NETWORK", "false")
    monkeypatch.setenv("PDLT_KNOWLEDGE_CUTOFF", "2031-02")
    req = ActivationRouteRecipe().build_request({"request": "anything"})
    assert req.state["policy_scope"] == "technical"
    assert req.state["sandbox_network"] == "false"
    assert req.state["knowledge_cutoff"] == "2031-02"
    criteria = req.questions["route"].criteria["BLOCKED_BY_HIGHER_PRIORITY"]
    assert "policy_scope" in criteria and "sandbox_network" in criteria and "knowledge_cutoff" in criteria


def test_activation_route_explicit_env_state_beats_process_env(monkeypatch) -> None:
    monkeypatch.setenv("PDLT_SANDBOX_NETWORK", "true")
    req = ActivationRouteRecipe().build_request({"request": "x", "env": {"sandbox_network": False}})
    assert req.state["sandbox_network"] is False


def test_activation_route_has_no_pattern_matching() -> None:
    assert not hasattr(ActivationRouteRecipe, "classify_text_deterministic")


def test_activation_route_sys1_blocked_wire_conformance() -> None:
    recipe = ActivationRouteRecipe()
    backend_response = {
        "answers": {
            "route": {
                "choice": "BLOCKED_BY_HIGHER_PRIORITY",
                "confidence": 0.96,
                "probabilities": {"BLOCKED_BY_HIGHER_PRIORITY": 0.96, "APPLY_PROTOCOL": 0.04},
                "refusal_response": "Requested operations exceed defined policy boundary.",
            }
        }
    }
    result = recipe.parse_response(backend_response, duration_ms=8.0)
    assert result.status == "ready"
    assert result.verdict == "BLOCKED_BY_HIGHER_PRIORITY"

    wire = recipe.map_to_wire(result)
    assert wire["route"] == "BLOCKED_BY_HIGHER_PRIORITY"
    assert wire["response"] == "Requested operations exceed defined policy boundary."

    from pdl_taskmaster.runtime.wire_payloads import ActivationDecisionPayload
    # Must pass Pydantic SSOT validation without extra/missing fields
    payload = ActivationDecisionPayload.model_validate(wire)
    assert payload.route.value == "BLOCKED_BY_HIGHER_PRIORITY"
    assert payload.response == "Requested operations exceed defined policy boundary."



def test_problem_class_routes_checkable_exact_values_to_verified_execution() -> None:
    """Live sessions: a fully specified question with one exact numeric answer was
    classified standard ("word problems" was a STANDARD criterion), so the answer
    was published with nothing checked."""
    from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe

    question = ProblemClassRecipe().build_request({"request": "any task"}).questions["problem_class"]
    verified = question.criteria["VERIFIED_EXECUTION"].lower()
    standard = question.criteria["STANDARD_EXECUTION"].lower()
    assert "fully specified, concrete inputs" in verified
    for kind in ("single exact value", "count", "probability", "expected value"):
        assert kind in verified, kind
    # GUARD-03.2: symbolic-parameter answers, proofs and open analysis stay standard.
    assert "symbolic parameters" in standard and "proof" in standard and "open-ended analysis" in standard
    assert "word problem" not in standard
    # A witness is requested, never code (GUARD-03).
    assert "code" not in verified and "python" not in verified and "program" not in verified


def test_follow_up_recipe_gates_only_a_confident_new_request() -> None:
    from pdl_taskmaster.providers.sys1.recipes.follow_up import FollowUpRecipe

    recipe = FollowUpRecipe()
    request = recipe.build_request({"previous_request": "task one", "message": "incorrect, try again"})
    assert request.state == {"previous_request": "task one", "message": "incorrect, try again"}
    assert request.questions["follow_up"].choices == ["FOLLOW_UP", "NEW_REQUEST"]

    def decide(choice, confidence):
        body = {"answers": {"follow_up": {"choice": choice, "confidence": confidence,
                                          "probabilities": {choice: confidence, "other": 1 - confidence}}}}
        return recipe.map_to_wire(recipe.parse_response(body))["follow_up"]

    assert decide("NEW_REQUEST", 0.95) is False
    assert decide("FOLLOW_UP", 0.95) is True
    assert decide("NEW_REQUEST", 0.6) is True  # below the floor: keep the merge
    assert decide("WITHIN_10M_STEPS", 0.97) is True  # not one of the choices

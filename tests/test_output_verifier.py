from __future__ import annotations

import pytest

from pdl_taskmaster.verification.checkers.fallback import FallbackChecker
from pdl_taskmaster.verification.output_verifier import OutputVerifier


def test_fallback_checker():
    checker = FallbackChecker()
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"result_map": {"x": 1}},
    }
    verdict = checker.check(witness, {})
    assert verdict.valid
    assert verdict.provisional
    assert "Provisional" in verdict.diagnostic


def test_validate_result_ir_empty_files_allowed(tmp_path):
    from pdl_taskmaster.runtime.result_ir import validate_result_ir

    ir = {
        "files": [],
        "reconciliation": [
            {
                "requirement": "R1",
                "status": "satisfied",
                "evidence": {"path": "execution://body"},
            }
        ],
        "open_defects": [],
        "witness": {
            "polarity": "negative",
            "evidence": {"path": "execution://witness"},
            "search_exhausted": True,
            "nodes_explored": 10,
            "method": "exhaustive_search",
        },
    }
    errors, normalized = validate_result_ir(
        ir,
        workspace_path=tmp_path,
        requirements=["R1: DEFINE the problem."],
        execution_body="false",
    )
    assert not errors
    assert normalized["files"] == []


def test_validate_result_ir_echoed_requirement_on_satisfied(tmp_path):
    from pdl_taskmaster.runtime.result_ir import validate_result_ir

    ir = {
        "files": [],
        "reconciliation": [
            {
                "requirement": "R1",
                "status": "satisfied",
                "evidence": {
                    "path": "execution://body",
                    "observed": "DEFINE the problem.",
                },
            }
        ],
        "open_defects": [],
    }
    # Delivery body is just "false", but model echoed the prompt requirement
    errors, normalized = validate_result_ir(
        ir,
        workspace_path=tmp_path,
        requirements=["DEFINE the problem."],
        execution_body="false",
    )
    assert not errors


def test_render_instructions_with_verified_execution():
    from pdl_taskmaster.runtime.result_ir import render_instructions

    instructions = render_instructions(
        ["DEFINE the problem."],
        requires_verified_execution=True,
    )
    assert "WITNESS:" in instructions and "json.dumps" in instructions
    assert "positive" in instructions and "negative" in instructions
    assert "open_defects" in instructions
    assert "DEFINE the problem." not in instructions  # RS-02: requirements are not rendered


def test_requirement_wording_is_never_scanned_for_vocabulary(tmp_path):
    """GUARD-02/03: an honest negative result is judged by its schema, not by the
    verbs in the requirement it reconciles."""
    from pdl_taskmaster.runtime.result_ir import validate_result_ir

    ir = {
        "files": [],
        "reconciliation": [
            {"requirement": "R1", "status": "satisfied", "evidence": {"path": "execution://body"}},
            {"requirement": "R2", "status": "satisfied", "evidence": {"path": "execution://body"}},
        ],
        "open_defects": [],
        "witness": {"polarity": "negative", "basis": "proof", "argument": "Parity forbids it."},
    }
    errors, _ = validate_result_ir(
        ir, workspace_path=tmp_path,
        requirements=["VERIFY whether a solution exists.", "GENERATE one concrete example."],
        execution_body="No example exists.",
    )
    assert errors == []


def test_output_verifier_dispatch():
    verifier = OutputVerifier()
    # No problem-specific checker ships in the harness: every domain is checked by the fallback.
    assert verifier.detect_domain({"domain": "general"}) == "general"
    assert verifier.get_checker("general").name == "fallback"
    assert verifier.get_checker("some_declared_domain").name == "fallback"
    # Problem text is never inspected for domain vocabulary (GUARD-02)
    assert verifier.detect_domain("find a cover of these sets") is None


def test_unregistered_typed_domain_is_provisional():
    verdict = OutputVerifier().check(
        {"domain": "undeclared", "polarity": "positive", "data": {"answer": [1, 2]}}, {}
    )
    assert verdict.valid and verdict.provisional


def test_negative_search_witness_requires_positive_state_count():
    verdict = FallbackChecker().check(
        {"polarity": "negative", "search_exhausted": True, "nodes_explored": 0, "method": "search"}, {}
    )
    assert not verdict.valid
    assert "nodes_explored" in verdict.diagnostic


def test_negative_witness_by_proof_is_first_class():
    """GUARD-03: an impossibility proof needs no fabricated search telemetry."""
    verdict = FallbackChecker().check(
        {"polarity": "negative", "basis": "proof", "argument": "The constraints sum to an odd total."}, {}
    )
    assert verdict.valid and verdict.provisional
    assert verdict.details["basis"] == "proof"
    inferred = FallbackChecker().check({"polarity": "negative", "argument": "Parity contradiction."}, {})
    assert inferred.valid and inferred.details["basis"] == "proof"
    empty = FallbackChecker().check({"polarity": "negative", "basis": "proof", "argument": " "}, {})
    assert not empty.valid

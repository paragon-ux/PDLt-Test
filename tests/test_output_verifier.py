from __future__ import annotations

import pytest

from pdl_taskmaster.verification.checkers.fallback import FallbackChecker
from pdl_taskmaster.verification.checkers.partition_sum_triples import (
    PartitionSumTriplesChecker,
)
from pdl_taskmaster.verification.output_verifier import OutputVerifier


def test_partition_sum_triples_valid_positive():
    checker = PartitionSumTriplesChecker()
    # 2 valid triples: [2, 3, 5], [1, 7, 8]
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "triples": [
                [2, 3, 5],
                [1, 7, 8],
            ]
        },
    }
    constraints = {
        "input_elements": [1, 2, 3, 5, 7, 8],
        "expected_triples_count": 2,
    }
    verdict = checker.check(witness, constraints)
    assert verdict.valid
    assert verdict.diagnostic is None
    assert verdict.details["triples_verified"] == 2


def test_partition_sum_triples_arithmetic_failure():
    checker = PartitionSumTriplesChecker()
    # [2, 3, 6] -> 2 + 3 != 6
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "triples": [
                [2, 3, 6],
            ]
        },
    }
    verdict = checker.check(witness, {})
    assert not verdict.valid
    assert "violates sum constraint" in verdict.diagnostic


def test_partition_sum_triples_duplicate_elements_failure():
    checker = PartitionSumTriplesChecker()
    # 3 appears in both triples
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "triples": [
                [1, 2, 3],
                [3, 4, 7],
            ]
        },
    }
    verdict = checker.check(witness, {})
    assert not verdict.valid
    assert "Triples are not disjoint" in verdict.diagnostic
    assert "duplicate elements" in verdict.diagnostic


def test_partition_sum_triples_missing_element_failure():
    checker = PartitionSumTriplesChecker()
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "triples": [
                [1, 2, 3],
            ]
        },
    }
    # Expected inputs include 10, but 10 is missing
    constraints = {"input_elements": [1, 2, 3, 10]}
    verdict = checker.check(witness, constraints)
    assert not verdict.valid
    assert "misses required elements" in verdict.diagnostic
    assert "10" in verdict.diagnostic


def test_partition_sum_triples_valid_negative():
    checker = PartitionSumTriplesChecker()
    witness = {
        "polarity": "negative",
        "evidence": {"path": "execution://witness"},
        "search_exhausted": True,
        "nodes_explored": 4820,
        "method": "backtracking_mrv",
    }
    verdict = checker.check(witness, {})
    assert verdict.valid
    assert verdict.diagnostic is None
    assert verdict.details["search_exhausted"] is True


def test_partition_sum_triples_incomplete_negative_failure():
    checker = PartitionSumTriplesChecker()
    # search_exhausted is False -> unproven
    witness = {
        "polarity": "negative",
        "evidence": {"path": "execution://witness"},
        "search_exhausted": False,
        "nodes_explored": 100,
        "method": "greedy_pass",
    }
    verdict = checker.check(witness, {})
    assert not verdict.valid
    assert "search_exhausted" in verdict.diagnostic


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


def test_output_verifier_dispatch():
    verifier = OutputVerifier()

    # Typed domain routes to its checker
    domain = verifier.detect_domain({"domain": "partition_sum_triples"})
    assert domain == "partition_sum_triples"
    checker = verifier.get_checker(domain)
    assert checker.name == "partition_sum_triples"

    # Problem text is never inspected for domain vocabulary (GUARD-02)
    assert verifier.detect_domain("Partition 45 integers into Schur triples") is None
    fallback_checker = verifier.get_checker(None)
    assert fallback_checker.name == "fallback"


def test_verifier_uses_typed_witness_domain():
    verifier = OutputVerifier()
    witness = {
        "domain": "partition_sum_triples",
        "polarity": "positive",
        "data": {"triples": [[1, 2, 3], [3, 4, 7]]},
    }
    verdict = verifier.check(witness, {}, domain="general")
    assert not verdict.valid  # strict checker selected by typed domain; triples not disjoint
    assert "not disjoint" in verdict.diagnostic


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
        requirements=["R1: DEFINE problem as Schur Triples detection."],
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
                    "observed": "DEFINE problem as Schur Triples detection.",
                },
            }
        ],
        "open_defects": [],
    }
    # Delivery body is just "false", but model echoed the prompt requirement
    errors, normalized = validate_result_ir(
        ir,
        workspace_path=tmp_path,
        requirements=["DEFINE problem as Schur Triples detection."],
        execution_body="false",
    )
    assert not errors


def test_render_instructions_with_verified_execution():
    from pdl_taskmaster.runtime.result_ir import render_instructions

    instructions = render_instructions(
        ["DEFINE problem as Schur Triples detection."],
        requires_verified_execution=True,
    )
    assert "WITNESS REQUIREMENT" in instructions
    assert "execution://witness" in instructions
    assert "positive" in instructions
    assert "negative" in instructions


def test_partition_sum_triples_rejects_incomplete_partition():
    verifier = OutputVerifier()
    # Only 2 triples provided; structured input_elements list 9 numbers
    incomplete_witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"triples": [[1, 2, 3], [4, 5, 9]]},
    }
    verdict = verifier.check(
        incomplete_witness,
        {"input_elements": [1, 2, 3, 4, 5, 9, 6, 7, 13]},
        domain="partition_sum_triples",
    )
    assert not verdict.valid
    assert "Partition misses required elements" in verdict.diagnostic


def test_partition_sum_triples_does_not_scrape_prompt_text():
    verifier = OutputVerifier()
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"triples": [[1, 2, 3]]},
    }
    prompt = "1 2 3 4 5 6 7 8 9 10"
    verdict = verifier.check(witness, {"prompt_body": prompt}, domain="partition_sum_triples")
    assert verdict.valid  # coverage is not inferred from prompt text


def test_negative_witness_single_node_rejected_regardless_of_wording():
    checker = PartitionSumTriplesChecker()
    witness = {
        "polarity": "negative",
        "search_exhausted": True,
        "nodes_explored": 1,
        "method": "mathematical parity argument, divisible by modulo",
    }
    verdict = checker.check(
        witness, {}, body="mathematical divisible modulo parity cardinality"
    )
    assert not verdict.valid


def test_reject_zero_nodes_explored_negative_witness():
    from pdl_taskmaster.verification.checkers.partition_sum_triples import PartitionSumTriplesChecker
    from pdl_taskmaster.verification.checkers.fallback import FallbackChecker

    pst = PartitionSumTriplesChecker()
    fb = FallbackChecker()

    dummy_neg = {
        "polarity": "negative",
        "evidence": {"path": "execution://witness"},
        "search_exhausted": True,
        "nodes_explored": 0,
        "method": "MRV backtracking",
    }
    v_pst = pst.check(dummy_neg, {"prompt_body": "test problem"}, body="dummy code")
    assert not v_pst.valid
    assert "nodes_explored" in v_pst.diagnostic
    assert "greater than 0" in v_pst.diagnostic

    v_fb = fb.check(dummy_neg, {})
    assert not v_fb.valid
    assert "nodes_explored" in v_fb.diagnostic
    assert "greater than 0" in v_fb.diagnostic


def test_reject_contradictory_reconciliation(tmp_path):
    from pdl_taskmaster.runtime.result_ir import validate_result_ir

    ir = {
        "files": [
            {
                "filename": "solver.py",
                "satisfies": ["R1", "R2", "R3"],
                "evidence": {"path": "execution://body", "observed": "import sys"},
            }
        ],
        "reconciliation": [
            {
                "requirement": "R1",
                "status": "satisfied",
                "evidence": {"path": "execution://body", "observed": "import sys"},
            },
            {
                "requirement": "R2",
                "status": "satisfied",
                "evidence": {"path": "execution://witness", "observed": 'polarity": "negative"'},
            },
        ],
        "open_defects": [],
        "witness": {
            "polarity": "negative",
            "evidence": {"path": "execution://witness"},
            "search_exhausted": True,
            "nodes_explored": 500,
            "method": "MRV backtracking",
        },
    }
    requirements = [
        "R1: VERIFY whether a partition exists.",
        "R2: GENERATE one concrete example of 15 triples.",
    ]
    errors, normalized = validate_result_ir(
        ir,
        workspace_path=tmp_path,
        requirements=requirements,
        execution_body="import sys",
    )
    assert errors
    assert any("A negative witness cannot satisfy a generation requirement" in e for e in errors)


def test_problem_domain_enum_routing():
    from pdl_taskmaster.verification.checkers.base import ProblemDomain
    from pdl_taskmaster.verification.output_verifier import OutputVerifier

    verifier = OutputVerifier()
    domain = verifier.detect_domain(ProblemDomain.PARTITION_SUM_TRIPLES)
    assert domain == "partition_sum_triples"
    checker = verifier.get_checker(ProblemDomain.PARTITION_SUM_TRIPLES)
    assert checker.name == "partition_sum_triples"





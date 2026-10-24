"""L116: CLOSED_SUCCESS means the host's checks established the result, not that the protocol completed. A result
resting on a claim the host cannot check (a negative claim, L110; a deliverable declaring requirements open; a
positive result established by an argument, L119) is
published and closes CLOSED_UNVERIFIED (exit 5); a failed verification or a malformed reply closes CLOSED_CANCELLED
(exit 1); a witness printed by a program the host ran still closes CLOSED_SUCCESS. All offline; no model call."""
from __future__ import annotations

import json
import sys

import run_catalogue
from pdl_taskmaster.controller.mechanical_controller import ProtocolState, Stage
from pdl_taskmaster.runtime import presentation
from pdl_taskmaster.runtime.text_blocks import split_published_ir

from test_execution_phase import _incomplete_ir, _ir, _kinds, _run
from test_l104_witness_provenance import COMPUTING, _unconfirmed

NEGATIVE_SEARCH = ("import json\nnodes = 0\nfor x in range(27):\n    nodes += 1\n"
                   "print('WITNESS: ' + json.dumps({'polarity': 'negative', 'basis': 'search', "
                   "'search_exhausted': True, 'nodes_explored': nodes, 'method': 'enumeration'}))")
NEGATIVE_PROOF = {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "proof",
                  "argument": "The constraints force an odd total equal to an even one."}
POSITIVE = ("import json\nvalues = [a * b for a in range(2, 5) for b in range(3, 6)]\n"
            "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'largest': max(values)}}))")
LITERAL = ("import json\n"
           "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'triples': [[12, 23, 35]]}}))")
VERIFIED = "VERIFIED_EXECUTION"


def _status(engine) -> str:
    return engine.workspace.read_turn_status(engine.workspace.turn_id)["status"]


def _unverified_reasons(events) -> list[str]:
    return [e["payload"]["reason"] for e in events if e["kind"] == "CLOSED_UNVERIFIED"]


# A failed verification or a malformed reply cannot close as a success.

def test_a_failed_verification_closes_cancelled(tmp_path):
    unprinted = {"kind": "RESULT", "body": "The answer is 9.", "result_ir": _ir()}  # no program prints a witness
    engine, _, _, events = _run(tmp_path, [unprinted] * 8, problem_class=VERIFIED)
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED and _status(engine) == "CLOSED_CANCELLED"
    assert "VERIFICATION_FAILED" in _kinds(events) and not _unverified_reasons(events)


def test_a_malformed_execution_reply_closes_cancelled(tmp_path):
    engine, _, _, events = _run(tmp_path, ['{"kind": "RESULT", "body": "unterminated'] * 8, problem_class=VERIFIED)
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED and _status(engine) == "CLOSED_CANCELLED"
    assert not _unverified_reasons(events)


# A result the host cannot establish is published, labelled and closes CLOSED_UNVERIFIED.

def test_a_negative_claim_printed_by_a_program_closes_unverified(tmp_path):
    engine, response, executes, events = _run(
        tmp_path, [{"kind": "RESULT", "body": NEGATIVE_SEARCH, "result_ir": _ir()}], problem_class=VERIFIED)
    assert len(executes) == 1  # accepted on the first attempt: nothing to repair
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and _status(engine) == "CLOSED_UNVERIFIED"
    assert _unverified_reasons(events) == ["negative_claim_unchecked"]
    text, _ = split_published_ir(response.text)
    assert text.endswith(presentation.negative_claim_note())


def test_a_declared_negative_proof_closes_unverified(tmp_path):
    engine, _, _, events = _run(
        tmp_path, [{"kind": "RESULT", "body": "No solution exists: parity.", "result_ir": _ir(NEGATIVE_PROOF)}],
        problem_class=VERIFIED)
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED
    assert _unverified_reasons(events) == ["negative_claim_unchecked"]


def test_a_declared_incomplete_result_closes_unverified(tmp_path):
    reply = {"kind": "RESULT", "body": "print('partial search finished without a complete answer')",
             "result_ir": _incomplete_ir()}
    engine, _, _, events = _run(tmp_path, [reply], problem_class=VERIFIED)
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED
    assert _unverified_reasons(events) == ["declared_incomplete"]


def test_a_negative_claim_on_the_unconfirmed_route_closes_unverified(tmp_path):
    engine, _, events = _unconfirmed(tmp_path, [{"interpretation": "Decide whether a partition exists.",
                                                 "approach": "Enumerate the candidates.", "kind": "RESULT",
                                                 "body": NEGATIVE_SEARCH, "result_ir": _ir()}])
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and _status(engine) == "CLOSED_UNVERIFIED"
    assert _unverified_reasons(events) == ["negative_claim_unchecked"]


# A verified deliverable still succeeds.

def test_a_witness_computed_by_a_program_closes_success(tmp_path):
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": POSITIVE, "result_ir": _ir()}],
                                problem_class=VERIFIED)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS and _status(engine) == "CLOSED_SUCCESS"
    assert not _unverified_reasons(events)
    passed = [e["payload"] for e in events if e["kind"] == "VERIFICATION_PASSED"][-1]
    assert passed["sandbox_reproduced"] is True and passed["provisional"] is False


def test_a_witness_computed_on_the_unconfirmed_route_closes_success(tmp_path):
    engine, _, events = _unconfirmed(tmp_path, [COMPUTING])
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS and not _unverified_reasons(events)


def test_a_witness_its_program_writes_out_is_never_a_verified_success(tmp_path):
    """L113, L119: a witness the program writes out instead of computing is returned as a correction; repeated, it
    closes CLOSED_CANCELLED. A result established by an argument closes CLOSED_UNVERIFIED (test_l119_witness_forms)."""
    engine, _, executes, events = _run(tmp_path, [{"kind": "RESULT", "body": LITERAL, "result_ir": _ir()}] * 8,
                                       problem_class=VERIFIED)
    assert "WITNESS_LITERAL_IN_PROGRAM" in _kinds(events) and "[WITNESS_WRITTEN_IN_PROGRAM]" in executes[1].prompt
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED and not _unverified_reasons(events)


def test_a_task_without_verified_execution_closes_unverified_on_its_contract_checks(tmp_path):
    """L164: only a result the host reproduced closes CLOSED_SUCCESS; one checked against the contract alone is
    published and closes CLOSED_UNVERIFIED with the reason contract_checked."""
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": "42"}])
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and _unverified_reasons(events) == ["contract_checked"]


# The closure is terminal like the others, and it carries a published result.

def test_an_unverified_closure_is_terminal_and_keeps_its_result(tmp_path):
    engine, _, _, _ = _run(tmp_path, [{"kind": "RESULT", "body": NEGATIVE_SEARCH, "result_ir": _ir()}],
                           problem_class=VERIFIED)
    controller = engine.controller
    controller.cancel()  # a closed instance is not reopened
    assert controller.state.stage == Stage.CLOSED_UNVERIFIED and controller.state.current_result is not None
    restored = dict(controller.state.to_dict(), in_flight_action={"action_id": "a1", "description": "x"})
    assert ProtocolState.from_dict(restored).stage == Stage.CLOSED_UNVERIFIED  # not OUTCOME_UNCERTAIN
    assert controller.new_instance().state.stage == Stage.PROMPT_REQUIRED
    assert engine.workspace.previous_turn()["result"]  # a follow-up turn sees the published result
    assert any(t["status"] == "CLOSED_UNVERIFIED" for t in engine.workspace.closed_turns())


def test_headless_exit_code_for_an_unverified_closure_is_5(monkeypatch, capsys, tmp_path):
    from pdl_taskmaster.host import repl
    from test_repl_integration import FIXTURE, ROOT

    class MockHost:
        def status(self):
            return {"controller_state": {"stage": "CLOSED_UNVERIFIED"}}

    class MockRuntime:
        def __init__(self, session_dir):
            self.host = MockHost()
            self.session_dir = session_dir
            self.exit_on_close = True
            self.transcript = (session_dir / "transcript.txt").open("w", encoding="utf-8")

        def close(self):
            self.transcript.close()

    def eof(prompt="> "):
        raise EOFError()

    monkeypatch.setattr(repl, "open_session", lambda *args, **kwargs: MockRuntime(tmp_path))
    monkeypatch.setattr(repl, "_read_repl_input", eof)
    monkeypatch.setattr(repl, "_disable_bracketed_paste", lambda: None)
    monkeypatch.setattr(sys, "argv", ["pdlt", "--non-interactive", "--candidate-repo", str(ROOT),
                                      "--evidence", str(FIXTURE), "--worker", "recorded",
                                      "--session-id", "mock-unverified"])
    assert repl.main() == repl.EXIT_UNVERIFIED == run_catalogue.EXIT_UNVERIFIED == 5
    assert "could not verify" in capsys.readouterr().err


# Catalogue scoring: an unverified closure never counts as the CLOSED_SUCCESS a prompt expects.

def _result(verdict: str, expected: str, grade: str = "PASS") -> dict:
    return {"verdict": verdict, "expected_stage": expected, "ground_truth_grade": {"grade": grade}}


def test_catalogue_scores_an_unverified_closure_against_the_expected_stage():
    assert run_catalogue.outcome_class(_result("CLOSED_UNVERIFIED", "CLOSED_SUCCESS")) == "FAIL"
    assert run_catalogue.outcome_class(_result("CLOSED_SUCCESS", "CLOSED_SUCCESS")) == "PASS"
    assert run_catalogue.outcome_class(_result("CLOSED_UNVERIFIED", "CLOSED_UNVERIFIED")) == "PASS"
    assert run_catalogue.outcome_class(_result("CLOSED_SUCCESS", "CLOSED_UNVERIFIED")) == "PASS"
    assert run_catalogue.outcome_class(_result("CLOSED_CANCELLED", "CLOSED_UNVERIFIED")) == "FAIL"
    assert run_catalogue.outcome_class(_result("CLOSED_UNVERIFIED", "CLOSED_UNVERIFIED", "FAIL")) == "FAIL"


def test_the_manifest_expects_an_unverified_closure_where_the_answer_is_negative_or_contract_checked():
    """13-01, whose answer is a negative claim, and since L164 every prompt routed STANDARD_EXECUTION."""
    rows = [json.loads(line) for line in run_catalogue.MANIFEST_PATH.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]
    standard = {r["id"] for r in rows if r["expected_routing"] == "STANDARD_EXECUTION"
                and r["expected_stage"] != "WAITING_INPUT"}
    assert {r["id"] for r in rows if r["expected_stage"] == "CLOSED_UNVERIFIED"} == {"13-01"} | standard

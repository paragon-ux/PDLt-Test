"""L119 (ADR-0030): a positive result under verified execution is computed by a program, stated as a certificate a
program checks (the host gives it to every program as WITNESS_DATA), or established by an argument (published as
unverified). A program that writes out the data it prints is returned as a correction, so a result never has to be
hard-coded to be accepted. All offline; no model call."""
from __future__ import annotations

import json

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime import agent_tools, presentation
from pdl_taskmaster.runtime.result_ir import render_instructions
from pdl_taskmaster.runtime.witness_forms import CERTIFICATE_VARIABLE, with_certificate

from test_execution_phase import ROOT, _ir, _kinds, _run

VERIFIED = "VERIFIED_EXECUTION"
COLOURING = {"colours": {"0": 3, "1": 1, "2": 2, "3": 1, "4": 2}}
EDGES = "edges = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 3), (3, 4), (4, 1)]\n"
CHECKER = ("import json, sys\n" + EDGES +
           "colours = {int(k): v for k, v in WITNESS_DATA['colours'].items()}\n"
           "if any(colours[a] == colours[b] for a, b in edges):\n    sys.exit('adjacent nodes share a colour')\n"
           "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': WITNESS_DATA}))")
WRITTEN_OUT = ("import json\ncolours = {'0': 3, '1': 1, '2': 2, '3': 1, '4': 2}\n"
               "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'colours': colours}}))")


def _certificate(data=COLOURING) -> dict:
    return {"polarity": "positive", "basis": "certificate", "data": data}


def _reasons(events) -> list[str]:
    return [e["payload"]["reason"] for e in events if e["kind"] == "CLOSED_UNVERIFIED"]


def test_the_certificate_is_bound_to_witness_data_on_the_first_line():
    source = with_certificate("print(WITNESS_DATA['note'])", {"note": 'a "quoted" \\ value'})
    assert source.splitlines()[0].startswith(CERTIFICATE_VARIABLE + " = ")
    assert with_certificate("print(1)", None) == "print(1)"


def test_a_certificate_a_program_checks_closes_success(tmp_path):
    engine, _, executes, events = _run(
        tmp_path, [{"kind": "RESULT", "body": CHECKER, "result_ir": _ir(_certificate())}], problem_class=VERIFIED)
    assert len(executes) == 1 and engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert "WITNESS_LITERAL_IN_PROGRAM" not in _kinds(events) and not _reasons(events)
    passed = [e["payload"] for e in events if e["kind"] == "VERIFICATION_PASSED"][-1]
    assert passed["certificate_checked"] is True and passed["sandbox_reproduced"] is True


def test_a_certificate_that_fails_its_check_is_returned_with_the_program_failure(tmp_path):
    wrong = _certificate({"colours": {"0": 3, "1": 1, "2": 1, "3": 2, "4": 2}})  # nodes 1 and 2 share a colour
    engine, _, executes, events = _run(
        tmp_path, [{"kind": "RESULT", "body": CHECKER, "result_ir": _ir(wrong)},
                   {"kind": "RESULT", "body": CHECKER, "result_ir": _ir(_certificate())}], problem_class=VERIFIED)
    assert len(executes) == 2 and "[PROGRAM_FAILED]" in executes[1].prompt
    assert "adjacent nodes share a colour" in executes[1].prompt
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_a_certificate_no_program_prints_is_not_accepted(tmp_path):
    engine, _, executes, _ = _run(
        tmp_path, [{"kind": "RESULT", "body": "The colouring is in the Result IR.", "result_ir": _ir(_certificate())},
                   {"kind": "RESULT", "body": CHECKER, "result_ir": _ir(_certificate())}], problem_class=VERIFIED)
    assert "[WITNESS_NOT_PRINTED]" in executes[1].prompt and "WITNESS_DATA" in executes[1].prompt
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_a_result_established_by_an_argument_closes_unverified(tmp_path):
    argued = {"polarity": "positive", "basis": "proof", "data": {"probability": "7/12"},
              "argument": "Conway's leading numbers give odds 5:7 for the second pattern."}
    engine, response, executes, events = _run(
        tmp_path, [{"kind": "RESULT", "body": "By Conway's algorithm the probability is 7/12.",
                    "result_ir": _ir(argued)}], problem_class=VERIFIED)
    assert len(executes) == 1 and engine.controller.state.stage == Stage.CLOSED_UNVERIFIED
    assert _reasons(events) == ["argued_result"] and "POSITIVE_RESULT_ARGUED" in _kinds(events)
    assert presentation.argued_result_note() in response.text


def test_a_positive_proof_without_an_argument_is_not_accepted(tmp_path):
    bare = {"polarity": "positive", "basis": "proof", "data": {"probability": "7/12"}}
    engine, _, executes, _ = _run(
        tmp_path, [{"kind": "RESULT", "body": "The probability is 7/12.", "result_ir": _ir(bare)}] * 8,
        problem_class=VERIFIED)
    assert "[WITNESS_NOT_PRINTED]" in executes[1].prompt
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED


def test_a_written_out_witness_is_a_correction_and_a_certificate_then_succeeds(tmp_path):
    engine, _, executes, events = _run(
        tmp_path, [{"kind": "RESULT", "body": WRITTEN_OUT, "result_ir": _ir()},
                   {"kind": "RESULT", "body": CHECKER, "result_ir": _ir(_certificate())}], problem_class=VERIFIED)
    assert "WITNESS_LITERAL_IN_PROGRAM" in _kinds(events)
    assert len(executes) == 2 and "[WITNESS_WRITTEN_IN_PROGRAM]" in executes[1].prompt
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS and not _reasons(events)


def test_the_instructions_name_the_three_positive_forms():
    text = render_instructions(["R1"], repo_root=ROOT, evidence_paths=["execution://body", "execution://witness"],
                               requires_verified_execution=True)
    assert '"basis" "certificate"' in text and "WITNESS_DATA" in text and '"basis" "proof"' in text
    assert "writes out itself" in text


def test_the_in_call_check_accepts_an_argued_result_and_gives_programs_the_certificate():
    class Bridge:
        def parse_unconfirmed_execution(self, text):
            from types import SimpleNamespace
            data = json.loads(text)
            return SimpleNamespace(kind=data["kind"], body=data["body"], result_ir=data.get("result_ir"))

    from pdl_taskmaster.runtime.session_engine import _parse_sandbox_witness, _python_blocks, _witness_written_in_program
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

    validate = agent_tools.make_validator(Bridge(), ExecutionSandbox(label="l119"), EXECUTION_BUDGETS["STANDARD"],
                                          True, _python_blocks, _parse_sandbox_witness, _witness_written_in_program)
    argued = {"polarity": "positive", "basis": "proof", "data": {"n": 19}, "argument": "m + n = 7 + 12."}
    errors, _ = validate({"kind": "RESULT", "body": "The answer is 19.", "result_ir": {"witness": argued}})
    assert errors == []
    errors, facts = validate({"kind": "RESULT", "body": CHECKER, "result_ir": {"witness": _certificate()}})
    assert errors == [] and "printed a WITNESS line True" in facts[0]

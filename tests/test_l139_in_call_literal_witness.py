"""L139: the in-call submission check (agent_tools.make_validator) applies the host's rule for a witness the program
writes out itself (L113, L119), so a submission the host would flag after the call is returned during it, with the
same error. One rule: the host's ``_witness_written_in_program``, applied as the host applies it, to the last block
that printed a witness. Also the argued-result fact (ADR-0030). Offline; no model call."""
from __future__ import annotations

import json

import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime.agent_tools import SUBMIT

from test_agent_tools import _engine, _validator, outcome
from test_execution_phase import _ir, _kinds, _run


def _line(data: str) -> str:
    return "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': " + data + "}))\n"


LITERAL = _line("{'answer': 19}")
NAMES = ("import json\nanswer = 19\nwitness = {'polarity': 'positive', 'data': {'answer': answer}}\n"
         "print('WITNESS: ' + json.dumps(witness))\n")
STRING_LINE = "print('WITNESS: {\"polarity\": \"positive\", \"data\": {\"answer\": 19}}')\n"
# The shape of run 01-03 r3 of L132 (run-20261017-214832-unconfirmed-agent-tools-tier-d1): a table of values and
# an argument written out, then printed as the witness; accepted in the call, flagged by the host after it.
TABLE = ("import json\nassignment = {\n    0: 4,\n    1: 1,\n    2: 2,\n    3: 3,\n    4: 1,\n    5: 2,\n}\n"
         "argument = 'Each value differs from those it is compared with.'\n"
         "witness = {'polarity': 'positive', 'data': {'assignment': assignment, 'argument': argument}}\n"
         "print('WITNESS: ' + json.dumps(witness))\n")
COMPUTED = _line("{'answer': sum([7, 12])}")
SELECTED = "import json\nvalues = [12, 5, 23, 35, 7, 40]\n" + _line("{'largest': max(values)}").split("\n", 1)[1]
CHANGED = ("import json\nfound = []\nfor v in [3, 4, 9]:\n    if v % 3 == 0:\n        found.append(v)\n"
           + _line("{'found': found}").split("\n", 1)[1])


def _blocks(*programs: str) -> str:
    return "The result.\n\n" + "\n".join(f"```python\n{p}```\n" for p in programs)


CASES = {  # name: (body, flagged)
    "literal": (LITERAL, True),
    "names bound once": (NAMES, True),
    "a witness line written out": (STRING_LINE, True),
    "a table and an argument written out (01-03 r3)": (TABLE, True),
    "computed": (COMPUTED, False),
    "selected from input data": (SELECTED, False),
    "built by the program": (CHANGED, False),
    "written out, then computed: the last witness counts": (_blocks(LITERAL, COMPUTED), False),
    "computed, then written out": (_blocks(COMPUTED, LITERAL), True),
}


def _codes(errors):
    return [e["code"] for e in errors]


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_in_call_check_flags_a_witness_the_program_writes_out(name):
    body, flagged = CASES[name]
    errors, facts = _validator()(outcome(body))
    assert ("WITNESS_WRITTEN_IN_PROGRAM" in _codes(errors)) is flagged, (errors, facts)
    if flagged:
        (error,) = errors
        assert error["path"].startswith("outcome.body block ")
        assert "writes out itself" in error["problem"] and "Compute the result in the program" in error["expected"]
    else:
        assert errors == []


@pytest.mark.parametrize("name", sorted(CASES))
def test_the_in_call_check_and_the_host_agree(name, tmp_path):
    """The same outcome: rejected in the call exactly when the host flags it after the call."""
    body, _ = CASES[name]
    in_call = "WITNESS_WRITTEN_IN_PROGRAM" in _codes(_validator()(outcome(body))[0])
    reply = {"kind": "RESULT", "body": body, "result_ir": _ir()}
    _, _, _, events = _run(tmp_path, [reply] * 4, problem_class="VERIFIED_EXECUTION")
    assert ("WITNESS_LITERAL_IN_PROGRAM" in _kinds(events)) is in_call


def test_without_a_required_witness_the_rule_does_not_apply():
    # As on the host, which checks witnesses only where one is required.
    errors, facts = _validator(witness_required=False)(outcome(LITERAL))
    assert errors == [] and len(facts) == 1 and facts[0].endswith("printed a WITNESS line True")


def test_an_argued_result_is_accepted_with_the_fact_that_it_is_published_unverified():
    argued = {"polarity": "positive", "basis": "proof", "data": {"n": 19}, "argument": "m + n = 7 + 12."}
    errors, facts = _validator()({**outcome("The answer is 19."), "result_ir": {**_ir(), "witness": argued}})
    assert errors == []
    assert facts == ["the result_ir witness rests on its argument (basis proof) and no program printed a WITNESS "
                     "line: the host cannot check an argument, so it publishes the result as unverified "
                     "(exit status 5)"]
    errors, facts = _validator()({**outcome(COMPUTED), "result_ir": {**_ir(), "witness": argued}})
    assert errors == [] and not any("argument" in f for f in facts)  # a program printed the witness


def test_a_session_gets_the_rejection_in_the_call_and_closes_on_a_computed_resubmission(tmp_path):
    def execute(req):
        envelope, accepted = req.tools.submit(json.dumps({"outcome": outcome(TABLE)}))
        assert accepted is None and _codes(envelope["errors"]) == ["WITNESS_WRITTEN_IN_PROGRAM"]
        envelope, accepted = req.tools.submit(json.dumps({"outcome": outcome(COMPUTED)}))
        assert envelope["ok"] is True
        return json.dumps(accepted)

    engine, response, _, events = _engine(tmp_path, execute, agent_tools_on=True)
    assert response.closed and engine.controller.state.stage == Stage.CLOSED_SUCCESS
    submissions = [e["payload"].get("accepted") for e in events
                   if e["kind"] == "AGENT_TOOL_CALL" and e["payload"]["tool"] == SUBMIT]
    assert submissions == [False, True]
    assert "WITNESS_LITERAL_IN_PROGRAM" not in _kinds(events) and "VERIFICATION_PASSED" in _kinds(events)

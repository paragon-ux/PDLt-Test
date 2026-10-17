"""L104: under VERIFIED_EXECUTION a claimed result is certified only by a WITNESS line printed by a
program the host runs. A positive witness written only into the Result IR used to close the turn
CLOSED_SUCCESS (exit 0) as a provisional pass; it is now WITNESS_NOT_PRINTED, as an undeclared witness
always was. A reply that is only literal data is not run as a program. All offline; no model call."""
from __future__ import annotations

import json
from pathlib import Path

from pdl_taskmaster.runtime.session_engine import SessionEngine, _python_blocks
from pdl_taskmaster.controller.mechanical_controller import Stage

from test_execution_phase import ClassifyingSys1

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Partition the given list of integers into disjoint triples (a, b, c) with a + b = c."

# The recorded reply of run-20261009-175714 01-01 r1 (EXECUTE_UNCONFIRMED, VERIFIED_EXECUTION): the body
# is a bare list display and the declared witness carries the same triples (35 appears twice). The host
# logged VERIFICATION_PASSED (provisional) and closed CLOSED_SUCCESS; the grader failed it.
_TRIPLES = [[12, 23, 35], [13, 22, 35], [15, 26, 41], [32, 40, 72], [44, 45, 89], [44, 56, 100], [40, 45, 85],
            [58, 71, 129], [54, 61, 115], [63, 76, 139], [71, 92, 163], [84, 102, 186], [83, 100, 183],
            [90, 105, 195], [113, 117, 230]]
RECORDED = {
    "interpretation": "Find a set of 15 triples (a,b,c) from list L such that each element is used exactly once "
                      "and a+b=c for each triple.",
    "approach": "Use Python to enumerate all possible pairs (a,b) where a+b is also in L. Build a graph of valid "
                "triples and solve exact cover via recursive backtracking to select 15 disjoint triples covering "
                "all 45 numbers.",
    "kind": "RESULT",
    "body": "[" + ", ".join(f"({a}, {b}, {c})" for a, b, c in _TRIPLES) + "]",
    "result_ir": {"files": [], "reconciliation": [], "open_defects": [],
                  "witness": {"polarity": "positive", "data": {"triples": _TRIPLES}, "basis": None,
                              "search_exhausted": None, "nodes_explored": None, "method": None,
                              "argument": None, "domain": None}},
}
COMPUTING = {
    "interpretation": "Find triples (a, b, c) with a + b = c.",
    "approach": "Enumerate pairs and print the triples found as a witness.",
    "kind": "RESULT",
    "body": ("import json\n"
             "triples = [[a, b, a + b] for a in range(1, 3) for b in range(a + 1, 4)]\n"
             "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'triples': triples}}))"),
    "result_ir": {"files": [], "reconciliation": [], "open_defects": []},
}


def _unconfirmed(tmp_path, replies: list[dict]):
    executes: list = []

    def worker(request):
        if request.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Partition the list into triples.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        executes.append(request)
        return json.dumps(replies[min(len(executes), len(replies)) - 1])

    engine = SessionEngine(ROOT, worker, workspace_root=tmp_path, sys1_client=ClassifyingSys1("VERIFIED_EXECUTION"),
                           no_review=True)
    engine.handle_user_message(REQUEST)
    return engine, executes, engine.workspace.read_events()


def test_recorded_declared_witness_without_a_program_is_not_a_certified_result(tmp_path):
    engine, executes, events = _unconfirmed(tmp_path, [RECORDED])
    kinds = [e["kind"] for e in events]
    assert "VERIFICATION_PASSED" not in kinds and engine.controller.state.stage == Stage.CLOSED_CANCELLED
    assert len(executes) >= 2
    for repair in executes[1:]:
        assert "WITNESS_NOT_PRINTED" in repair.prompt
        assert "The witness in the Result IR was not printed by a program the host ran." in repair.prompt
    # (B) the body is a literal list: data, not a program, so nothing ran in the sandbox
    assert "SANDBOX_RUN" not in kinds


def test_a_program_printing_the_witness_after_the_repair_is_accepted(tmp_path):
    engine, executes, events = _unconfirmed(tmp_path, [RECORDED, COMPUTING])
    assert len(executes) == 2 and engine.controller.state.stage == Stage.CLOSED_SUCCESS
    passed = next(e for e in events if e["kind"] == "VERIFICATION_PASSED")["payload"]
    assert passed["sandbox_reproduced"] is True and passed["provisional"] is False


def test_a_reply_of_literal_data_is_not_a_program():
    for data in ("[(12, 23, 35), (13, 22, 35)]", "{'a': [1, 2], 'b': (3, 4)}", "42", "-1.5", '"text"',
                 "[1, 2]\n(3, 4)\n"):
        assert _python_blocks(data) == [], data
    for program in ("print([1, 2])", "x = [1, 2]", "[1, 2] + [3]", "[i for i in range(3)]", "import json\n[1]"):
        assert _python_blocks(program) == [program], program
    fenced = "The triples:\n\n```python\nprint(1)\n```\n"
    assert _python_blocks(fenced) == ["print(1)\n"]

"""L113: a witness is flagged as written into the program only when the program writes its data out (literals and
names bound once to them), not when every value merely occurs in the program. A program that selects its answer
from input data it contains computes the answer and closes CLOSED_SUCCESS; one that writes the answer out closes
CLOSED_UNVERIFIED (L116). All offline; no model call."""
from __future__ import annotations

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime.session_engine import _witness_written_in_program

from test_execution_phase import _ir, _kinds, _run

INPUT = "values = [12, 5, 23, 35, 7, 40]\n"


def written(data, source) -> bool:
    return _witness_written_in_program({"polarity": "positive", "data": data}, source)


# A selection from the program's input data is computed, though every value is a constant of the program.

def test_a_selection_from_input_data_is_computed():
    pairs = {"pair": [12, 23, 35]}
    assert not written(pairs, INPUT + "print({'pair': [a for a in values if a in (12, 23, 35)]})")
    assert not written({"largest": 40}, INPUT + "print({'largest': max(values)})")
    loop = INPUT + "best = None\nfor v in values:\n    if best is None or v > best:\n        best = v\nprint({'largest': best})"
    assert not written({"largest": 40}, loop)
    search = (INPUT + "found = []\n"
              "def search(i, chosen):\n"
              "    if sum(chosen) == 70:\n        found.append(list(chosen))\n        return True\n"
              "    return i < len(values) and (search(i + 1, chosen + [values[i]]) or search(i + 1, chosen))\n"
              "search(0, [])\nprint({'pair': found[0]})")
    assert not written({"pair": [12, 23, 35]}, search)


def test_a_value_the_program_changes_or_rebinds_is_computed():
    assert not written({"items": [3, 4]}, "items = []\nitems.append(3)\nitems.append(4)\nprint({'items': items})")
    assert not written({"answer": 4}, "answer = 3\nanswer = 4\nprint({'answer': answer})")
    assert not written({"answer": 4}, "answer = 3\nanswer += 1\nprint({'answer': answer})")


# An answer written out is flagged, however it reaches the print.

def test_an_answer_written_out_through_names_is_flagged():
    source = ("import json\ndef compute():\n    result = 3\n    witness = {'polarity': 'positive', 'data': {'answer': result}}\n"
              "    print('WITNESS:', json.dumps(witness))\ncompute()\n")
    assert written({"answer": 3}, source)
    assert written({"pair": [12, 23, 35]}, INPUT + "answer = [12, 23, 35]\nprint({'pair': answer})")


def test_an_answer_written_out_and_then_checked_is_flagged():
    source = ("grid = [[1, 2], [2, 1]]\n"
              "assert all(sorted(row) == [1, 2] for row in grid)\n"
              "print({'grid': grid})")
    assert written({"grid": [[1, 2], [2, 1]]}, source)


def test_written_out_data_compares_as_json():
    source = "colors = {0: 3, 1: 1, 10: 2}\nprint({'colors': colors, 'cells': (1, 2)})"
    assert written({"colors": {"0": 3, "1": 1, "10": 2}, "cells": [1, 2]}, source)


def test_an_f_string_witness_line_of_written_out_values_is_flagged():
    source = "n = 19\nprint(f'WITNESS: {{\"answer\": {n}}}')"
    assert _witness_written_in_program(
        {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"answer": 19}}, source)
    assert not _witness_written_in_program(
        {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"answer": 19}},
        "n = sum([7, 12])\nprint(f'WITNESS: {{\"answer\": {n}}}')")


# The closure follows the flag.

def test_a_selection_from_input_data_closes_success(tmp_path):
    body = ("import json\n" + INPUT +
            "chosen = [v for v in values if v % 5 == 0]\n"
            "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'chosen': chosen}}))")
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": body, "result_ir": _ir()}],
                                problem_class="VERIFIED_EXECUTION")
    assert "WITNESS_LITERAL_IN_PROGRAM" not in _kinds(events)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    passed = [e["payload"] for e in events if e["kind"] == "VERIFICATION_PASSED"][-1]
    assert passed["sandbox_reproduced"] is True and passed["provisional"] is False


def test_an_answer_written_out_closes_unverified(tmp_path):
    body = ("import json\ndef compute():\n    result = 3\n"
            "    print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'answer': result}}))\ncompute()\n")
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": body, "result_ir": _ir()}],
                                problem_class="VERIFIED_EXECUTION")
    assert "WITNESS_LITERAL_IN_PROGRAM" in _kinds(events)
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED
    assert [e["payload"]["reason"] for e in events if e["kind"] == "CLOSED_UNVERIFIED"] == [
        "witness_written_in_program"]

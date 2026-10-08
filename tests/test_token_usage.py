"""Token accounting in run_catalogue: every call of an observation record counts, and the control's
one call (logged as an event, not an observation record) is counted too."""
from __future__ import annotations

import json
from pathlib import Path

import run_catalogue


def _usage(inp: int, out: int, reasoning: int = 0) -> dict:
    return {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out, "reasoning_tokens": reasoning}


def _write_lines(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")


def test_every_call_of_a_record_is_counted(tmp_path: Path) -> None:
    # One REPL turn of an unconfirmed route: two calls in one record.
    record = {"calls": [
        {"operation": "BOOTSTRAP_ANALYSIS", "usage": _usage(2800, 800)},
        {"operation": "EXECUTE_UNCONFIRMED", "usage": _usage(4100, 970, 12)},
    ]}
    _write_lines(tmp_path / "session" / "observations" / "repl-session.jsonl", [record, record])
    totals = run_catalogue.token_usage(tmp_path)
    assert totals["output_tokens"] == {"BOOTSTRAP_ANALYSIS": 1600, "EXECUTE_UNCONFIRMED": 1940}
    assert totals["input_tokens"] == {"BOOTSTRAP_ANALYSIS": 5600, "EXECUTE_UNCONFIRMED": 8200}
    assert totals["reasoning_tokens"]["EXECUTE_UNCONFIRMED"] == 24


def test_an_older_record_shape_still_reads_its_one_call(tmp_path: Path) -> None:
    record = {"turn": {"operation": "EXECUTE", "usage": _usage(10, 20, 5)}}
    _write_lines(tmp_path / "observations" / "old.jsonl", [record])
    assert run_catalogue.token_usage(tmp_path)["output_tokens"] == {"EXECUTE": 20}


def test_the_control_event_supplies_the_tokens_when_there_is_no_observation_record(tmp_path: Path) -> None:
    event = {"kind": "MODEL_OUTPUT_RECORDED", "payload": {
        "operation": "CONTROL_EXECUTE", "input_tokens": 279, "output_tokens": 3880, "reasoning_tokens": 2729}}
    _write_lines(tmp_path / "session" / "turns" / "turn_001" / "events.jsonl", [event])
    totals = run_catalogue.token_usage(tmp_path)
    assert totals == {"reasoning_tokens": {"CONTROL_EXECUTE": 2729}, "output_tokens": {"CONTROL_EXECUTE": 3880},
                      "input_tokens": {"CONTROL_EXECUTE": 279}}


def test_a_harness_event_is_never_counted_twice(tmp_path: Path) -> None:
    # The fallback is for the control only: a harness run's tokens come from its observation records.
    _write_lines(tmp_path / "observations" / "repl-session.jsonl",
                 [{"calls": [{"operation": "EXECUTE", "usage": _usage(1, 2)}]}])
    _write_lines(tmp_path / "events.jsonl", [{"kind": "MODEL_OUTPUT_RECORDED", "payload": {
        "operation": "CONTROL_EXECUTE", "output_tokens": 999}}])
    assert run_catalogue.token_usage(tmp_path)["output_tokens"] == {"EXECUTE": 2}


def test_the_execute_calls_of_every_route_are_counted_as_execute() -> None:
    for operation in ("EXECUTE", "EXECUTE_UNCONFIRMED", "CONTROL_EXECUTE"):
        assert run_catalogue.is_execute_operation(operation)
    for operation in ("BOOTSTRAP_ANALYSIS", "DRAFT_EXECUTE", "DRAFT_PROMPT", "DRAFT_PLAN"):
        assert not run_catalogue.is_execute_operation(operation)

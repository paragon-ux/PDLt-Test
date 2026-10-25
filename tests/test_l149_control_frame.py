"""L149: the Control client can add one element of the protocol's frame at a time (a measurement, the user,
2026-10-22): worker (the stateless-worker instructions), wrap (the request inside a JSON projection document), json
(JSON-mode output, the answer in a body field). Without the option Control sends the plain request as before. Offline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_catalogue
from pdl_taskmaster.host import control_cli
from pdl_taskmaster.host.control_cli import deliverable, frame_parts, framed_request

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "How many sisters does each brother have?"
WORKER = (ROOT / "src" / "pdl_taskmaster" / "runtime" / "worker-bootstrap.txt").read_text(encoding="utf-8")


def test_without_a_frame_control_sends_the_plain_request():
    assert framed_request(REQUEST, frozenset(), WORKER) == {"input": REQUEST}


def test_worker_adds_only_the_protocol_s_instructions():
    fields = framed_request(REQUEST, frozenset({"worker"}), WORKER)
    assert fields == {"input": REQUEST, "instructions": WORKER.rstrip()}


def test_wrap_carries_the_request_inside_the_projection_document():
    document = json.loads(framed_request(REQUEST, frozenset({"wrap"}), WORKER)["input"])
    assert document["operation"] == "EXECUTE_UNCONFIRMED" and "output_schema" not in document
    assert document["operation_inputs"]["SOURCE_REQUEST"] == REQUEST


def test_json_asks_for_a_body_field_in_json_mode():
    fields = framed_request(REQUEST, frozenset({"json"}), WORKER)
    assert fields["text"] == {"format": {"type": "json_object"}} and fields["input"].startswith(REQUEST)
    assert '"body"' in fields["input"] and fields["input"].endswith(control_cli._JSON_ONLY)
    wrapped = framed_request(REQUEST, frozenset({"wrap", "json"}), WORKER)["input"]
    document = json.loads(wrapped[: -len("\n\n" + control_cli._JSON_ONLY)])
    assert document["output_schema"]["required"] == ["body"]


def test_the_graded_deliverable_is_the_body_under_json():
    assert deliverable('{"body": "S + 1"}', frozenset({"json"})) == "S + 1"
    assert deliverable("not json", frozenset({"json"})) == "not json"
    assert deliverable('{"body": "S + 1"}', frozenset()) == '{"body": "S + 1"}'


def test_unknown_parts_are_refused_and_the_runner_passes_parts_to_control_only(tmp_path: Path):
    with pytest.raises(SystemExit):
        frame_parts("worker,xml")
    assert frame_parts("worker, json") == {"worker", "json"}

    def cmd(**settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m",
                                                   "low", run_settings=settings)
    control = cmd(route="control", control_frame=["worker", "wrap"])
    assert control[control.index("--frame") + 1] == "worker,wrap"
    assert "--frame" not in cmd(route="unconfirmed", control_frame=["worker"])

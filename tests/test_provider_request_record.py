"""Every model call's full request is recorded, instructions included
(TARGET_ARCHITECTURE I-9; GOAL T0.5).

The real harness runs a confirmed task against the local stub server
(test_reasoning_wire._run_stub); the server's captured bodies are compared with the
files the run recorded."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import test_reasoning_wire as wire

REQUEST_DIR = "provider-requests"  # the directory beside call-trace.jsonl


def _recorded(tmp_path: Path) -> tuple[list[dict], list[dict]]:
    traces = [json.loads(line) for path in sorted(tmp_path.rglob("call-trace.jsonl"))
              for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    attempts = [(t, a) for t in traces for a in t["attempts"] if not t["operation"].startswith("SYSTEM1:")]
    return traces, [{"operation": t["operation"], **a} for t, a in attempts]


def test_each_operation_records_the_exact_request_it_sent(tmp_path: Path) -> None:
    ops, bodies = wire._run_stub(tmp_path, {})
    assert ops[:4] == ["BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN", "EXECUTE"]
    _, attempts = _recorded(tmp_path)
    assert len(attempts) == len(bodies)
    for attempt, sent in zip(attempts, bodies):
        stored = (next(tmp_path.rglob(attempt["request_file"].split("/")[-1]))).read_bytes()
        assert json.loads(stored) == sent  # byte content equals what the server received
        assert attempt["request_sha256"] == hashlib.sha256(stored).hexdigest()
        assert attempt["request_file"].startswith(REQUEST_DIR + "/")


def test_the_recorded_request_includes_the_instructions_field(tmp_path: Path) -> None:
    _, bodies = wire._run_stub(tmp_path, {})
    _, attempts = _recorded(tmp_path)
    by_operation = {}
    for attempt in attempts:
        stored = json.loads(next(tmp_path.rglob(attempt["request_file"].split("/")[-1])).read_bytes())
        by_operation.setdefault(attempt["operation"], stored)
    for operation in ("DRAFT_PROMPT", "DRAFT_PLAN", "EXECUTE"):
        assert "NORMATIVE GUIDELINES" in by_operation[operation]["instructions"], operation
    assert all("Authorization" not in json.dumps(b) and "stub" != b.get("api_key") for b in by_operation.values())

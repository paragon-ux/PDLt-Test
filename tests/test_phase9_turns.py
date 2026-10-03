"""Phase 9 (v2.4.0) tests: S3 turn-directory hierarchy and S4 deliverable chaining.

S3: WorkspaceRun supports an optional turn-scoped layout
(turns/<turn_id>/{state,events,stages}) while the legacy flat layout remains
byte-identical for single-turn runners and recorded fixtures.

S4: the prior turn's confirmed deliverable is the only artifact that crosses
the turn boundary; drafts, rejected plans, and review dialogue are
structurally unreachable in the new turn.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pdl_taskmaster.runtime.workspace import WorkspaceError, WorkspaceRun  # noqa: E402


def test_legacy_flat_layout_unchanged(tmp_path: Path) -> None:
    """Backwards compatibility: no turn_id -> exactly the pre-Phase-9 layout."""
    ws = WorkspaceRun.create(ROOT, tmp_path)
    assert (ws.path / "state").is_dir()
    assert (ws.path / "events").is_dir()
    assert (ws.path / "stages").is_dir()
    assert (ws.path / "shared").is_dir()
    assert not (ws.path / "turns").exists()
    assert ws.turn_id is None
    # controller state + invocation counter stay at the workspace root
    assert ws.controller_state_path == ws.path / "state" / "controller-state.json"
    inv = ws.materialize_operation("BOOTSTRAP_ANALYSIS", {"HOST_PROTOCOL_STATE": "X", "RAW_UNTRUSTED_CONTENT": "y"})
    assert str(inv.input_dir).startswith(str(ws.path / "stages"))
    # bind_protocol rebinding stays forbidden in flat mode
    ws.bind_protocol("instance-1")
    with pytest.raises(WorkspaceError):
        ws.bind_protocol("instance-2")


def test_turn_hierarchy_scaffold_and_routing(tmp_path: Path) -> None:
    """S3: turn-scoped state/events/stages under turns/<turn_id>/."""
    ws = WorkspaceRun.create(ROOT, tmp_path, turn_id="turn_001")
    assert ws.turn_id == "turn_001"
    # session-level dirs at root; stage tree scoped to the turn
    assert (ws.path / "shared").is_dir()
    assert (ws.path / "turns" / "turn_001" / "state").is_dir()
    assert (ws.path / "turns" / "turn_001" / "events").is_dir()
    assert (ws.path / "turns" / "turn_001" / "stages").is_dir()
    assert not (ws.path / "stages").exists()
    turn_meta = ws.read_turn_status("turn_001")
    assert turn_meta["status"] == "ACTIVE"

    # stage materialization and controller state route through the turn scope
    assert ws.controller_state_path == ws.path / "turns" / "turn_001" / "state" / "controller-state.json"
    inv = ws.materialize_operation("BOOTSTRAP_ANALYSIS", {"HOST_PROTOCOL_STATE": "X", "RAW_UNTRUSTED_CONTENT": "y"})
    assert str(inv.input_dir).startswith(str(ws.path / "turns" / "turn_001" / "stages"))
    # events are turn-scoped
    assert (ws.path / "turns" / "turn_001" / "events" / "events.jsonl").is_file()


def test_start_turn_moves_pointer_and_preserves_history(tmp_path: Path) -> None:
    ws = WorkspaceRun.create(ROOT, tmp_path, turn_id="turn_001")
    ws.publish_execution_outcome("RESULT", "first deliverable body")
    first_events = ws.path / "turns" / "turn_001" / "events" / "events.jsonl"
    before = first_events.read_text(encoding="utf-8")

    ws.start_turn("turn_002")
    assert ws.turn_id == "turn_002"
    assert (ws.path / "turns" / "turn_002" / "stages").is_dir()
    assert not (ws.path / "turns" / "turn_002" / "stages" / "50_execution").exists()
    # prior turn state preserved verbatim
    assert first_events.read_text(encoding="utf-8") == before
    with pytest.raises(WorkspaceError):
        ws.start_turn("turn_002")  # pointer unchanged
    assert ws.next_turn_id() == "turn_003"


def test_previous_deliverable_returns_only_confirmed_success_turn(tmp_path: Path) -> None:
    """S4: the prior deliverable is the ONLY thing reachable across turns."""
    ws = WorkspaceRun.create(ROOT, tmp_path, turn_id="turn_001")
    assert ws.previous_deliverable() is None  # nothing closed yet
    ws.publish_execution_outcome("RESULT", "confirmed deliverable one")
    ws.mark_turn_status("CLOSED_SUCCESS", deliverable_sha256="abc123")

    ws.start_turn("turn_002")
    assert ws.previous_deliverable() == "confirmed deliverable one"

    # drafts from the *current* turn are unreachable as previous deliverables
    ws.publish_execution_outcome("RESULT", "turn two draft")
    assert ws.previous_deliverable() == "confirmed deliverable one"

    # a cancelled prior turn never becomes a previous deliverable
    ws.mark_turn_status("CLOSED_CANCELLED")
    ws.start_turn("turn_003")
    assert ws.previous_deliverable() == "confirmed deliverable one"


def test_per_turn_protocol_binding(tmp_path: Path) -> None:
    """Each turn runs its own protocol lifecycle; rebinding across turns is expected."""
    ws = WorkspaceRun.create(ROOT, tmp_path, turn_id="turn_001")
    ws.bind_protocol("instance-one")
    assert ws.read_turn_status("turn_001")["protocol_instance_id"] == "instance-one"
    ws.start_turn("turn_002")
    ws.bind_protocol("instance-two")  # must not raise in hierarchy mode
    assert ws.read_turn_status("turn_002")["protocol_instance_id"] == "instance-two"


def test_engine_chaining_compiles_previous_deliverable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """S4 engine path: after a CLOSED_SUCCESS turn, a new message chains into
    the next turn with the prior deliverable compiled as background context."""
    from pdl_taskmaster.host.app import PDLtHost
    from pdl_taskmaster.providers.live_stub import LiveStubWorker
    from pdl_taskmaster.runtime.operation_bridge import ModelRequest

    captured: list[dict] = []

    class CapturingStub(LiveStubWorker):
        def call(self, request: ModelRequest):
            if request.operation == "BOOTSTRAP_ANALYSIS":
                captured.append(request.prompt)
            return super().call(request)

    host = PDLtHost(
        ROOT,
        worker=CapturingStub(),
        workspace_root=tmp_path / "workspaces",
        run_id="phase9-chain",
        render_compact=True,
    ).start()
    try:
        first = host.handle("Draft a short apology note about a broken heater.")
        assert not first.closed
        # drive through the gates with stub confirmations
        steps = 0
        while not first.closed and steps < 8:
            steps += 1
            st = (host.status().get("controller_state") or {}).get("stage")
            if st in {"PROMPT_REVIEW", "PLAN_REVIEW"}:
                first = host.handle("Confirm.")
            elif st == "WAITING_INPUT":
                first = host.handle("Proceed with execution.")
            elif st in {"CLOSED_SUCCESS", "CLOSED_CANCELLED"}:
                break
            else:
                first = host.handle("Confirm.")
        assert first.closed, "first turn did not close"

        captured.clear()
        second = host.handle("Now draft a thank-you note for the same landlord.")
        assert not second.bypass
        ws_path = Path(host.status()["workspace_path"])
        ws = WorkspaceRun.open(ROOT, ws_path)
        assert ws.turn_id == "turn_002"
        assert ws.previous_deliverable() is not None
        # the chained bootstrap projection carries the prior deliverable
        assert captured, "no bootstrap call captured in turn 2"
        assert "PREVIOUS_DELIVERABLE" in captured[0]
    finally:
        host.close()


def _two_turn_session(tmp_path, first_execute_replies, follow_up):
    """Turn 1 on a verified task, then a follow-up turn; records every call."""
    import json as _json

    from pdl_taskmaster.runtime.session_engine import SessionEngine

    calls, sys1_requests = [], []
    executes = iter(first_execute_replies + [{"kind": "RESULT", "body": "5"}] * 4)

    class Verified:
        is_configured, model = True, "fake"

        def call(self, request):
            sys1_requests.append(request)
            name = next(iter(request.questions))
            choice = {"route": "APPLY_PROTOCOL", "problem_class": "VERIFIED_EXECUTION"}.get(name, "WITHIN_10M_STEPS")
            return {"answers": {name: {"choice": choice, "confidence": 0.97, "probabilities": {choice: 0.97}}}}, 1.0

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _json.dumps({"kind": "ANALYSIS", "task_summary": "The user asks for a computed result.",
                                "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return _json.dumps({"kind": "PROMPT", "prompt_body": "PARTITION the list into triples", "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return _json.dumps({"neutral_plan_body": "SEARCH for the triples\nRETURN them"})
        return _json.dumps(next(executes))

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Verified())
    for message in ("$confirm-with-pseudocode partition the list L = {1, 2, 3}", "/confirm", "/confirm"):
        engine.handle_user_message(message)
    first_status = engine.controller.state.stage.value
    first_calls, first_sys1 = len(calls), len(sys1_requests)
    for message in ("$confirm-with-pseudocode " + follow_up, "/confirm", "/confirm"):  # as the host sends it
        engine.handle_user_message(message)
    return engine, first_status, calls[first_calls:], sys1_requests[first_sys1:]


def test_follow_up_after_a_cancelled_turn_works_from_the_previous_request(tmp_path: Path) -> None:
    """Sessions 082239 / 122654: a follow-up after a cancelled turn had no task, was
    routed from the follow-up text alone, and executed without the data."""
    failing = [{"kind": "RESULT", "body": "import sys\nsys.exit(1)"}] * 3
    engine, first, calls, sys1 = _two_turn_session(tmp_path, failing, "retry with a more efficient solution")
    assert first == "CLOSED_CANCELLED"
    bootstrap = next(c for c in calls if c.operation == "BOOTSTRAP_ANALYSIS")
    assert "partition the list L = {1, 2, 3}" in bootstrap.prompt and "retry with a more efficient" in bootstrap.prompt
    routed = [r.state.get("request", "") for r in sys1 if "problem_class" in r.questions]
    assert routed and "partition the list L = {1, 2, 3}" in routed[0]  # routing sees the task, not only the follow-up
    execute = next(c for c in calls if c.operation == "EXECUTE")
    assert "L = {1, 2, 3}" in execute.prompt  # the data reaches execution
    assert "not evidence and not a justification" in execute.prompt
    assert "sys.exit(1)" not in execute.prompt  # the failed candidate is never carried
    assert "UNVERIFIED ANSWER" not in execute.prompt


def test_follow_up_after_a_successful_turn_gets_its_result_as_reference_only(tmp_path: Path) -> None:
    witness = {"files": [], "reconciliation": [], "open_defects": [],
               "witness": {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"answer": 6}}}
    ok = [{"kind": "RESULT", "body": "The sum is 6.", "result_ir": witness}]
    engine, first, calls, _ = _two_turn_session(tmp_path, ok, "now double it")
    assert first == "CLOSED_SUCCESS"
    execute = next(c for c in calls if c.operation == "EXECUTE")
    assert "The sum is 6." in execute.prompt and "not evidence and not a justification" in execute.prompt
    assert "turns/turn_001" not in execute.prompt  # the previous turn is never an evidence path
    assert '\\"answer\\": 6' not in execute.prompt and '"answer": 6' not in execute.prompt  # its Result IR is not carried


def test_state_and_archive_files_use_lf_on_every_os(tmp_path: Path) -> None:
    """Every workspace file is written with LF; Path.write_text without newline=
    wrote CRLF on Windows, so artifacts differed byte-for-byte by OS."""
    from pdl_taskmaster.controller.mechanical_controller import MemoryAtomicJsonStore, ProtocolState
    from pdl_taskmaster.runtime.workspace import MemoryWorkspaceRun

    store = MemoryAtomicJsonStore(tmp_path / "state" / "controller-state.json")
    store.save(ProtocolState.new())
    assert b"\r\n" not in store.path.read_bytes()

    ws = MemoryWorkspaceRun.create(ROOT, tmp_path / "ws", turn_id="turn_001")
    archive = ws.flush_turn_archive()
    assert b"\r\n" not in archive.read_bytes()

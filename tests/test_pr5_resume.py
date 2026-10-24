"""PR #5 F1: session switching preserves the active session on rejection. Offline."""
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.host import repl

from test_api import ROOT
from test_l153_modes import DirectWorker, REQUEST


def _args(*flags):
    args = repl._build_parser().parse_args(list(flags))
    args.candidate_repo = ROOT
    return args


def _saved_session(folder, mode):
    with api.Session.open(DirectWorker(), folder, repo_root=ROOT, mode=mode) as session:
        session.send(REQUEST)
        return session.status()["workspace_path"]


def test_implicit_resume_adopts_destination_mode_without_rewriting_launch_args(tmp_path):
    saved = _saved_session(tmp_path / "protocol", "protocol")
    args, worker = _args(), DirectWorker()
    worker.agent_tools = None  # carries API-worker defaults, without a live transport
    current = repl.open_session(args, tmp_path, worker, "direct")
    try:
        assert current.host.engine.mode == "saver"
        resumed = repl.switch_session(current, args, tmp_path, worker, "protocol")
        current = resumed
        assert current.host.engine.mode == "protocol"
        assert current.host.status()["workspace_path"] == saved
        assert args.mode is None
    finally:
        current.close()


def test_rejected_resume_keeps_current_host_transcript_and_worker_bindings(tmp_path):
    _saved_session(tmp_path / "protocol", "protocol")
    args, worker = _args("--mode", "direct"), DirectWorker()
    worker.workdir = "initial"
    worker.progress_path = Path("initial.log")
    worker.trace_path = Path("initial.jsonl")
    current = repl.open_session(args, tmp_path, worker, "direct")
    before = (worker.workdir, worker.progress_path, worker.trace_path)
    try:
        current.host.handle(REQUEST)
        with pytest.raises(ValueError, match="runs in protocol mode"):
            repl.switch_session(current, args, tmp_path, worker, "protocol")
        assert not current.transcript.closed
        assert (worker.workdir, worker.progress_path, worker.trace_path) == before
        assert current.host.handle("A separate explanation.").closed
        current.transcript.write("still usable\n")
        current.transcript.flush()
    finally:
        if not current.transcript.closed:
            current.close()


def test_failed_start_rolls_back_worker_bindings_without_closing_current(tmp_path, monkeypatch):
    args, worker = _args("--mode", "direct"), DirectWorker()
    worker.trace_path = Path("initial.jsonl")
    current = repl.open_session(args, tmp_path, worker, "current")
    before = worker.trace_path
    original = repl.PDLtHost.start

    def fail_destination(host):
        if host.workspace_root.parent.name == "broken":
            raise OSError("destination unavailable")
        return original(host)

    monkeypatch.setattr(repl.PDLtHost, "start", fail_destination)
    try:
        with pytest.raises(OSError, match="destination unavailable"):
            repl.switch_session(current, args, tmp_path, worker, "broken")
        assert not current.transcript.closed and worker.trace_path == before
        assert current.host.handle(REQUEST).closed
    finally:
        if not current.transcript.closed:
            current.close()


def test_protocol_to_saver_resume_and_self_resume_keep_the_saved_workspace(tmp_path):
    saved = _saved_session(tmp_path / "saver", "saver")
    args, worker = _args(), DirectWorker()
    current = repl.open_session(args, tmp_path, worker, "protocol")
    try:
        assert current.host.engine.mode == "protocol"
        current = repl.switch_session(current, args, tmp_path, worker, "saver")
        assert current.host.engine.mode == "saver" and current.host.status()["workspace_path"] == saved
        assert repl.switch_session(current, args, tmp_path, worker, "saver") is current
    finally:
        current.close()


def test_a_saved_protocol_review_is_preserved_on_resume(tmp_path):
    with api.Session.open(DirectWorker(), tmp_path / "review", repo_root=ROOT,
                          mode="protocol", no_review=False) as session:
        result = session.send(REQUEST)
        saved = session.status()["workspace_path"]
        assert result.stage == "PROMPT_REVIEW"
    current = repl.open_session(_args(), tmp_path, DirectWorker(), "review")
    try:
        assert current.host.status()["workspace_path"] == saved
        assert current.host.status()["controller_state"]["stage"] == "PROMPT_REVIEW"
    finally:
        current.close()

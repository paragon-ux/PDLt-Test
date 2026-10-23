"""A PDLt session as a library object (L120). The REPL and headless runs drive the same host this drives; a library
caller sends messages and gets a TurnResult back, with the exit status a headless run would give.

    from pdl_taskmaster.api import Session, create_worker

    worker = create_worker("api", model="...")
    with Session.open(worker, "runs/sessions/demo", no_review=True) as session:
        result = session.send("...")
        print(result.stage, result.exit_status, result.provenance)

A provider or transport error raises from ``send`` (a headless run exits 4 on it); the session stays usable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pdl_taskmaster.api.outcome import RESULT_STAGES, TurnResult, exit_status

POINTER = "session.json"
# Standing confirmations ``run(confirm=True)`` gives before it reports the open review instead (prompt and plan
# need two; a revision loop is the user's to drive).
MAX_STANDING_CONFIRMATIONS = 8


def default_repo_root() -> Path:
    """The PDLt checkout this package runs from: the Standard, the operations and their schemas."""
    import pdl_taskmaster

    return Path(pdl_taskmaster.__file__).resolve().parents[2]


def prepare_worker(worker: Any, session_dir: Path, workdir: Path | None = None) -> None:
    """Point the worker's working folder, progress log and call trace at the session folder."""
    if hasattr(worker, "workdir"):
        worker.workdir = str(workdir or session_dir)
    if hasattr(worker, "progress_path"):
        worker.progress_path = session_dir / "worker-progress.log"
    if hasattr(worker, "trace_path"):
        worker.trace_path = session_dir / "call-trace.jsonl"


MODE_FILE = "mode.json"


def check_session_mode(session_dir: Path, mode: str, restoring: bool) -> None:
    """A session runs in one mode for its whole life (L153): a mode change opens a new session, so no turn history
    crosses modes. A session with history and no mode file ran in protocol mode."""
    path = Path(session_dir) / MODE_FILE
    stored = json.loads(path.read_text(encoding="utf-8")).get("mode") if path.is_file() else None
    if stored is None and restoring:
        stored = "protocol"
    if stored is not None and stored != mode:
        raise ValueError(f"session {Path(session_dir).name} runs in {stored} mode; a mode change opens a new session")
    if mode != "protocol" and not path.is_file():
        path.write_text(json.dumps({"mode": mode}) + "\n", encoding="utf-8")


def stored_workspace(session_dir: Path, warn: Callable[[str], None] | None = None) -> Path | None:
    """The workspace the session's pointer names, when it still exists."""
    pointer = session_dir / POINTER
    if not pointer.is_file():
        return None
    try:
        data = json.loads(pointer.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:  # e.g. a pointer cut short before replace-on-write
        if warn is not None:
            warn(f"session pointer unreadable ({exc}); starting fresh protocol state")
        return None
    stored = data.get("workspace_path")
    if stored and Path(stored).is_dir():
        return Path(stored)
    if data.get("workspace_relpath"):
        candidate = (session_dir / data["workspace_relpath"]).resolve()
        return candidate if candidate.is_dir() else None
    if stored:
        candidate = (session_dir / "workspaces" / Path(stored).name).resolve()
        return candidate if candidate.is_dir() else None
    return None


def write_pointer(session_dir: Path, session_id: str, workspace_path: str | Path | None) -> None:
    """Record the session's workspace, so reopening the session resumes it. Nothing is written before one exists."""
    from pdl_taskmaster.fileio import replace_text

    if not workspace_path:
        return
    payload: dict[str, Any] = {"session_id": session_id, "workspace_path": str(workspace_path)}
    try:
        payload["workspace_relpath"] = Path(workspace_path).relative_to(session_dir).as_posix()
    except ValueError:
        pass
    replace_text(session_dir / POINTER, json.dumps(payload, indent=2) + "\n")


class Session:
    """One session: a folder holding its workspaces, observations, worker log and call trace."""

    def __init__(self, host: Any, session_dir: Path):
        self.host = host
        self.session_dir = session_dir

    @classmethod
    def open(cls, worker: Any, session_dir: str | Path, *, repo_root: str | Path | None = None,
             sandbox_mode: str | None = None, no_review: bool = False, restore: bool = True,
             output_verifier: Any = None, run_id: str = "api", task_type: str | None = None,
             settings: Any = None, sys1: Any = None, mode: str = "protocol") -> "Session":
        """Open the session in ``session_dir``, resuming its workspace when ``restore`` and it has one.

        ``no_review`` runs the standard route (no prompt or plan review). ``output_verifier`` replaces the host's
        verifier registry (``verification.output_verifier.OutputVerifier``), for callers that register their own
        domain checkers. ``sandbox_mode`` None means $PDLT_SANDBOX, else auto. ``task_type`` pins a registered task
        type for every request (extensions/task_types.py); None lets System 1 classify each one. ``settings`` is a
        RunSettings (runtime/run_settings.py) carrying these and the other run settings; without it they are read
        from the arguments and the worker's attributes. ``sys1`` is a System 1 client (api.create_system1); None:
        the worker's."""
        from pdl_taskmaster.extensions import task_types
        from pdl_taskmaster.host.app import PDLtHost
        from pdl_taskmaster.runtime.run_settings import RunSettings

        if settings is None:
            settings = RunSettings.from_worker(worker, no_review=no_review, sandbox_mode=sandbox_mode,
                                               task_type=task_type, mode=mode)
        elif (no_review, sandbox_mode, task_type, mode) != (False, None, None, "protocol"):
            raise ValueError("pass no_review, sandbox_mode, task_type and mode in settings when settings is given")
        no_review, task_type = settings.no_review, settings.task_type
        if task_type is not None:
            route = "unconfirmed" if no_review else "confirmed"
            if task_type not in task_types.REGISTRY:
                raise ValueError(f"unknown task type {task_type!r}; registered: {', '.join(task_types.REGISTRY.names())}")
            if route not in task_types.REGISTRY.get(task_type).routes:
                raise ValueError(f"task type {task_type!r} does not run on the {route} route")

        session_dir = Path(session_dir).resolve()
        session_dir.mkdir(parents=True, exist_ok=True)
        prepare_worker(worker, session_dir)
        restore_path = stored_workspace(session_dir) if restore else None
        check_session_mode(session_dir, settings.mode, restore_path is not None)
        host = PDLtHost(repo_root or default_repo_root(), worker=worker,
                        workspace_root=session_dir / "workspaces",
                        restore_path=restore_path,
                        run_id=run_id, observation_dir=session_dir / "observations",
                        settings=settings, sys1_client=sys1).start()
        if output_verifier is not None:
            host.engine.output_verifier = output_verifier
        session = cls(host, session_dir)
        session._refresh_pointer()
        return session

    @property
    def restore_notice(self) -> str | None:
        """Why a stored workspace could not be resumed, when it could not."""
        return getattr(self.host, "restore_notice", None)

    def send(self, message: str) -> TurnResult:
        """A request, a follow-up, or a review command (/confirm, /revise <feedback>, /stop, /cancel)."""
        return self._result(self.host.handle(message))

    def confirm(self) -> TurnResult:
        return self.send("/confirm")

    def revise(self, feedback: str) -> TurnResult:
        return self.send(f"/revise {feedback}")

    def stop(self) -> TurnResult:
        return self.send("/stop")

    def cancel(self) -> TurnResult:
        return self.send("/cancel")

    def run(self, message: str, *, confirm: bool = False) -> TurnResult:
        """Send ``message``; with ``confirm``, accept each review it opens on a standing confirmation (recorded as
        such, as the REPL's fast mode does). An artifact with host findings is left for review."""
        result = self.send(message)
        for _ in range(MAX_STANDING_CONFIRMATIONS):
            if not (confirm and result.review) or result.details.get("host_findings"):
                break
            result = self._result(self.host.confirm_on_standing_instruction())
        return result

    def status(self) -> dict[str, Any]:
        return self.host.status()

    def close(self) -> None:
        self.host.close()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _refresh_pointer(self) -> None:
        write_pointer(self.session_dir, self.session_dir.name, self.host.status().get("workspace_path"))

    def _result(self, turn: Any) -> TurnResult:
        self._refresh_pointer()
        status = self.host.status()
        state = status.get("controller_state")
        stage = state.get("stage") if state else None
        refused = bool(status.get("refused")) and state is None
        record = None
        workspace = getattr(self.host.engine, "workspace", None)
        if turn.closed and stage in RESULT_STAGES and workspace is not None:
            record = workspace.read_provenance()
        return TurnResult(text=turn.text, stage=stage, exit_status=exit_status(stage, refused=refused),
                          closed=bool(turn.closed), review=turn.review, refused=refused, provenance=record,
                          workspace_path=status.get("workspace_path"),
                          details={"bypass": bool(turn.bypass), "host_findings": bool(turn.host_findings)})

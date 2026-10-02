from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
import sys

from pdl_taskmaster.observation.session import ObservedSession
from pdl_taskmaster.observation.records import controller_snapshot
from pdl_taskmaster.observation.sink import JsonlSink


@dataclass
class HostTurn:
    text: str | None
    bypass: bool
    closed: bool
    state_after: dict[str, Any] | None


@dataclass
class _PlainRequest:
    prompt: str
    operation: str = "BYPASS_ORDINARY"
    environment: str | None = None  # the session's execution environment, capabilities only


def _plain_reply_text(text: str | None) -> str | None:
    """A direct reply as text: a JSON object holding a single string (e.g.
    {"message": "..."} or {"response": "..."}) is presented as that string."""
    try:
        value = json.loads(text or "")
    except ValueError:
        return text
    if isinstance(value, dict) and len(value) == 1:
        (only,) = value.values()
        if isinstance(only, str):
            return only
    return text


REVIEW_COMMANDS = frozenset({"/confirm", "/revise", "/stop", "/cancel"})
NO_OPEN_REVIEW = (
    "No review is open: /confirm, /revise, /stop and /cancel apply to a pending prompt or plan review. "
    "Send a new request to start a task."
)


DEFAULT_HIGHER_PRIORITY_CONSTRAINTS = (
    "Obey applicable provider/platform safety, privacy, permission, and tool constraints."
)


class PDLtHost:
    """External interactive host.

    The host owns process/session lifetime only. Protocol state remains in
    SessionEngine/Workspace; /status is a read-only projection.
    """

    def __init__(
        self,
        candidate_repo: str | Path,
        *,
        worker: Any,
        workspace_root: str | Path | None = None,
        restore_path: str | Path | None = None,
        run_id: str = "host",
        case_id: str | None = None,
        observation_dir: str | Path | None = None,
        include_bodies: bool = False,
        render_compact: bool = False,
        higher_priority_constraints: str | None = None,
        sandbox_mode: str | None = None,
    ):
        self.candidate_repo = Path(candidate_repo).resolve()
        self.worker = worker
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd() / "runs" / "workspaces"
        self.restore_path = Path(restore_path) if restore_path else None
        self.run_id = run_id
        self.case_id = case_id
        self.observation_dir = Path(observation_dir) if observation_dir else None
        self.include_bodies = include_bodies
        self.render_compact = render_compact
        self.higher_priority_constraints = higher_priority_constraints or DEFAULT_HIGHER_PRIORITY_CONSTRAINTS
        self.sandbox_mode = sandbox_mode  # None: $PDLT_SANDBOX, else auto (native confinement)
        self.engine: Any = None
        self.observed: ObservedSession | None = None
        self.sink: JsonlSink | None = None

    def _load_candidate(self) -> None:
        repo = str(self.candidate_repo)
        if repo not in sys.path:
            sys.path.insert(0, repo)

    def start(self) -> "PDLtHost":
        self._load_candidate()
        from pdl_taskmaster.runtime.session_engine import SessionEngine

        self.restore_notice: str | None = None
        engine: SessionEngine | None = None
        if self.restore_path is not None:
            try:
                engine = SessionEngine.restore(
                    str(self.candidate_repo),
                    lambda request: "",
                    self.restore_path,
                    higher_priority_constraints=self.higher_priority_constraints,
                    available_execution_tools=None,
                    render_compact=self.render_compact,
                    sys1_client=getattr(self.worker, "sys1_client", None),
                    sandbox_mode=self.sandbox_mode,
                )
            except Exception as exc:
                # Graceful degradation: a session with no committed protocol
                # state (bypass-only, or a chained turn interrupted before any
                # commit) resumes as a fresh engine rather than crashing the
                # host. The notice is surfaced by the REPL.
                self.restore_notice = f"session state not restorable ({exc}); starting fresh protocol state"
        if engine is None:
            engine = SessionEngine(
                str(self.candidate_repo),
                lambda request: "",
                higher_priority_constraints=self.higher_priority_constraints,
                available_execution_tools=None,
                workspace_root=self.workspace_root,
                render_compact=self.render_compact,
                sys1_client=getattr(self.worker, "sys1_client", None),
                sandbox_mode=self.sandbox_mode,
            )
        self.engine = engine
        engine.max_repairs = getattr(self.worker, "max_repairs", None)
        engine.draft_execute = bool(getattr(self.worker, "draft_execute", False))
        if self.observation_dir is not None:
            session_id = f"{self.run_id}-{self.case_id or 'session'}"
            self.sink = JsonlSink(self.observation_dir, session_id)
        self.observed = ObservedSession(
            engine,
            self.sink,
            run_id=self.run_id,
            case_id=self.case_id,
            include_bodies=self.include_bodies,
            worker=self.worker,
        )
        return self

    def handle(self, user_message: str) -> HostTurn:
        if self.observed is None:
            raise RuntimeError("host not started")
        command = user_message.split(maxsplit=1)[0].lower() if user_message.strip() else ""
        if command in REVIEW_COMMANDS and self._at_protocol_entry():
            # A review command with no open review is not a request: wrapped as one, a
            # piped /confirm left over after closure started the task again.
            return HostTurn(text=NO_OPEN_REVIEW, bypass=False, closed=False,
                            state_after=controller_snapshot(self.engine))
        routed_message = self._ensure_protocol_entry(user_message)
        response = self.observed.handle_user_message(routed_message)
        if response.bypass and response.text is None:
            plain = self.worker.call(_PlainRequest(user_message, environment=self._bypass_environment()))
            return HostTurn(
                text=_plain_reply_text(plain.text),
                bypass=True,
                closed=False,
                state_after=controller_snapshot(self.engine),
            )
        return HostTurn(
            text=response.text,
            bypass=bool(response.bypass),
            closed=bool(response.closed),
            state_after=controller_snapshot(self.engine),
        )

    def _bypass_environment(self) -> str | None:
        """The factual execution environment for a direct reply (the sandbox's
        own System 1 routing state), and where programs actually run."""
        sandbox = getattr(self.engine, "sandbox", None)
        if sandbox is None:
            return None
        try:
            environment = sandbox.decision_state()["execution_environment"]
        except Exception:
            return None
        return (f"{environment} Programs run only in the execution stage of a confirmed task, "
                "not during a direct reply.")

    def _at_protocol_entry(self) -> bool:
        """No protocol instance is open: the next request starts one."""
        if self.engine is None or self.engine.controller is None:
            return True
        return self.engine.controller.state.stage.value in {"CLOSED_SUCCESS", "CLOSED_CANCELLED"}

    def _ensure_protocol_entry(self, user_message: str) -> str:
        if self._at_protocol_entry():
            return self._with_invocation(user_message)
        return user_message

    @staticmethod
    def _with_invocation(user_message: str) -> str:
        if "$confirm-with-pseudocode" in user_message:
            return user_message
        return "$confirm-with-pseudocode " + user_message

    def status(self) -> dict[str, Any]:
        if self.engine is None:
            return {"active": False}
        state = self.engine.controller.state.to_dict() if self.engine.controller is not None else None
        return {
            "active": True,
            "workspace_id": self.engine.workspace.metadata.get("workspace_id") if self.engine.workspace else None,
            "workspace_path": str(self.engine.workspace.path) if self.engine.workspace else None,
            "controller_state": state,
            "refused": bool(getattr(self.engine, "refused", False)),
        }

    def close(self) -> None:
        try:
            close_engine = getattr(self.engine, "close", None)
            if close_engine is not None:
                close_engine()
        finally:
            if self.sink is not None:
                self.sink.close()

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
import json
import os
import re
import tempfile
import hashlib

from pdl_taskmaster.controller.mechanical_controller import (
    AtomicJsonStore,
    ControllerError,
    Intent,
    MechanicalController,
    MemoryAtomicJsonStore,
    NextAction,
    ProtocolState,
    ReviewDecision,
    Stage,
    Transition,
)
from pdl_taskmaster.runtime.operation_bridge import ActivationRoute, ModelRequest, OperationBridge, WireError
from pdl_taskmaster.runtime.quarantine import compile_bootstrap_output
from pdl_taskmaster.verification.sandbox import ExecutionSandbox


def _wrap_witness(d: dict[str, Any]) -> dict[str, Any]:
    """A printed witness without an explicit polarity is a positive witness whose
    payload is exactly what the sandbox printed."""
    if "polarity" in d:
        return d
    return {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": d}


def _parse_sandbox_witness(stdout_text: str) -> dict[str, Any] | None:
    """Parse the host-reproduced witness from sandbox stdout (ADR-0018).

    Exactly two forms are recognised: a ``WITNESS: <json>`` protocol line (the last
    one wins), or an entire stdout that is one JSON object. Nothing else in stdout
    is scanned, guessed, or re-labelled.
    """
    import ast

    text = (stdout_text or "").strip()
    if not text:
        return None
    for line in reversed(text.splitlines()):
        blob = witness_payload(line)
        if not blob:
            continue
        for loader in (json.loads, ast.literal_eval):
            try:
                d = loader(blob)
            except Exception:
                continue
            if isinstance(d, dict):
                return _wrap_witness(d)
        break
    try:
        d = json.loads(text)
    except Exception:
        return None
    return _wrap_witness(d) if isinstance(d, dict) else None


from pdl_taskmaster.runtime.text_blocks import fenced_blocks, split_published_ir, witness_payload, words  # noqa: E402


from pdl_taskmaster.verification.error_registry import Finding, finding_codes  # noqa: E402

def _is_wire_failure(exc: BaseException) -> bool:
    """A reply that is not a valid output object: one the host failed to parse
    (WireError) or one the provider's own schema check rejected (a ProviderError
    marked wire_equivalent). Both are model-output failures, never harness errors."""
    return isinstance(exc, WireError) or bool(getattr(exc, "wire_equivalent", False))


class _FailedExecution:
    """Stand-in outcome for an EXECUTE response that never parsed (cut off at the
    output cap, or malformed past its wire retry): a RESULT with nothing in it."""

    kind = "RESULT"
    body = ""
    result_ir = None


# Repairs per execution that do not count against the tier: after an attempt that
# ran no program, the sandbox measured nothing, so the tier's repairs stay intact.
UNMEASURED_REPAIRS = 1


def _previous_turn_reference(previous: dict[str, Any] | None) -> str | None:
    """The previous turn's result as labelled reference for a follow-up turn."""
    if not previous or not previous.get("result"):
        return None
    status = "completed" if previous.get("status") == "CLOSED_SUCCESS" else "was cancelled"
    return (
        "PREVIOUS TURN RESULT (reference only). It shows what the previous turn produced so that the new request "
        "can be understood. It is not evidence and not a justification: do not cite it, rely on it, or reason "
        "from it. Derive every result from the confirmed prompt and the supplied data.\n"
        f"The previous turn {status}. Its result:\n{previous['result']}"
    )


def _normalized_lines(body: str) -> list[str]:
    """Non-empty lines, lowercased, with punctuation and whitespace runs collapsed."""
    lines = (" ".join(words(line)) for line in (body or "").splitlines())
    return [line for line in lines if line]


def _python_blocks(body: str) -> list[str]:
    """The Python the host runs, decided by grammar, never by keywords.

    A deliverable body that is itself a Python module (it parses, and it does more
    than state a bare literal) is one program. Otherwise every fenced block tagged
    ``python`` or ``py`` is a program. Prose never parses as a module.
    """
    import ast

    text = body or ""
    try:
        module = ast.parse(text)
    except SyntaxError as error:
        module = None
        fenced = [block for block in fenced_blocks(text, ("python", "py")) if block.strip()]
        if not fenced and _is_program_prefix(text, error.lineno):
            # A program with a syntax error is still a program: run it, so the
            # sandbox reports the error and its line instead of "no program".
            return [text]
    except (ValueError, MemoryError, RecursionError):
        # CPython's parser raises MemoryError, not SyntaxError, on long runs of
        # bare words (prose); either way the body is not a program.
        module = None
    if module is not None and any(
        not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
        for node in module.body
    ):
        return [text]
    return [block for block in fenced_blocks(text, ("python", "py")) if block.strip()]


def _stderr_summary(stderr: str | None) -> str:
    """The program's own failure location and message from standard error."""
    from pdl_taskmaster.verification.sandbox import PROGRAM_FILENAME

    lines = [line for line in (stderr or "").strip().splitlines() if line.strip()]
    if not lines:
        return ""
    location = next((line.strip() for line in reversed(lines) if f'File "{PROGRAM_FILENAME}"' in line), "")
    tail = lines[-3:] if "Error" not in lines[-1] else [lines[-1]]
    parts = ([location] if location else []) + [line.strip() for line in tail]
    return " Standard error: " + " / ".join(parts)


def _is_program_prefix(text: str, error_line: int | None) -> bool:
    """The source around a syntax error parses as Python and has program
    structure: an import, definition, loop or other block statement, or at least
    three statements. The source before the error is checked first; an unclosed
    bracket is reported at its opening line, so the source after the error line
    is checked too. Prose fails on its first line and has no parsable remainder;
    a lone assignment followed by sentences ("n = 15" then prose) does not
    qualify."""
    import ast

    if not error_line:
        return False
    structural = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.For, ast.While,
                  ast.If, ast.With, ast.Try)

    def has_structure(source: str) -> bool | None:
        try:
            module = ast.parse(source)
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            return None
        statements = [node for node in module.body if not isinstance(node, ast.Expr)]
        return len(statements) >= 3 or any(isinstance(node, structural) for node in statements)

    lines = text.splitlines()
    for end in range(error_line - 1, 0, -1):  # before the error: back off to a complete statement
        verdict = has_structure("\n".join(lines[:end]))
        if verdict is not None:
            if verdict:
                return True
            break
    for start in range(error_line, min(len(lines), error_line + 20)):  # after the error line
        verdict = has_structure("\n".join(lines[start:]))
        if verdict is not None:
            return verdict
    return False
    lines = text.splitlines()
    for end in range(error_line - 1, 0, -1):  # back off to the last complete statement
        try:
            prefix = ast.parse("\n".join(lines[:end]))
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            continue
        statements = [node for node in prefix.body if not isinstance(node, ast.Expr)]
        structural = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef, ast.For, ast.While,
                      ast.If, ast.With, ast.Try)
        return len(statements) >= 3 or any(isinstance(node, structural) for node in statements)
    return False


def _attach_result_ir(body: str, ir_dict: dict[str, Any]) -> str:
    """Publish the host-validated Result IR (which carries the authoritative witness)
    after the deliverable. The deliverable text is never rewritten."""
    ir_json_str = json.dumps(ir_dict, indent=2, ensure_ascii=False)
    return body.rstrip() + f"\n\n```json\n{ir_json_str}\n```"


from pdl_taskmaster.runtime.workspace import MemoryWorkspaceRun, WorkspaceError, WorkspaceRun
from pdl_taskmaster.runtime import presentation


ModelCall = Callable[[ModelRequest], str]


_EXPLICIT_INVOCATION = re.compile(
    r"^\s*(?:(?:please\s+)?(?:(?:could|can|would)\s+you\s+)?(?:use|apply|invoke|run)\s+)?"
    r"(?:\$confirm-with-pseudocode|\[\$confirm-with-pseudocode\]\([^)]+\))"
    r"\s*(?:(?:to)\b|[.:,;-])?\s*(?P<body>.*)$",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class InvocationObservation:
    explicit: bool
    substantive_request: str


def observe_invocation(user_message: str) -> InvocationObservation:
    """Recognize host-visible leading skill invocation syntax.

    Only the leading control wrapper is removed. Mentions inside the substantive
    request remain data, including tasks whose subject is this protocol.
    """
    match = _EXPLICIT_INVOCATION.match(user_message)
    if not match:
        return InvocationObservation(False, user_message.strip())
    return InvocationObservation(True, match.group("body").strip())


@dataclass
class CallTrace:
    operation: str
    projection_manifest: dict[str, Any]
    model_text: str
    workspace_stage: str
    workspace_invocation_id: str


@dataclass
class EngineResponse:
    text: str | None
    traces: list[CallTrace] = field(default_factory=list)
    bypass: bool = False
    closed: bool = False
    refused: bool = False


class SessionEngine:
    """Condition C session orchestrator.

    Control flow is owned by MechanicalController. Context flow and durable
    stage-to-stage handoff are owned by WorkspaceRun. Semantic worker calls are
    stateless and receive only the operation projection compiled from the
    materialized stage inputs plus applicable Standard clauses.
    """

    def __init__(
        self,
        repo_root: str | Path,
        model_call: ModelCall,
        *,
        higher_priority_constraints: Any = None,
        available_execution_tools: Any = None,
        workspace_root: str | Path | None = None,
        render_compact: bool = False,
        sys1_client: Any = None,
    ):
        self.repo_root = Path(repo_root)
        self.model_call = model_call
        self.higher_priority_constraints = higher_priority_constraints
        self.bridge = OperationBridge(self.repo_root, render_compact=render_compact)
        # Axiom 3: one session-scoped sandbox, constructed at boot and reused by every run.
        # It builds its session lazily, on the first program run; close() releases it.
        self.sandbox = ExecutionSandbox(timeout_seconds=15.0, label="engine")
        self._sandbox_session_logged: Any = None  # the workspace that has its SANDBOX_SESSION event
        # The solver is told the truth about where its code runs (EXEC-01): the
        # sandbox under the task's routed budget, unless the host declares its own.
        from pdl_taskmaster.verification.sandbox import DEFAULT_BUDGET

        self._host_execution_tools = available_execution_tools
        self._profile_distribution: dict[str, float] = {}
        self._execution_budget = DEFAULT_BUDGET
        self.available_execution_tools = (
            available_execution_tools if available_execution_tools is not None
            else self.sandbox.describe(DEFAULT_BUDGET)
        )
        self.controller: Optional[MechanicalController] = None
        self.workspace: Optional[WorkspaceRun] = None
        # System 1 is injected by the host (the live worker owns it). The engine never
        # builds a network client from ambient environment variables, so an engine
        # constructed without one is fully offline.
        self.sys1_client = sys1_client
        # Protocol v2: semantic-bootstrap containment (structural, non-optional).
        # Raw untrusted content is read by BOOTSTRAP_ANALYSIS only; every compile
        # operation receives the sanitized compiled analysis. Cache is keyed on
        # the raw source so repeated sources bootstrap once per session.
        self._bootstrap_cache: dict[tuple[str, str | None], str] = {}
        self._task_entities_cache: dict[tuple[str, str | None], tuple[str, ...]] = {}
        # S4: confirmed deliverable carried from the prior turn (chaining);
        # None for first turns and legacy single-turn workspaces.
        self._previous_deliverable: str | None = None
        self._previous_turn: dict[str, Any] | None = None
        # Run settings set by the host from CLI flags: None = the routed tier's repairs;
        # 0 = stop at the first failed EXECUTE (no repair, no retry of any kind).
        self.max_repairs: int | None = None
        self.draft_execute = False  # A/B option: DRAFT_EXECUTE brief before the first EXECUTE
        self._active_task_entities: tuple[str, ...] = ()
        # AUTH-04: the user's original request is source data for execution; the
        # confirmed prompt governs task semantics where the two differ.
        self._source_request: str | None = None
        self._requires_verified_execution: bool = False
        self._problem_domain: Any = None
        self.refused: bool = False
        if workspace_root is None:
            self.workspace_root = Path(tempfile.mkdtemp(prefix="pdl-c0-workspaces-"))
        else:
            self.workspace_root = Path(workspace_root)
            self.workspace_root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def restore(
        cls,
        repo_root: str | Path,
        model_call: ModelCall,
        workspace_path: str | Path,
        *,
        higher_priority_constraints: Any = None,
        available_execution_tools: Any = None,
        render_compact: bool = False,
        sys1_client: Any = None,
    ) -> "SessionEngine":
        workspace_path = Path(workspace_path)
        engine = cls(
            repo_root,
            model_call,
            higher_priority_constraints=higher_priority_constraints,
            available_execution_tools=available_execution_tools,
            workspace_root=workspace_path.parent,
            render_compact=render_compact,
            sys1_client=sys1_client,
        )
        workspace = MemoryWorkspaceRun.open(repo_root, workspace_path)
        # Pointer may sit on a turn whose controller never committed (e.g. a
        # turn opened by S4 chaining and then interrupted before any model
        # call). Fall back to the most recent turn with a committed,
        # instance-matching state before declaring the session unrestorable.
        candidates: list[tuple[str | None, Path, str | None]] = []
        if workspace.turn_id is not None:
            ordered_ids = [workspace.turn_id]
            turns_dir = workspace.path / "turns"
            if turns_dir.is_dir():
                ordered_ids.extend(
                    d.name for d in sorted(turns_dir.iterdir(), reverse=True)
                    if d.is_dir() and re.match(r"^turn_\d+$", d.name) and d.name != workspace.turn_id
                )
            for turn_id in ordered_ids:
                turn_meta = workspace.read_turn_status(turn_id)
                candidates.append((
                    turn_id,
                    workspace.path / "turns" / turn_id / "state" / "controller-state.json",
                    turn_meta.get("protocol_instance_id") or workspace.protocol_instance_id,
                ))
        else:
            if workspace.protocol_instance_id is None:
                raise WorkspaceError("restorable_protocol_state_missing")
            candidates.append((None, workspace.controller_state_path, workspace.protocol_instance_id))
        restore_state_path: Path | None = None
        for turn_id, candidate_path, expected_instance in candidates:
            if not candidate_path.is_file():
                continue
            candidate_state = json.loads(candidate_path.read_text(encoding="utf-8"))
            if candidate_state.get("instance_id") == expected_instance:
                restore_state_path = candidate_path
                if turn_id is not None and turn_id != workspace.turn_id:
                    workspace.metadata["turn_id"] = turn_id
                    workspace._atomic_write(
                        workspace.metadata_path,
                        json.dumps(workspace.metadata, ensure_ascii=False, indent=2) + "\n",
                    )
                    workspace.turn_id = turn_id
                break
        if restore_state_path is None:
            raise WorkspaceError("restorable_protocol_state_missing")
        store = (
            MemoryAtomicJsonStore(restore_state_path)
            if isinstance(workspace, MemoryWorkspaceRun)
            else AtomicJsonStore(restore_state_path)
        )
        state = store.load()
        if state.instance_id != workspace.protocol_instance_id and workspace.turn_id is None:
            raise WorkspaceError("restore_instance_binding")
        engine.workspace = workspace
        engine.controller = MechanicalController(state, store)
        # Cross-epoch deliverable chaining: repopulate the prior confirmed
        # deliverable on restore. The S4 turn-chaining path sets this field
        # only when a new user message opens a turn in the same process; a
        # resumed epoch (e.g. /confirm in a later REPL invocation) must
        # re-chain it so the execution phase still receives the byte-exact
        # prior deliverable in REQUIRED_TASK_INPUTS. The active turn's status
        # is ACTIVE at restore time, so previous_deliverable() correctly
        # returns the last CLOSED_SUCCESS turn before it.
        engine._previous_turn = workspace.previous_turn()
        engine._previous_deliverable = _previous_turn_reference(engine._previous_turn)
        engine._source_request = workspace.turn_source()
        workspace.append_event("SESSION_RESTORED", {"instance_id": state.instance_id})
        return engine

    def _new_workspace(self) -> WorkspaceRun:
        # ADR-0011 / ADR-0008: software-defined in-memory VFS workspace run.
        # Fast, unjournaled writes bypass Windows NTFS fsync latency.
        # Legacy flat workspaces remain supported for direct WorkspaceRun.create callers.
        return MemoryWorkspaceRun.create(self.repo_root, self.workspace_root, turn_id="turn_001")

    def _bind_new_controller(self, workspace: WorkspaceRun) -> MechanicalController:
        state = ProtocolState.new()
        workspace.bind_protocol(state.instance_id)
        store = (
            MemoryAtomicJsonStore(workspace.controller_state_path)
            if isinstance(workspace, MemoryWorkspaceRun)
            else AtomicJsonStore(workspace.controller_state_path)
        )
        controller = MechanicalController(state, store)
        workspace.publish_approach_sources([])
        return controller

    def _invoke(self, request: ModelRequest, traces: list[CallTrace]) -> str:
        model_text = self.model_call(request)
        self.workspace.record_model_output(request.workspace_invocation, model_text)
        traces.append(
            CallTrace(
                request.operation,
                request.manifest,
                model_text,
                request.workspace_invocation.stage,
                request.workspace_invocation.invocation_id,
            )
        )
        return model_text

    def _call(
        self,
        operation: str,
        values: dict[str, Any],
        traces: list[CallTrace],
        parser: Callable[[str], Any] | None = None,
        operator_correction: str | None = None,
    ) -> Any:
        """Invoke one operation. With a parser, retry ONCE on WireError with an
        operator correction so a sampling glitch (invalid JSON, dropped field)
        costs one extra call instead of fatally failing the session. A caller may
        supply ``operator_correction`` (factual host-side findings only) for the
        first attempt; it travels outside the projection document."""
        if self.workspace is None:
            raise WorkspaceError("workspace_not_initialized")
        request = self.bridge.request(
            operation,
            values,
            workspace=self.workspace,
            higher_priority_constraints=self.higher_priority_constraints,
            operator_correction=operator_correction,
        )
        try:
            model_text = self._invoke(request, traces)
            return model_text if parser is None else parser(model_text)
        except Exception as first_error:
            if parser is None or not _is_wire_failure(first_error):
                raise
            feedback = getattr(first_error, "operator_feedback", None)
            if feedback:
                correction = (
                    f"OPERATOR CORRECTION: {feedback}. "
                    "Emit exactly one conforming JSON object matching the declared schema."
                )
            else:
                correction = (
                    "OPERATOR CORRECTION: the previous response failed host-side validation "
                    f"(reason: {first_error}). Emit exactly one JSON object that conforms to the "
                    "declared output_schema for this operation, with no prose or code fences around it."
                )
            if operator_correction:
                # A wire retry must not drop the caller's correction (e.g. verification
                # findings for a repair): the worker is stateless.
                correction = operator_correction + "\n\n" + correction
            retry_request = self.bridge.request(
                operation,
                values,
                workspace=self.workspace,
                higher_priority_constraints=self.higher_priority_constraints,
                operator_correction=correction,
            )
            try:
                return parser(self._invoke(retry_request, traces))
            except Exception as retry_error:
                if _is_wire_failure(retry_error):
                    raise first_error from None
                raise

    def _refuse(self, text: str | None, traces: list[CallTrace], phase: str) -> EngineResponse:
        """Close on a boundary refusal (ADR-0019 amendment): the refusal is a
        complete, correct answer, published as-is and closed with REFUSED."""
        assert self.workspace is not None
        self.refused = True
        self.workspace.append_event("PROTOCOL_REFUSED", {"phase": phase})
        return EngineResponse(text or presentation.cancelled(), traces, closed=True, refused=True)

    def _s1_activation(self, text: str) -> tuple[str, str | None] | None:
        """Phase 0 (TARGET_ARCHITECTURE §3): System 1 routes the request against the
        environment recipe state (policy scope, offline sandbox, knowledge cutoff).

        System 1 only: System 2 never sees the environment settings, and nothing here
        matches keywords or dates. Returns (route, refusal text) for a gated decision
        other than APPLY_PROTOCOL; System 1 absent, uncertain, or failing yields None
        (no System 1 evidence: the explicit invocation stands).
        """
        client = self.sys1_client
        if not (text or "").strip() or client is None or not client.is_configured:
            return None
        from pdl_taskmaster.providers.sys1.recipes.activation_route import ActivationRouteRecipe

        recipe = ActivationRouteRecipe()
        try:
            environment = {"execution_environment": self.sandbox.decision_state()["execution_environment"]}
            body, duration_ms = client.call(recipe.build_request({"request": text, "env": environment}))
            result = recipe.parse_response(body, duration_ms=duration_ms)
        except Exception:
            return None
        assert self.workspace is not None
        self.workspace.append_event(
            "ACTIVATION_ROUTED",
            {
                "verdict": result.verdict,
                "passed_gating": result.passed_gating,
                "confidence": result.confidence,
            },
        )
        if not result.passed_gating or result.verdict == "APPLY_PROTOCOL":
            return None
        if result.verdict == "BLOCKED_BY_HIGHER_PRIORITY":
            return result.verdict, recipe.map_to_wire(result)["response"]
        return result.verdict, None

    def _publish_prompt(self) -> None:
        assert self.controller is not None and self.workspace is not None
        prompt = self.controller.state.current_prompt
        assert prompt is not None
        self.workspace.publish_artifact("prompt", prompt.artifact_id, prompt.body, confirmed=prompt.confirmed)
        self.workspace.publish_approach_sources(list(self.controller.state.approach_sources))

    def _publish_plan(self) -> None:
        assert self.controller is not None and self.workspace is not None
        plan = self.controller.state.current_plan
        assert plan is not None
        prompt = self.controller.state.current_prompt
        assert prompt is not None
        self.workspace.publish_artifact(
            "plan",
            plan.artifact_id,
            plan.body,
            confirmed=plan.confirmed,
            source_prompt_id=plan.source_prompt_id,
            confirmed_prompt_hash=hashlib.sha256(prompt.body.encode("utf-8")).hexdigest(),
        )
        self.workspace.publish_approach_sources(list(self.controller.state.approach_sources))
        # Telemetry only: how much of the plan restates the prompt (PLAN-02 / PROMPT-02).
        prompt_lines = _normalized_lines(prompt.body)
        plan_lines = _normalized_lines(plan.body)
        copied = sum(1 for line in plan_lines if line in set(prompt_lines))
        self.workspace.append_event(
            "PLAN_PROMPT_ECHO",
            {
                "plan_id": plan.artifact_id,
                "identical": bool(plan_lines) and plan_lines == prompt_lines,
                "copied_line_ratio": round(copied / len(plan_lines), 3) if plan_lines else 0.0,
            },
        )

    def _semantic_read(self, raw_text: str, traces: list[CallTrace]) -> str | None:
        """Protocol v2 structural containment: the ONLY operation that sees raw
        untrusted content. Returns the sanitized compiled analysis for compile
        operations, or None when the bootstrap blocks under higher priority.
        """
        cache_key = (raw_text, self._previous_deliverable)
        if cache_key in self._bootstrap_cache:
            return self._bootstrap_cache[cache_key]
        bootstrap_values: dict[str, Any] = {
            "HOST_PROTOCOL_STATE": "SEMANTIC_READ",
            "RAW_UNTRUSTED_CONTENT": raw_text,
        }
        if self._previous_deliverable:
            # S4: the prior turn's confirmed deliverable is host-published,
            # gate-passed content (never raw untrusted input). It is compiled
            # as inactive background context for the new turn.
            bootstrap_values["PREVIOUS_DELIVERABLE"] = self._previous_deliverable
        outcome = self._call(
            "BOOTSTRAP_ANALYSIS",
            bootstrap_values,
            traces,
            parser=self.bridge.parse_bootstrap_analysis,
        )
        if outcome["kind"] == "BLOCKED_BY_HIGHER_PRIORITY":
            self._bootstrap_cache[cache_key] = ""
            self._blocked_response = outcome.get("response")
            return None
        compiled, _meta = compile_bootstrap_output(raw_text, outcome["task_summary"])
        # Containment-boundary durability: a lazy semantic read that classifies
        # substantive raw content as instruction-free loses the entire task
        # upstream of every gate. Detect and retry once before compiling.
        summary_lowers = (outcome["task_summary"] or "").lower()
        if len(raw_text) > 500 and (
            "no operative instructions" in summary_lowers
            or "no substantive" in summary_lowers
            or "no requested" in summary_lowers
            or len((outcome["task_summary"] or "").strip()) < 40
        ):
            self.workspace.append_event(
                "BOOTSTRAP_DEGENERATE_READ_RETRY",
                {"raw_chars": len(raw_text), "summary_chars": len(outcome["task_summary"] or "")},
            ) if self.workspace is not None else None
            outcome = self._call(
                "BOOTSTRAP_ANALYSIS",
                bootstrap_values,
                traces,
                parser=self.bridge.parse_bootstrap_analysis,
            )
            if outcome["kind"] == "BLOCKED_BY_HIGHER_PRIORITY":
                self._bootstrap_cache[cache_key] = ""
                return None
            compiled, _meta = compile_bootstrap_output(raw_text, outcome["task_summary"])


        # Mechanical entity containment: a task entity is forwarded downstream
        # ONLY if it is a verbatim substring of the SANITIZED task summary.
        # Hostile tokens (canaries, exploit directives) are replaced by the
        # sanitizer, so a hostile entity can never pass this filter -- the
        # verbatim-preservation channel inherits the compile tier's redaction.
        raw_entities = outcome.get("task_entities") or []
        entities = tuple(
            e for e in raw_entities
            if isinstance(e, str) and e.strip() and e in compiled
        )
        dropped = [e for e in raw_entities if e not in entities]
        if dropped and self.workspace is not None:
            self.workspace.append_event("TASK_ENTITY_DROPPED_UNSAFE", {"count": len(dropped)})
        self._task_entities_cache[cache_key] = entities
        # In Protocol v2 out-of-band field isolation: approach_notes carries TASK-02
        # procedural guidance for planning. risk_notes is quarantined threat data
        # retained in telemetry/traces, not leaked into compile contexts.
        approach = outcome.get("approach_notes", "")
        notes, _ = compile_bootstrap_output(raw_text, approach) if approach else ("", {})
        if "risk_notes" in outcome and isinstance(outcome["risk_notes"], str):
            sanitized_risk, _ = compile_bootstrap_output(raw_text, outcome["risk_notes"])
            outcome["risk_notes"] = sanitized_risk
        document = (
            f"TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):\n{compiled}\n"
            f"APPROACH/RISK NOTES:\n{notes}"
        )
        if entities:
            document += (
                "\nOPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the "
                "task_entities array AND reproduce each verbatim inside the prompt body):\n"
                + "\n".join(f"- {e}" for e in entities)
            )
        self._bootstrap_cache[cache_key] = document
        return document

    def _compile_context(self, raw_text: str, traces: list[CallTrace]) -> str:
        """Route raw content through the semantic read; compile ops never see raw."""
        document = self._semantic_read(raw_text, traces)
        if document is None:
            return "[CONTENT BLOCKED BY HIGHER-PRIORITY CONSTRAINTS]"
        return document

    def _compile_approach_context(self, raw_text: str, traces: list[CallTrace]) -> str:
        """Route approach content through semantic compilation explicitly labeled as TASK-02."""
        raw_compiled = self._compile_context(raw_text, traces)
        if raw_compiled.startswith("[CONTENT BLOCKED"):
            return raw_compiled
        prefix = "TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):"
        if prefix in raw_compiled:
            parts = raw_compiled.split("APPROACH/RISK NOTES:")
            task_part = parts[0].replace(prefix, "").strip()
            approach_part = parts[1].strip() if len(parts) > 1 else ""
            combined = "\n".join(filter(None, [task_part, approach_part]))
            return f"APPROACH CONSTRAINT (TASK-02 operative requirement; incorporate per PLAN-08):\n{combined}"
        return f"APPROACH CONSTRAINT (TASK-02 operative requirement; incorporate per PLAN-08):\n{raw_compiled.strip()}"


    def _entity_coverage_missing(self, prompt_body: str, entities: tuple[str, ...]) -> list[str]:
        """Mechanical source-coverage check: every forwarded task entity must
        appear verbatim in the prompt IR. Host-side string presence only -- no
        model judgment, no generation constraint."""
        return [e for e in entities if e not in prompt_body]

    def _enforce_entity_coverage(
        self,
        draft_fn,
        context: dict[str, Any],
        parser,
        entities: tuple[str, ...],
        traces: list[CallTrace],
        phase: str,
    ) -> Any:
        """Call the draft op, then mechanically verify task-entity coverage of
        the prompt body. On a miss, retry once with an operator correction
        appended outside the projection document. Persistent misses are
        published with a workspace event (utility-first: measurable, not
        fatal)."""
        outcome = draft_fn(context, traces, parser=parser)
        if getattr(outcome, "kind", "") == "TASK_BLOCKED_BY_HIGHER_PRIORITY":
            return outcome
        missing = self._entity_coverage_missing(outcome.prompt_body or "", entities)
        if not missing:
            return outcome
        if self.workspace is not None:
            self.workspace.append_event("TASK_ENTITY_COVERAGE_RETRY", {"missing": len(missing)})
        corrected_context = dict(context)
        corrected_context["SUBSTANTIVE_REQUEST"] = (
            context["SUBSTANTIVE_REQUEST"]
            + "\n\nOPERATOR CORRECTION (host-side mechanical check): the following task entities are "
            "missing from the prompt body and MUST appear verbatim, character-for-character: "
            + "; ".join(missing)
        )
        outcome = draft_fn(corrected_context, traces, parser=parser)
        if getattr(outcome, "kind", "") == "TASK_BLOCKED_BY_HIGHER_PRIORITY":
            return outcome
        missing = self._entity_coverage_missing(outcome.prompt_body or "", entities)
        if missing and self.workspace is not None:
            self.workspace.append_event(
                "TASK_ENTITY_COVERAGE_MISSING",
                {"entities": list(missing), "phase": phase},
            )
        return outcome

    def _budget_refusal(self) -> str | None:
        """Policy gate (TARGET_ARCHITECTURE §5): a task that needs a certified result
        is refused when no domain verifier is registered for it and System 1 judges
        it more likely than not to need more steps than the largest budget. Neither
        a sandbox reproduction nor a checker could then certify it here."""
        from pdl_taskmaster.providers.sys1.recipes.execution_profile import BEYOND_BUDGET_REFUSAL_PROBABILITY
        from pdl_taskmaster.verification.output_verifier import OutputVerifier
        from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

        if not self._requires_verified_execution:
            return None
        beyond = float(self._profile_distribution.get("BEYOND_100M_STEPS", 0.0))
        if beyond <= BEYOND_BUDGET_REFUSAL_PROBABILITY:
            return None
        if OutputVerifier().get_checker(self._problem_domain).name != "fallback":
            return None
        largest = max(budget.step_limit for budget in EXECUTION_BUDGETS.values())
        assert self.workspace is not None
        self.workspace.append_event(
            "BUDGET_REFUSAL",
            {"p_beyond_largest_budget": round(beyond, 4), "largest_step_budget": largest},
        )
        return (
            "This request asks for a result that must be certified, and it is more likely than not to need more "
            f"than {largest:,} computation steps, the largest step budget of this environment. No verifier is "
            "available to certify such a result by other means, so an exact answer could not be produced or "
            "checked here and the request was not attempted. A smaller instance, or an explicitly approximate "
            "answer, fits within the environment."
        )

    def _route_execution_profile(self, request: str) -> None:
        """System 1 routes the task to a resource tier (TARGET_ARCHITECTURE §5).

        The tier's fixed budget is what the sandbox enforces and what the solver is
        told. System 1 absent, uncertain or failing leaves the STANDARD budget.
        """
        from pdl_taskmaster.verification.sandbox import DEFAULT_BUDGET, EXECUTION_BUDGETS

        prediction, tier, passed, probabilities = self._predict_profile({"request": request})
        distribution = {k: round(v, 4) for k, v in probabilities.items()}
        self._profile_distribution = dict(probabilities)
        self._execution_budget = EXECUTION_BUDGETS.get(tier, DEFAULT_BUDGET)
        if self._host_execution_tools is None:
            self.available_execution_tools = self.sandbox.describe(self._execution_budget)
        assert self.workspace is not None
        self.workspace.append_event(
            "EXECUTION_PROFILE_ROUTED",
            {
                "predicted_steps": prediction,
                "distribution": distribution,
                "tier": self._execution_budget.tier,
                "passed_gating": passed,
                "step_limit": self._execution_budget.step_limit,
                "timeout_seconds": self._execution_budget.timeout_seconds,
                "memory_mb": self._execution_budget.memory_limit_bytes // (1024 * 1024),
            },
        )

    def _predict_profile(self, state: dict[str, Any]) -> tuple[str | None, str, bool, dict[str, float]]:
        """One ExecutionProfileRecipe decision: (prediction, tier, passed_gating,
        probabilities). System 1 absent or failing yields the STANDARD tier."""
        from pdl_taskmaster.providers.sys1.recipes.execution_profile import ExecutionProfileRecipe

        if self.sys1_client is None or not self.sys1_client.is_configured:
            return None, "STANDARD", False, {}
        recipe = ExecutionProfileRecipe()
        try:
            sys1_request = recipe.build_request({**state, "environment": self.sandbox.decision_state()})
            body, duration_ms = self.sys1_client.call(sys1_request)
            result = recipe.parse_response(body, duration_ms=duration_ms)
            routed = recipe.map_to_wire(result)
        except Exception:
            return None, "STANDARD", False, {}
        return routed["prediction"], routed["tier"], result.passed_gating, dict(result.probabilities)

    def _route_plan_profile(self, prompt_body: str, plan_body: str) -> None:
        """Plan-time routing (TARGET_ARCHITECTURE §5): System 1 predicts the step cost
        of the confirmed procedure. One-way: nothing about the prediction reaches the
        solver except the environment it declares. A usable prediction may raise the
        budget tier routed from the request, never lower it."""
        from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

        prediction, tier, passed, probabilities = self._predict_profile(
            {"request": prompt_body, "procedure": plan_body}
        )
        order = list(EXECUTION_BUDGETS)
        before = self._execution_budget
        raised = passed and tier in EXECUTION_BUDGETS and order.index(tier) > order.index(before.tier)
        if raised:
            self._execution_budget = EXECUTION_BUDGETS[tier]
            if self._host_execution_tools is None:
                self.available_execution_tools = self.sandbox.describe(self._execution_budget)
        assert self.workspace is not None
        self.workspace.append_event(
            "PLAN_PROFILE_ROUTED",
            {
                "predicted_steps": prediction,
                "distribution": {k: round(v, 4) for k, v in probabilities.items()},
                "passed_gating": passed,
                "request_tier": before.tier,
                "plan_tier": tier if passed else None,
                "tier": self._execution_budget.tier,
                "budget_raised": raised,
                "step_limit": self._execution_budget.step_limit,
            },
        )

    def _draft_initial_prompt(
        self,
        substantive_request: str,
        traces: list[CallTrace],
        *,
        protocol_state: str,
    ) -> EngineResponse:
        assert self.workspace is not None
        previous_request = (getattr(self, "_previous_turn", None) or {}).get("request")
        if previous_request:
            # A follow-up refers to the previous request: routing, drafting and the
            # execution source all work from both, never from the follow-up alone
            # (session 20261001-122654: "try a more efficient method" was routed as
            # a standard task at the MINIMAL tier and executed without the data).
            substantive_request = (
                f"{previous_request}\n\nFollow-up from the user, referring to the request above:\n"
                f"{substantive_request}"
            )
        self._source_request = substantive_request
        self.workspace.write_turn_source(substantive_request)
        from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe
        from pdl_taskmaster.verification.checkers.base import ProblemDomain
        requires_verified = False
        if self.sys1_client and self.sys1_client.is_configured:
            try:
                recipe = ProblemClassRecipe()
                sys1_req = recipe.build_request({"request": substantive_request})
                resp_body, dur_ms = self.sys1_client.call(sys1_req)
                res = recipe.parse_response(resp_body, duration_ms=dur_ms)
                if res.passed_gating:
                    requires_verified = (res.verdict == "VERIFIED_EXECUTION")
            except Exception:
                pass
        self._requires_verified_execution = requires_verified
        self._route_execution_profile(substantive_request)
        # GUARD-02: the harness never infers a problem domain from request text.
        # The domain stays GENERAL unless the witness itself declares a typed domain.
        self._problem_domain = ProblemDomain.GENERAL if requires_verified else None

        if self.workspace is not None:
            self.workspace.append_event(
                "PROBLEM_CLASS_CLASSIFIED",
                {
                    "requires_verified_execution": self._requires_verified_execution,
                    "domain": self._problem_domain.value if self._problem_domain else None,
                },
            )
        budget_refusal = self._budget_refusal()
        if budget_refusal is not None:
            return self._refuse(budget_refusal, traces, "budget")
        # Protocol v2: raw content is read by BOOTSTRAP_ANALYSIS only; the
        # compile op receives the sanitized compiled analysis.
        compiled = self._semantic_read(substantive_request, traces)
        if compiled is None:
            self.workspace.append_event("PROTOCOL_BLOCKED", {"phase": "bootstrap"})
            return self._refuse(getattr(self, "_blocked_response", None), traces, "bootstrap")
        entities = self._task_entities_cache.get((substantive_request, self._previous_deliverable), ())
        self._active_task_entities = entities

        def _draft_call(ctx: dict[str, Any], tr: list[CallTrace], parser) -> Any:
            return self._call("DRAFT_PROMPT", ctx, tr, parser=parser)

        outcome = self._enforce_entity_coverage(
            _draft_call,
            {
                "HOST_PROTOCOL_STATE": protocol_state,
                "SUBSTANTIVE_REQUEST": compiled,
            },
            self.bridge.parse_prompt_draft,
            entities,
            traces,
            phase="draft_prompt",
        )
        if outcome.kind == "TASK_BLOCKED_BY_HIGHER_PRIORITY":
            self.workspace.append_event(
                "PROTOCOL_BLOCKED",
                {"phase": "prompt_draft", "blocking_basis": outcome.blocking_basis},
            )
            return self._refuse(outcome.response, traces, "prompt_draft")
        assert outcome.prompt_body is not None
        from pdl_taskmaster.verification.plan_soundness import validate_plan_soundness
        prompt_lint = validate_plan_soundness(outcome.prompt_body)
        if not prompt_lint.valid:
            self.workspace.append_event("PROMPT_LINT_RETRY", {"violations": prompt_lint.violations})
            redraft = self._call(
                "DRAFT_PROMPT",
                {"HOST_PROTOCOL_STATE": protocol_state, "SUBSTANTIVE_REQUEST": compiled},
                traces,
                parser=self.bridge.parse_prompt_draft,
                operator_correction="OPERATOR CORRECTION: " + prompt_lint.feedback,
            )
            if redraft.kind == "TASK_BLOCKED_BY_HIGHER_PRIORITY":
                self.workspace.append_event(
                    "PROTOCOL_BLOCKED",
                    {"phase": "prompt_draft", "blocking_basis": redraft.blocking_basis},
                )
                return self._refuse(redraft.response, traces, "prompt_draft")
            if redraft.prompt_body is not None:
                outcome = redraft
                if not validate_plan_soundness(outcome.prompt_body).valid:
                    self.workspace.append_event("PROMPT_LINT_UNRESOLVED", {})
        self.controller = self._bind_new_controller(self.workspace)
        approach_source = substantive_request if outcome.approach_handoff == "CARRY_SOURCE_TO_PLAN" else None
        self.controller.commit_initial_prompt(outcome.prompt_body, approach_source)
        self._publish_prompt()
        return EngineResponse(presentation.prompt_artifact(outcome.prompt_body), traces)

    def _sync_review_edit(self) -> None:
        assert self.controller is not None and self.workspace is not None
        state = self.controller.state
        if state.stage == Stage.PROMPT_REVIEW and state.current_prompt:
            body = self.workspace.sync_unconfirmed_edit("prompt", state.current_prompt.artifact_id, state.current_prompt.body)
            if body != state.current_prompt.body:
                self.controller.replace_current_unconfirmed_body("prompt", body)
        elif state.stage == Stage.PLAN_REVIEW and state.current_plan:
            self.workspace.validate_confirmed_artifact(
                "prompt", state.current_prompt.artifact_id, state.current_prompt.body  # type: ignore[union-attr]
            )
            body = self.workspace.sync_unconfirmed_edit("plan", state.current_plan.artifact_id, state.current_plan.body)
            if body != state.current_plan.body:
                self.controller.replace_current_unconfirmed_body("plan", body)

    def _activation(self, user_message: str, traces: list[CallTrace]) -> EngineResponse | None:
        # S4 cross-turn chaining (ADR-0008 §4): when the SAME session's prior
        # turn reached a terminal stage and the user issues a new command,
        # continue in the same workspace under the next turn id. Only the prior
        # turn's confirmed deliverable carries forward; drafts, rejected plans,
        # and review dialogue are structurally unreachable in the new turn.
        self.refused = False
        prior = self.workspace
        if (
            prior is not None
            and prior.turn_id is not None
            and self.controller is not None
            and self.controller.state.stage in {Stage.CLOSED_SUCCESS, Stage.CLOSED_CANCELLED}
        ):
            prior_status = prior.read_turn_status(prior.turn_id).get("status")
            if prior_status == "ACTIVE":
                prior.mark_turn_status(
                    "CLOSED_SUCCESS"
                    if self.controller.state.stage == Stage.CLOSED_SUCCESS
                    else "CLOSED_CANCELLED"
                )
            previous = prior.previous_turn()
            prior.start_turn(prior.next_turn_id())
            self.workspace = prior
            self._previous_turn = previous
            self._previous_deliverable = _previous_turn_reference(previous)
            self._source_request = None
            self.workspace.append_event(
                "TURN_CHAINED",
                {
                    "turn_id": prior.turn_id,
                    "previous_deliverable": self._previous_deliverable is not None,
                    "previous_status": (previous or {}).get("status"),
                    "previous_request": bool((previous or {}).get("request")),
                },
            )
        else:
            self.workspace = self._new_workspace()
            self._previous_turn = None
            self._previous_deliverable = None
            self._source_request = None
        observation = observe_invocation(user_message)
        if observation.explicit:
            self.workspace.append_event(
                "EXPLICIT_INVOCATION_OBSERVED",
                {"substantive_request_present": bool(observation.substantive_request)},
            )
            routed = self._s1_activation(observation.substantive_request)
            if routed is not None:
                route, refusal = routed
                if route == "BLOCKED_BY_HIGHER_PRIORITY":
                    return self._refuse(refusal, traces, "activation")
                # BYPASS / PROTOCOL_DISCUSSION: a direct answer, no protocol instance (§3).
                self.workspace.append_event("DIRECT_ANSWER_ROUTED", {"route": route})
                if route == "PROTOCOL_DISCUSSION":
                    return self._discuss_protocol(observation.substantive_request, traces)
                return EngineResponse(None, traces, bypass=True)
            return self._draft_initial_prompt(
                observation.substantive_request,
                traces,
                protocol_state="ACTIVE_BY_EXPLICIT_INVOCATION",
            )
        decision = self._call(
            "INTERPRET_ACTIVATION", {"RAW_USER_MESSAGE": user_message}, traces,
            parser=self.bridge.parse_activation,
        )
        if decision.route == ActivationRoute.BLOCKED_BY_HIGHER_PRIORITY:
            return self._refuse(decision.response, traces, "activation")
        if decision.route == ActivationRoute.BYPASS:
            return EngineResponse(None, traces, bypass=True)
        if decision.route == ActivationRoute.PROTOCOL_DISCUSSION:
            return self._discuss_protocol(user_message, traces)
        return self._draft_initial_prompt(
            user_message.strip(),
            traces,
            protocol_state="ACTIVE_BY_SEMANTIC_REQUEST",
        )

    def _draft_plan(self, transition: Transition, traces: list[CallTrace]) -> EngineResponse:
        assert self.controller is not None and self.workspace is not None
        prompt = self.controller.state.current_prompt
        assert prompt is not None
        self.workspace.validate_confirmed_artifact("prompt", prompt.artifact_id, prompt.body)
        _, prompt_body = self.workspace.read_artifact("prompt")
        carried_raw = self.workspace.read_approach_sources()
        if carried_raw != self.controller.state.approach_sources:
            raise WorkspaceError("approach_source_handoff")
        carried = [self._compile_approach_context(s, traces) for s in carried_raw]
        body = self._linted_call(
            "DRAFT_PLAN",
            {
                "CONFIRMED_PROMPT_BODY": prompt_body,
                "CARRIED_APPROACH_SOURCES": carried,
            },
            traces,
            parser=self.bridge.parse_plan_body,
            artifact="PLAN",
        )
        self.controller.commit_plan(body)
        self._publish_plan()
        return EngineResponse(presentation.plan_artifact(body), traces)

    def _linted_call(
        self, operation: str, context: dict[str, Any], traces: list[CallTrace], *, parser: Any, artifact: str
    ) -> str:
        """Call an operation that returns pseudocode and lint the body (plan_soundness).
        A violation gets exactly one redraft carrying the finding; a residual
        violation is recorded and the body stands for the user's review."""
        from pdl_taskmaster.verification.plan_soundness import validate_plan_soundness

        assert self.workspace is not None
        body = self._call(operation, context, traces, parser=parser)
        lint = validate_plan_soundness(body)
        if lint.valid:
            return body
        self.workspace.append_event(
            f"{artifact}_LINT_RETRY", {"operation": operation, "violations": lint.violations}
        )
        body = self._call(
            operation, context, traces, parser=parser, operator_correction="OPERATOR CORRECTION: " + lint.feedback
        )
        residual = validate_plan_soundness(body)
        if not residual.valid:
            self.workspace.append_event(
                f"{artifact}_LINT_UNRESOLVED", {"operation": operation, "violations": residual.violations}
            )
        return body

    def _revise_prompt(self, transition: Transition, traces: list[CallTrace]) -> EngineResponse:
        assert self.controller is not None and self.workspace is not None
        prompt = self.controller.state.current_prompt
        assert prompt is not None
        meta, prompt_body = self.workspace.read_artifact("prompt")
        if meta.get("artifact_id") != prompt.artifact_id or prompt_body != prompt.body:
            raise WorkspaceError("prompt_revision_handoff")
        change_id = transition.payload["change_id"]
        had_plan = self.controller.state.current_plan is not None
        try:
            body = self._linted_call(
                "REVISE_PROMPT",
                {
                    "CURRENT_PROMPT_BODY": prompt_body,
                    # Protocol v2: raw change source routed through the
                    # semantic read; compile op receives the compiled form.
                    "TASK_CHANGE_SOURCE": self._compile_context(
                        transition.payload["task_change_source"], traces
                    ),
                },
                traces,
                parser=self.bridge.parse_prompt_body,
                artifact="PROMPT",
            )
            self.controller.commit_prompt_revision(change_id, body)
            # Mechanical coverage regression check on revisions: entities the
            # draft carried must survive revision. Event-only in v1 (no loop).
            missing = self._entity_coverage_missing(body, self._active_task_entities)
            if missing and self.workspace is not None:
                self.workspace.append_event(
                    "TASK_ENTITY_COVERAGE_MISSING",
                    {"entities": list(missing), "phase": "revise_prompt"},
                )
        except Exception:
            self.controller.abort_pending_change(change_id)
            raise
        if had_plan:
            self.workspace.invalidate_artifact("plan", "prompt_revision")
        self._publish_prompt()
        return EngineResponse(presentation.prompt_artifact(body), traces)

    def _revise_plan(self, transition: Transition, traces: list[CallTrace]) -> EngineResponse:
        assert self.controller is not None and self.workspace is not None
        prompt = self.controller.state.current_prompt
        plan = self.controller.state.current_plan
        assert prompt is not None and plan is not None
        self.workspace.validate_confirmed_artifact("prompt", prompt.artifact_id, prompt.body)
        prompt_body = self.workspace.read_artifact("prompt")[1]
        plan_meta, plan_body = self.workspace.read_artifact("plan")
        if plan_meta.get("artifact_id") != plan.artifact_id or plan_body != plan.body:
            raise WorkspaceError("plan_revision_handoff")
        change_id = transition.payload["change_id"]
        carried_raw = self.workspace.read_approach_sources()
        if carried_raw != self.controller.state.approach_sources:
            raise WorkspaceError("approach_source_handoff")
        try:
            body = self._linted_call(
                "REVISE_PLAN",
                {
                    "CONFIRMED_PROMPT_BODY": prompt_body,
                    "CURRENT_PLAN_BODY": plan_body,
                    "CARRIED_APPROACH_SOURCES": [
                        *map(lambda s: self._compile_approach_context(s, traces), carried_raw),
                        self._compile_approach_context(transition.payload["approach_change_source"], traces),
                    ],
                },
                traces,
                parser=self.bridge.parse_plan_body,
                artifact="PLAN",
            )
            self.controller.commit_plan_revision(change_id, body)
        except Exception:
            self.controller.abort_pending_change(change_id)
            raise
        self._publish_plan()
        return EngineResponse(presentation.plan_artifact(body), traces)

    def _execute(self, transition: Transition, traces: list[CallTrace]) -> EngineResponse:
        """Phases 4 and 5 (TARGET_ARCHITECTURE §3): one EXECUTE call, deterministic
        verification, at most one repair carrying factual findings, then close."""
        assert self.controller is not None and self.workspace is not None
        if not self.controller.can_execute():
            raise ControllerError("execute_gate")
        prompt = self.controller.state.current_prompt
        plan = self.controller.state.current_plan
        assert prompt is not None and plan is not None
        self.workspace.validate_confirmed_artifact("prompt", prompt.artifact_id, prompt.body)
        self.workspace.validate_confirmed_artifact("plan", plan.artifact_id, plan.body)
        prompt_body = self.workspace.read_artifact("prompt")[1]
        plan_body = self.workspace.read_artifact("plan")[1]

        from pdl_taskmaster.runtime.result_ir import render_instructions

        # Source data (AUTH-04): user-supplied execution input, else the original
        # request, passed through the same quarantine sanitizer as every compile input.
        supplied_raw = transition.payload.get("execution_input_source") or self._source_request
        supplied = compile_bootstrap_output(supplied_raw, supplied_raw)[0].strip() if supplied_raw else None

        verified = self._requires_verified_execution
        result_ir_mode = verified or os.environ.get("PDLT_RESULT_IR") == "1"
        requirements: list[str] = []  # RESULT_STANDARD RS-02: not derived or rendered
        task_inputs: list[str] = []
        if self._previous_deliverable:
            task_inputs.append(self._previous_deliverable)
        if result_ir_mode:
            # The previous turn is reference only: it is never an evidence path and
            # its Result IR is never carried into this turn's instructions.
            evidence_paths = ["execution://body"] + (["execution://witness"] if verified else [])
            channel = render_instructions(
                requirements,
                repo_root=self.repo_root,
                evidence_paths=evidence_paths,
                requires_verified_execution=verified,
            )
            task_inputs.append(channel)
        execute_context = {
            "CONFIRMED_PROMPT_BODY": prompt_body,
            "CONFIRMED_PLAN_BODY": plan_body,
            "REQUIRED_TASK_INPUTS": "\n\n".join(task_inputs) or None,
            "SUPPLIED_EXECUTION_INPUT_SOURCE": supplied,
            "AVAILABLE_EXECUTION_TOOLS": self.available_execution_tools,
        }

        self._route_plan_profile(prompt_body, plan_body)
        execute_context["AVAILABLE_EXECUTION_TOOLS"] = self.available_execution_tools
        if self.draft_execute:
            brief = self._draft_execution_brief(execute_context, traces)
            if brief:
                # The model's own draft (GUARD-01: no harness feedback), drafted once.
                execute_context["REQUIRED_TASK_INPUTS"] = (
                    (execute_context["REQUIRED_TASK_INPUTS"] + "\n\n" if execute_context["REQUIRED_TASK_INPUTS"] else "")
                    + "EXECUTION BRIEF (your own draft for this task, written before this call):\n" + brief
                )
        stop_on_failure = self.max_repairs == 0
        repairs_allowed = self._execution_budget.repairs if self.max_repairs is None else self.max_repairs
        repairs_used = 0
        unmeasured_repairs = 0  # repairs after an attempt that ran no program (at most one)
        outcome, errors, final_body, ran_program = self._execute_attempt(
            execute_context, traces, prompt_body, plan_body, requirements, result_ir_mode,
        )
        # Bounded repair: at most the routed tier's number of re-executions (or the
        # user's --max-repairs), each carrying only the latest factual host findings
        # through the operator-correction channel (never as approach sources). The
        # tier's repairs are for attempts the sandbox measured: one repair after an
        # attempt that ran no program at all does not use them up. With
        # --max-repairs 0 nothing is retried: the first failure closes the run.
        attempt_findings = [list(errors)]  # per attempt, for the published failure record
        while outcome.kind == "RESULT" and errors and not stop_on_failure and (
            repairs_used < repairs_allowed or (not ran_program and unmeasured_repairs < UNMEASURED_REPAIRS)
        ):
            counted = ran_program or unmeasured_repairs >= UNMEASURED_REPAIRS
            if counted:
                repairs_used += 1
            else:
                unmeasured_repairs += 1
            self.workspace.append_event(
                "VERIFICATION_REPAIR",
                {"errors": errors, "codes": finding_codes(errors), "repair": repairs_used + unmeasured_repairs,
                 "counted": counted, "repairs_allowed": repairs_allowed},
            )
            outcome, errors, final_body, ran_program = self._execute_attempt(
                execute_context, traces, prompt_body, plan_body, requirements, result_ir_mode,
                correction=(
                    "OPERATOR CORRECTION (host-side verification findings): the previous "
                    "deliverable failed these checks:\n" + "\n".join(f"- {e}" for e in errors)
                ),
            )
            attempt_findings.append(list(errors))
        self.workspace.append_event(
            "EXECUTION_ATTEMPTS",
            {"attempts": 1 + repairs_used + unmeasured_repairs, "repairs_used": repairs_used,
             "unmeasured_repairs": unmeasured_repairs, "repairs_allowed": repairs_allowed,
             "tier": self._execution_budget.tier},
        )

        if outcome.kind == "REQUEST_INPUT":
            assert outcome.expected_type is not None and outcome.description is not None
            self.controller.request_execution_input(outcome.expected_type, outcome.description)
            self.workspace.publish_execution_outcome(
                outcome.kind,
                outcome.body,
                {"expected_type": outcome.expected_type, "description": outcome.description},
            )
            return EngineResponse(outcome.body, traces)
        if outcome.kind == "BLOCKED_BY_HIGHER_PRIORITY":
            self.controller.cancel()
            self.workspace.publish_execution_outcome(outcome.kind, outcome.body)
            return EngineResponse(outcome.body, traces, closed=True)
        if errors:
            self.workspace.append_event("VERIFICATION_FAILED", {"errors": errors, "codes": finding_codes(errors)})
            # Every attempt is on the record: a transcript shows only the final body.
            history = "\n".join(
                f"Attempt {n}: {', '.join(finding_codes(found)) if found else 'passed verification'}"
                for n, found in enumerate(attempt_findings, 1)
            )
            final_body = (
                "UNVERIFIED ANSWER: Substantive verification was not completed after repair attempts. "
                f"Reason: {'; '.join(errors)}\n\n{history}\n\nCandidate deliverable:\n{final_body}"
            )
            self.controller.cancel()
            if self.workspace.turn_id is not None:
                self.workspace.mark_turn_status("CLOSED_CANCELLED")
            self.workspace.publish_execution_outcome(
                "VERIFICATION_FAILED", final_body, {"errors": errors, "codes": finding_codes(errors)}
            )
            return EngineResponse(final_body, traces, closed=True)
        result_body_hash = hashlib.sha256(final_body.encode("utf-8")).hexdigest()
        self.controller.complete_success(result_body_hash)
        if self.workspace.turn_id is not None:
            self.workspace.mark_turn_status("CLOSED_SUCCESS", deliverable_sha256=result_body_hash)
        self.workspace.publish_execution_outcome(
            outcome.kind,
            final_body,
            {
                "source_prompt_id": prompt.artifact_id,
                "source_plan_id": plan.artifact_id,
                "result_body_hash": result_body_hash,
                "confirmed_prompt_hash": hashlib.sha256(prompt.body.encode("utf-8")).hexdigest(),
                "confirmed_plan_hash": hashlib.sha256(plan.body.encode("utf-8")).hexdigest(),
            },
        )
        return EngineResponse(final_body, traces, closed=True)

    def _draft_execution_brief(self, execute_context: dict[str, Any], traces: list[CallTrace]) -> str | None:
        """DRAFT_EXECUTE (A/B option): the model drafts how its deliverable will meet
        the confirmed prompt and plan within the stated environment. A draft that
        fails to parse is skipped, never retried into EXECUTE."""
        assert self.workspace is not None
        values = {key: execute_context.get(key) for key in (
            "CONFIRMED_PROMPT_BODY", "CONFIRMED_PLAN_BODY", "REQUIRED_TASK_INPUTS",
            "AVAILABLE_EXECUTION_TOOLS", "SUPPLIED_EXECUTION_INPUT_SOURCE",
        )}
        values["HOST_PROTOCOL_STATE"] = "EXECUTION_DRAFT"
        try:
            draft = self._call("DRAFT_EXECUTE", values, traces, parser=self.bridge.parse_execution_draft)
        except Exception as exc:
            if not _is_wire_failure(exc):
                raise
            self.workspace.append_event("EXECUTION_BRIEF_SKIPPED", {"reason": str(exc)})
            return None
        if draft.kind != "RESULT" or not draft.brief_body.strip():
            self.workspace.append_event("EXECUTION_BRIEF_SKIPPED", {"reason": draft.kind})
            return None
        self.workspace.append_event("EXECUTION_BRIEF_DRAFTED", {"chars": len(draft.brief_body)})
        return draft.brief_body.strip()

    def _execute_attempt(
        self,
        execute_context: dict[str, Any],
        traces: list[CallTrace],
        prompt_body: str,
        plan_body: str,
        requirements: list[str],
        result_ir_mode: bool,
        *,
        correction: str | None = None,
    ) -> tuple[Any, list[str], str, bool]:
        """One EXECUTE call plus Phase 5 verification: (outcome, findings, body to
        publish, ran_program). Exactly one model call: a response cut off at the
        output-token cap or one that does not parse is a counted failed attempt
        with a registry finding, never a hidden retry (each attempt cost up to two
        calls before, so a repair could cost four)."""
        try:
            outcome = self.bridge.parse_execution(self._call("EXECUTE", execute_context, traces,
                                                             operator_correction=correction))
        except Exception as exc:
            limit = getattr(exc, "output_limit", None)
            if limit is None and not _is_wire_failure(exc):
                raise
            assert self.workspace is not None
            if limit is not None:
                self.workspace.append_event("OUTPUT_LIMIT_REACHED", {"limit": limit})
                finding = Finding("OUTPUT_LIMIT_REACHED", limit=limit)
            else:
                self.workspace.append_event("EXECUTE_WIRE_FAILURE", {"reason": str(exc)})
                finding = Finding("OUTPUT_MALFORMED", reason=str(exc))
            return _FailedExecution(), [finding], "", True
        if outcome.kind != "RESULT":
            return outcome, [], outcome.body, False
        errors, final_body = self._verify_result(outcome, prompt_body, plan_body, requirements, result_ir_mode)
        return outcome, errors, final_body, getattr(self, "_last_programs_run", 0) > 0

    def _run_deliverable_code(self, body: str) -> tuple[dict[str, Any] | None, list[str]]:
        """Run every declared Python block in the session sandbox.

        Returns the host-reproduced witness (the last block that printed one wins)
        and one factual finding per block that did not run cleanly.
        """
        assert self.workspace is not None
        witness: dict[str, Any] | None = None
        failures: list[str] = []
        self._last_program_outputs: list[str] = []
        self._last_programs_run = 0
        for index, block in enumerate(_python_blocks(body), 1):
            self._last_programs_run += 1
            run = self.sandbox.run_code(
                block,
                timeout=self._execution_budget.timeout_seconds,
                memory_limit=self._execution_budget.memory_limit_bytes,
                step_limit=self._execution_budget.step_limit,
            )
            self._log_sandbox_session()
            self.workspace.append_event(
                "SANDBOX_RUN",
                {
                    "block": index,
                    "backend": self.sandbox.backend_name,
                    "tier": self._execution_budget.tier,
                    "exit_code": run.exit_code,
                    "step_budget_exceeded": run.step_budget_exceeded,
                    "steps_used": run.steps_used,
                    "timed_out": run.timed_out,
                    "oom_killed": run.oom_killed,
                    "duration_ms": round(run.duration_ms, 1),
                },
            )
            if not run.success:
                budget = self._execution_budget
                if run.step_budget_exceeded:
                    failures.append(Finding("STEP_BUDGET_EXCEEDED", block=index, step_limit=budget.step_limit))
                elif run.timed_out:
                    failures.append(Finding("WALL_CLOCK_EXCEEDED", block=index, timeout_seconds=budget.timeout_seconds))
                elif run.oom_killed:
                    failures.append(Finding("MEMORY_EXCEEDED", block=index,
                                            memory_mb=budget.memory_limit_bytes // (1024 * 1024)))
                else:
                    stderr = _stderr_summary(run.stderr)
                    failures.append(Finding("PROGRAM_FAILED", block=index, exit_code=run.exit_code, stderr=stderr))
                continue
            candidate = _parse_sandbox_witness(run.stdout)
            if candidate is not None:
                witness = candidate
            else:
                tail = " / ".join((run.stdout or "").strip().splitlines()[-3:])[:300]
                self._last_program_outputs.append(f"python block {index} exited 0" + (f" and printed: {tail}" if tail else " and printed nothing"))
        return witness, failures

    def _log_sandbox_session(self) -> None:
        """One SANDBOX_SESSION event per workspace: the backend that confines the
        programs and the session root they run under (outside every workspace)."""
        info = self.sandbox.session_info
        if info is None or self._sandbox_session_logged is self.workspace:
            return
        assert self.workspace is not None
        self.workspace.append_event("SANDBOX_SESSION", dict(info))
        self._sandbox_session_logged = self.workspace

    def close(self) -> None:
        """Release session-scoped resources (the sandbox session). Idempotent."""
        self.sandbox.close()

    def _payload_token_findings(self, body: str) -> list[str]:
        """EXEC-04: a deliverable carries no payload token from the untrusted source.
        The finding counts the tokens and never repeats them (SEM-06)."""
        from pdl_taskmaster.runtime.quarantine import echoed_payload_tokens

        echoed = echoed_payload_tokens(self._source_request, body)
        if not echoed:
            return []
        assert self.workspace is not None
        self.workspace.append_event("PAYLOAD_TOKENS_IN_DELIVERABLE", {"count": len(echoed)})
        return [Finding("PAYLOAD_TOKEN_REPEATED", count=len(echoed))]

    def _verify_result(
        self,
        outcome: Any,
        prompt_body: str,
        plan_body: str,
        requirements: list[str],
        result_ir_mode: bool,
    ) -> tuple[list[str], str]:
        """Phase 5: deterministic contract checks over a RESULT (ADR-0018, §2.1).

        Returns the factual findings (empty when valid) and the body to publish.
        """
        from dataclasses import replace

        from pdl_taskmaster.runtime.result_ir import validate_result_ir
        from pdl_taskmaster.verification.output_verifier import OutputVerifier

        assert self.workspace is not None
        body = outcome.body
        verified = self._requires_verified_execution
        sandbox_witness, run_failures = self._run_deliverable_code(body)
        payload_findings = self._payload_token_findings(body)
        if not result_ir_mode:
            # Standard execution: code runs are telemetry; code that needs an
            # unavailable capability is not a contract failure.
            return payload_findings, body

        errors: list[str] = list(payload_findings)
        # RS-01: the Result IR travels only in the structured field; the deliverable
        # text is never scanned for it. An absent IR claims nothing: a witness the
        # program printed still counts.
        ir = dict(outcome.result_ir) if isinstance(getattr(outcome, "result_ir", None), dict) else {}
        citations: list[str] = []
        ir_errors, _ = validate_result_ir(
            ir, self.workspace.path, requirements, execution_body=body, citations=citations
        )
        errors.extend(Finding("RESULT_IR_INVALID", detail=e) for e in ir_errors)
        if citations:
            # The model's bookkeeping about its deliverable (verbatim quotes, section
            # markers, one reconciliation per requirement) is recorded, not blocking:
            # it is not the deliverable's correctness.
            self.workspace.append_event("RESULT_IR_CITATION_FINDINGS", {"findings": citations})

        if verified:
            verifier = OutputVerifier()
            constraints = {
                "prompt_body": prompt_body,
                "plan_body": plan_body,
                "requirements": requirements,
                "domain": self._problem_domain,
            }
            model_witness = ir.get("witness")
            declared_incomplete = (  # RS-01: no witness, and what was not obtained is recorded
                model_witness is None and sandbox_witness is None and bool(ir.get("open_defects"))
            )
            if declared_incomplete:
                # A witness certifies a claimed result. A deliverable that declares
                # requirements open (with the defect recorded) claims none, so there
                # is nothing to certify; demanding a witness would force fabrication.
                errors.extend(run_failures)
                if not getattr(self, "_last_programs_run", 0):
                    # "Could not be obtained" must rest on an attempt: with no program
                    # run, an open requirement is an unattempted one, not an honest limit.
                    errors.append(Finding("INCOMPLETE_WITHOUT_ATTEMPT"))
                self.workspace.append_event(
                    "VERIFICATION_NOT_APPLICABLE",
                    {"reason": "declared_incomplete", "open_defects": len(ir["open_defects"]),
                     "programs_run": getattr(self, "_last_programs_run", 0)},
                )
            elif sandbox_witness is not None:
                verdict = verifier.check(sandbox_witness, constraints, domain=self._problem_domain, body=body)
                if verdict.valid:
                    sandbox_witness["provisional"] = False
                    if model_witness is not None and model_witness != sandbox_witness:
                        self.workspace.append_event("WITNESS_OVERRIDDEN_BY_SANDBOX", {})
                    ir["witness"] = sandbox_witness
            else:
                errors.extend(run_failures)
                verdict = verifier.check(model_witness, constraints, domain=self._problem_domain, body=body)
                claims_search = isinstance(model_witness, dict) and model_witness.get("polarity") == "negative" and (
                    model_witness.get("basis", "search") == "search"
                    or bool(model_witness.get("search_exhausted"))
                    or model_witness.get("nodes_explored") is not None
                )
                if verdict.valid and claims_search:
                    # A claim of computation must come from computation: an exhausted
                    # search (even one labelled a proof) that no program run by the
                    # host produced is not evidence.
                    verdict = replace(verdict, valid=False, diagnostic="SEARCH_CLAIM_UNREPRODUCED")
                elif verdict.valid:
                    ir["witness"]["provisional"] = True
                    verdict = replace(verdict, provisional=True)
            if declared_incomplete:
                pass
            elif verdict.valid:
                self.workspace.append_event(
                    "VERIFICATION_PASSED",
                    {
                        # §2.1: provisional means no sandbox run reproduced the witness.
                        "provisional": sandbox_witness is None,
                        "sandbox_reproduced": sandbox_witness is not None,
                        "domain_checked": not verdict.provisional,
                        "details": verdict.details,
                    },
                )
            elif verdict.diagnostic == "SEARCH_CLAIM_UNREPRODUCED":
                errors.append(Finding("SEARCH_CLAIM_UNREPRODUCED"))
            elif sandbox_witness is not None:
                # A program ran and printed a WITNESS line; the line itself fails the check.
                errors.append(Finding(
                    "WITNESS_INVALID",
                    diagnostic=f"the WITNESS line printed by the program does not check: {verdict.diagnostic}",
                ))
            elif model_witness is None:
                outputs = getattr(self, "_last_program_outputs", [])
                observation = (
                    "; ".join(outputs) + "; no line of the form `WITNESS: <json>` was printed."
                    if outputs else "the deliverable contains no program that ran successfully."
                )
                diagnostic = str(verdict.diagnostic).rstrip(".") + "."
                errors.append(Finding("WITNESS_NOT_PRINTED", diagnostic=diagnostic, host_observation=observation))
            else:
                errors.append(Finding("WITNESS_INVALID", diagnostic=verdict.diagnostic))

        if errors:
            return errors, body
        self.workspace.append_event("RESULT_IR_VALIDATED", {"ir": ir})
        return [], _attach_result_ir(body, ir)

    def _discuss_protocol(self, question: str, traces: list[CallTrace]) -> EngineResponse:
        """A protocol question outside any instance: answered directly, no instance opened."""
        return EngineResponse(self._call(
            "ANSWER_PROTOCOL_DISCUSSION",
            {
                "RAW_PROTOCOL_QUESTION": question,
                "CURRENT_STAGE_CLASS": None,
                "BOUND_REVIEW_SUBJECT_KIND": None,
                "BOUND_REVIEW_SUBJECT_BODY": None,
            },
            traces,
            parser=self.bridge.parse_protocol_discussion,
        ), traces, bypass=True)

    def _answer_protocol(self, user_message: str, traces: list[CallTrace]) -> EngineResponse:
        assert self.controller is not None
        kind, body = self.controller.review_subject()
        return EngineResponse(self._call(
            "ANSWER_PROTOCOL_DISCUSSION",
            {
                "RAW_PROTOCOL_QUESTION": user_message,
                "CURRENT_STAGE_CLASS": self.controller.state.stage.value,
                "BOUND_REVIEW_SUBJECT_KIND": kind,
                "BOUND_REVIEW_SUBJECT_BODY": body,
            },
            traces,
            parser=self.bridge.parse_protocol_discussion,
        ), traces)

    def _apply_transition(self, transition: Transition, user_message: str, traces: list[CallTrace]) -> EngineResponse:
        if transition.action == NextAction.DRAFT_PLAN:
            return self._draft_plan(transition, traces)
        if transition.action == NextAction.REVISE_PROMPT:
            return self._revise_prompt(transition, traces)
        if transition.action == NextAction.REVISE_PLAN:
            return self._revise_plan(transition, traces)
        if transition.action == NextAction.EXECUTE:
            return self._execute(transition, traces)
        if transition.action == NextAction.ANSWER_PROTOCOL:
            return self._answer_protocol(user_message, traces)
        if transition.action == NextAction.DEFER_SUBSTANTIVE:
            return EngineResponse(presentation.deferred_substantive(), traces)
        if transition.action == NextAction.REQUEST_REVIEW_CLARIFICATION:
            return EngineResponse(presentation.review_clarification(), traces)
        if transition.action == NextAction.SHOW_CURRENT_PROMPT:
            assert self.controller is not None and self.workspace is not None
            prompt = self.controller.state.current_prompt
            assert prompt is not None
            self.workspace.publish_approach_sources(list(self.controller.state.approach_sources))
            return EngineResponse(presentation.prompt_artifact(self.workspace.read_artifact("prompt")[1]), traces)
        if transition.action == NextAction.CLOSED:
            assert self.workspace is not None
            self.workspace.append_event("PROTOCOL_CLOSED", {"reason": "cancelled"})
            return EngineResponse(presentation.cancelled(), traces, closed=True)
        if transition.action == NextAction.START_NEW_INSTANCE:
            new_task = transition.payload["new_task_source"]
            assert self.workspace is not None
            self.workspace.append_event("PROTOCOL_CLOSED", {"reason": "new_task"})
            self.workspace = self._new_workspace()
            self.controller = None
            return self._draft_initial_prompt(
                new_task,
                traces,
                protocol_state="ACTIVE_FRESH_INSTANCE_FROM_REVIEW",
            )
        raise ControllerError(f"transition:{transition.action.value}")

    def handle_explicit_review(self, intent: Intent, feedback: str | None = None) -> EngineResponse:
        """Directly apply a review intent without LLM interpretation overhead (fast-path)."""
        traces: list[CallTrace] = []
        if self.workspace is None:
            raise WorkspaceError("active_controller_without_workspace")
        if self.controller is None:
            raise ControllerError("user_message_stage")
        # Durability (ADR-0009 workflow): interrupted internal transitions are
        # re-driven by explicit user input instead of bricking the epoch.
        if self.controller.state.stage == Stage.PLAN_REQUIRED:
            return self._draft_plan(Transition(NextAction.DRAFT_PLAN, {}), traces)
        if self.controller.state.stage == Stage.EXECUTION_READY:
            return self._execute(Transition(NextAction.EXECUTE, {}), traces)
        if self.controller.state.stage not in {Stage.PROMPT_REVIEW, Stage.PLAN_REVIEW, Stage.WAITING_INPUT}:
            raise ControllerError("user_message_stage")

        self._sync_review_edit()
        previous_stage = self.controller.state.stage
        decision = ReviewDecision(intent=intent)
        msg = feedback or ""
        transition = self.controller.apply_review_decision(decision, msg)
        if decision.intent == Intent.ACCEPT_CURRENT:
            if previous_stage == Stage.PROMPT_REVIEW:
                prompt = self.controller.state.current_prompt
                assert prompt is not None
                self.workspace.mark_artifact_confirmed("prompt", prompt.artifact_id)
            elif previous_stage == Stage.PLAN_REVIEW:
                plan = self.controller.state.current_plan
                assert plan is not None
                self.workspace.mark_artifact_confirmed("plan", plan.artifact_id)
        if decision.intent == Intent.REVISE_APPROACH and previous_stage == Stage.PROMPT_REVIEW:
            self.workspace.publish_approach_sources(list(self.controller.state.approach_sources))
        return self._apply_transition(transition, msg, traces)

    def handle_user_message(self, user_message: str) -> EngineResponse:
        traces: list[CallTrace] = []
        if self.controller is None or self.controller.state.stage in {Stage.CLOSED_SUCCESS, Stage.CLOSED_CANCELLED}:
            return self._activation(user_message, traces) or EngineResponse(None, traces, bypass=True)

        if self.workspace is None:
            raise WorkspaceError("active_controller_without_workspace")
        # Durability (ADR-0009 workflow): interrupted internal transitions are
        # re-driven by any user input instead of bricking the epoch.
        if self.controller.state.stage == Stage.PLAN_REQUIRED:
            return self._draft_plan(Transition(NextAction.DRAFT_PLAN, {}), traces)
        if self.controller.state.stage == Stage.EXECUTION_READY:
            return self._execute(Transition(NextAction.EXECUTE, {}), traces)
        if self.controller.state.stage not in {Stage.PROMPT_REVIEW, Stage.PLAN_REVIEW, Stage.WAITING_INPUT}:
            raise ControllerError("user_message_stage")

        stripped = user_message.strip()
        # Silence-deferral fix (Finding D3): do not route empty/whitespace input to LLM interpretation
        if not stripped:
            artifact_name = "prompt pseudocode" if self.controller.state.stage == Stage.PROMPT_REVIEW else "execution plan"
            return EngineResponse(
                f"Please confirm the {artifact_name} (type /confirm or press Enter with confirmation) or specify revisions (/revise <feedback>).",
                traces,
            )

        # Fast-path commands
        lower = stripped.lower()
        if lower in {
            "/confirm", "confirm", "yes", "y", "proceed",
            "looks good", "lgtm", "approved", "ok", "okay", "accept",
        }:
            return self.handle_explicit_review(Intent.ACCEPT_CURRENT)
        if lower.startswith("/revise"):
            fb = stripped[7:].strip()
            if not fb:
                return EngineResponse("Please specify your revisions: /revise <feedback>", traces)
            target_intent = (
                Intent.REVISE_TASK
                if self.controller.state.stage == Stage.PROMPT_REVIEW
                else Intent.REVISE_APPROACH
            )
            return self.handle_explicit_review(target_intent, fb)
        if lower in {"/stop", "stop", "/cancel", "cancel"}:
            return self.handle_explicit_review(Intent.CANCEL)

        # Standard LLM review interpretation
        self._sync_review_edit()
        subject_kind, subject_body = self.controller.review_subject()
        previous_stage = self.controller.state.stage
        operation, parser = {
            Stage.PROMPT_REVIEW: ("INTERPRET_PROMPT_REVIEW", self.bridge.parse_prompt_review),
            Stage.PLAN_REVIEW: ("INTERPRET_PLAN_REVIEW", self.bridge.parse_plan_review),
            Stage.WAITING_INPUT: ("INTERPRET_EXECUTION_INPUT", self.bridge.parse_execution_input),
        }[previous_stage]
        decision = ReviewDecision.from_dict(self._call(
            operation,
            {
                "BOUND_REVIEW_SUBJECT_KIND": subject_kind,
                "BOUND_REVIEW_SUBJECT_BODY": subject_body,
                "RAW_USER_REVIEW_MESSAGE": user_message,
            },
            traces,
            parser=parser,
        ))
        transition = self.controller.apply_review_decision(decision, user_message)

        if decision.intent == Intent.ACCEPT_CURRENT:
            if previous_stage == Stage.PROMPT_REVIEW:
                prompt = self.controller.state.current_prompt
                assert prompt is not None
                self.workspace.mark_artifact_confirmed("prompt", prompt.artifact_id)
            elif previous_stage == Stage.PLAN_REVIEW:
                plan = self.controller.state.current_plan
                assert plan is not None
                self.workspace.mark_artifact_confirmed("plan", plan.artifact_id)
        if decision.intent == Intent.REVISE_APPROACH and previous_stage == Stage.PROMPT_REVIEW:
            self.workspace.publish_approach_sources(list(self.controller.state.approach_sources))

        return self._apply_transition(transition, user_message, traces)

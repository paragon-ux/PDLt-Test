"""The plain-call arms C0-C3 (design §4, Appendix A).

All four go through the API worker's own transport (``_responses_request`` and
``_send_json_with_retries``). They therefore share P's endpoint, retries, socket
timeout, per-call deadline and call-trace records, so no transport difference
can separate an arm from the protocol.

| Arm | Sends |
|---|---|
| C0 | the request alone: no instructions, no ``reasoning`` field (the provider's default) |
| C1 (and C-med / C-high) | the request, with ``reasoning: {effort}`` |
| C2 | the request + EXECUTE's output contract: the bootstrap instructions, the exact ``output_schema`` a rendered EXECUTE projection shows (with the Result IR block in verified mode), the JSON-only suffix, and ``json_object`` mode |
| C3 | a real EXECUTE projection from ``OperationBridge`` with no prompt and no plan (both null) and the sanitized request as ``SUPPLIED_EXECUTION_INPUT_SOURCE``, sent by ``worker.call``, so the guidance, JSON mode and effort are EXECUTE's own |

These modules run under whichever worktree's code is on ``PYTHONPATH``. At gate
time that is P_new's, so C2 and C3 mirror P_new's EXECUTE (design §4).
"""
from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pdl_taskmaster.providers.api_worker import _JSON_ONLY_SUFFIX, ApiWorker, OutputLimitError, ProviderError
from pdl_taskmaster.runtime.operation_bridge import OperationBridge
from pdl_taskmaster.runtime.output_contracts import RESULT_IR_MODE
from pdl_taskmaster.runtime.quarantine import compile_bootstrap_output
from pdl_taskmaster.runtime.result_ir import render_instructions
from pdl_taskmaster.runtime.workspace import MemoryWorkspaceRun
from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

ARTIFACT_SYMBOLS = ("CONFIRMED_PROMPT_BODY", "CONFIRMED_PLAN_BODY")


@dataclass
class ControlResult:
    arm: str
    status: str  # "reply", "output_limit", "malformed", "deadline" or "outage"
    kind: str | None = None  # RESULT for free text; the parsed kind for C2 and C3
    text: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    finish: str | None = None
    latency_s: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"arm": self.arm, "status": self.status, "kind": self.kind, "usage": self.usage,
                "finish": self.finish, "latency_s": round(self.latency_s, 3), "error": self.error}


def failure_status(exc: BaseException) -> str:
    """A failed call as a model outcome (``deadline``, counted as a FAIL) or an
    ``outage`` (not scored; the block is re-run). Design §9.5."""
    message = str(exc).lower()
    if isinstance(exc, OutputLimitError):
        return "output_limit"
    if "deadline" in message or "timed out twice" in message:
        return "deadline"
    if isinstance(exc, ProviderError) and exc.wire_equivalent:
        return "malformed"
    return "outage"


def sanitized(request_text: str) -> str:
    """The request as EXECUTE receives it (SUPPLIED_EXECUTION_INPUT_SOURCE)."""
    return compile_bootstrap_output(request_text, request_text)[0].strip()


def system1_snapshot(request_text: str, sys1_client: Any, sandbox: ExecutionSandbox) -> dict[str, Any]:
    """Problem class and execution tier for the raw request, decided exactly as the
    engine decides them. They set C2's and C3's contract mode and tier."""
    if sys1_client is None or not getattr(sys1_client, "is_configured", False):
        return {"available": False, "verified": False, "tier": "STANDARD"}
    from pdl_taskmaster.providers.sys1.recipes.execution_profile import ExecutionProfileRecipe
    from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe

    snapshot: dict[str, Any] = {"available": True, "verified": False, "tier": "STANDARD"}
    try:
        recipe = ProblemClassRecipe()
        body, ms = sys1_client.call(recipe.build_request({"request": request_text}))
        result = recipe.parse_response(body, duration_ms=ms)
        snapshot["verified"] = bool(result.passed_gating and result.verdict == "VERIFIED_EXECUTION")
        snapshot["problem_class"] = {"verdict": result.verdict, "passed_gating": result.passed_gating,
                                     "confidence": round(result.confidence, 4)}
    except Exception as exc:  # System 1 failing means no evidence: standard mode, as in the engine
        snapshot["problem_class_error"] = f"{type(exc).__name__}: {exc}"
    try:
        recipe = ExecutionProfileRecipe()
        body, ms = sys1_client.call(recipe.build_request({"request": request_text,
                                                          "environment": sandbox.decision_state()}))
        result = recipe.parse_response(body, duration_ms=ms)
        routed = recipe.map_to_wire(result)
        snapshot["tier"] = routed["tier"] if routed["tier"] in EXECUTION_BUDGETS else "STANDARD"
        snapshot["execution_profile"] = {"prediction": routed["prediction"], "passed_gating": result.passed_gating}
    except Exception as exc:
        snapshot["execution_profile_error"] = f"{type(exc).__name__}: {exc}"
    return snapshot


class Controls:
    def __init__(self, repo_root: Path, *, model: str, providers: list[str], max_output_tokens: int = 16384,
                 sampling: dict[str, Any] | None = None, trace_path: Path | None = None,
                 worker: ApiWorker | None = None):
        self.repo_root = Path(repo_root)
        self.worker = worker or ApiWorker(
            repo_root=self.repo_root, model=model, max_output_tokens=max_output_tokens,
            provider_pinning={"order": list(providers), "allow_fallbacks": False},
        )
        if trace_path is not None:
            self.worker.trace_path = Path(trace_path)
        self.sampling = dict(sampling or {})
        self.bridge = OperationBridge(self.repo_root)
        self.bridge.contract_form = self.worker.contract_form
        from pdl_taskmaster.host.app import DEFAULT_HIGHER_PRIORITY_CONSTRAINTS

        self.higher_priority_constraints = DEFAULT_HIGHER_PRIORITY_CONSTRAINTS
        self.sandbox = ExecutionSandbox(timeout_seconds=15.0, label="gate-controls")

    def close(self) -> None:
        self.sandbox.close()

    # ------------------------------------------------------------------ request bodies

    def _base_body(self) -> dict[str, Any]:
        body: dict[str, Any] = {"model": self.worker.model}
        if self.worker.max_output_tokens:
            body["max_output_tokens"] = self.worker.max_output_tokens
        body.update(self.sampling)
        if self.worker.provider_pinning:
            body["provider"] = self.worker.provider_pinning
        if self.worker.safety_settings:
            body["safety_settings"] = self.worker.safety_settings
        return body

    def plain_body(self, request_text: str, effort: str | None) -> dict[str, Any]:
        body = {**self._base_body(), "input": request_text}
        if effort is not None:
            body["reasoning"] = {"effort": effort}
        return body

    def _verified_channel(self) -> str:
        return render_instructions([], repo_root=self.repo_root,
                                   evidence_paths=["execution://body", "execution://witness"],
                                   requires_verified_execution=True)

    def execute_request(self, request_text: str, *, tier: str = "STANDARD", verified: bool = False):
        """A real EXECUTE request with no prompt and no plan (C3), and the source
        of C2's output contract."""
        contract = self.bridge.compiler.execution_contract["operations"]["EXECUTE"]
        # Every symbol EXECUTE includes is present; the confirmed prompt and plan (and any
        # symbol this code version adds) are null: the request is the only task statement.
        values: dict[str, Any] = {symbol: None for symbol in contract["include"]
                                  if symbol not in ("OPERATION_ID", "APPLICABLE_STANDARD_CLAUSES",
                                                    "HIGHER_PRIORITY_CONSTRAINTS")}
        assert all(symbol in values for symbol in ARTIFACT_SYMBOLS)
        values["SUPPLIED_EXECUTION_INPUT_SOURCE"] = sanitized(request_text)
        values["AVAILABLE_EXECUTION_TOOLS"] = self.sandbox.describe(EXECUTION_BUDGETS[tier])
        if verified:
            values["REQUIRED_TASK_INPUTS"] = self._verified_channel()
        workspace = MemoryWorkspaceRun.create(self.repo_root, Path(tempfile.mkdtemp(prefix="gate-c3-")),
                                              turn_id="turn_001")
        return self.bridge.request("EXECUTE", values, workspace=workspace,
                                   higher_priority_constraints=self.higher_priority_constraints,
                                   modes=frozenset({RESULT_IR_MODE}) if verified else frozenset())

    def c2_body(self, request_text: str, effort: str | None, *, tier: str = "STANDARD",
                verified: bool = False) -> dict[str, Any]:
        schema = self.execute_request(request_text, tier=tier, verified=verified).projection.document["output_schema"]
        parts = [request_text.rstrip()]
        if verified:
            parts.append(self._verified_channel().strip())
        parts.append("output_schema:\n" + json.dumps(schema, indent=2, ensure_ascii=False))
        body = {**self._base_body(), "instructions": self.worker._bootstrap.rstrip(),
                "input": "\n\n".join(parts) + _JSON_ONLY_SUFFIX, "text": {"format": {"type": "json_object"}}}
        if effort is not None:
            body["reasoning"] = {"effort": effort}
        return body

    # ------------------------------------------------------------------ sending

    def _send(self, arm: str, body: dict[str, Any]) -> tuple[dict[str, Any] | None, ControlResult]:
        trace = self.worker.begin_call(f"CONTROL:{arm}")
        started = time.perf_counter()
        try:
            request = self.worker._responses_request(body, self.worker._resolve_api_key())
            data = self.worker._send_json_with_retries(request, time.monotonic() + self.worker.max_call_seconds)
            trace.final = "completed"
        except Exception as exc:
            trace.final, trace.error = "failed", type(exc).__name__
            return None, ControlResult(arm, failure_status(exc), latency_s=time.perf_counter() - started,
                                       error=f"{type(exc).__name__}: {exc}"[:2000])
        finally:
            self.worker.end_call(trace)
        details = data.get("incomplete_details") or {}
        finish = details.get("reason") if isinstance(details, dict) else details
        usage_raw = data.get("usage") or {}
        usage = {k: usage_raw.get(k) for k in ("input_tokens", "output_tokens")}
        usage["reasoning_tokens"] = (usage_raw.get("output_tokens_details") or {}).get("reasoning_tokens")
        result = ControlResult(arm, "reply", usage=usage, finish=finish, latency_s=time.perf_counter() - started)
        if data.get("status") == "incomplete" and finish in ("max_output_tokens", "max_tokens", "length"):
            result.status = "output_limit"
        return data, result

    def _parse_outcome(self, result: ControlResult, text: str) -> ControlResult:
        try:
            outcome = self.bridge.parse_execution(text)
        except Exception as exc:
            result.status, result.error = "malformed", f"{type(exc).__name__}: {exc}"[:2000]
            result.text = text
            return result
        result.kind, result.text = outcome.kind, outcome.body
        return result

    def run(self, arm: str, request_text: str, *, effort: str | None = None, tier: str = "STANDARD",
            verified: bool = False) -> ControlResult:
        if arm == "C3":
            return self._run_c3(request_text, tier=tier, verified=verified)
        body = (self.c2_body(request_text, effort, tier=tier, verified=verified) if arm == "C2"
                else self.plain_body(request_text, effort))
        data, result = self._send(arm, body)
        if data is None or result.status != "reply":
            return result
        text = ApiWorker._extract_output_text(data)
        if arm == "C2":
            return self._parse_outcome(result, text)
        result.kind, result.text = "RESULT", text
        return result

    def run_conversation(self, arm: str, messages: list[dict[str, str]], *, effort: str | None = None) -> ControlResult:
        """A plain call whose input is a conversation (the interaction groups' follow-ups)."""
        body = {**self._base_body(), "input": messages}
        if effort is not None:
            body["reasoning"] = {"effort": effort}
        data, result = self._send(arm, body)
        if data is None or result.status != "reply":
            return result
        result.kind, result.text = "RESULT", ApiWorker._extract_output_text(data)
        return result

    def _run_c3(self, request_text: str, *, tier: str, verified: bool) -> ControlResult:
        request = self.execute_request(request_text, tier=tier, verified=verified)
        started = time.perf_counter()
        try:
            reply = self.worker.call(request)
        except Exception as exc:
            return ControlResult("C3", failure_status(exc), latency_s=time.perf_counter() - started,
                                 error=f"{type(exc).__name__}: {exc}"[:2000])
        result = ControlResult("C3", "reply", usage=dict((reply.metadata or {}).get("usage") or {}),
                               latency_s=time.perf_counter() - started)
        return self._parse_outcome(result, reply.text)

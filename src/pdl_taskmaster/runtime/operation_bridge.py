from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
import json
import re

from pydantic import TypeAdapter, ValidationError

from pdl_taskmaster.runtime.context_compiler import CompiledProjection, ContextCompiler
from pdl_taskmaster.runtime.workspace import WorkspaceInvocation, WorkspaceRun
from pdl_taskmaster.runtime.wire_payloads import (
    ActivationDecisionPayload,
    ActivationRoute,
    ApproachChangeDimension,
    ArtifactReviewPayload,
    BootstrapAnalysisData,
    BootstrapAnalysisPayload,
    ExecutionDraftBlockedData,
    ExecutionDraftPayload,
    ExecutionDraftResultData,
    ExecutionInputPayload,
    ExecutionInputReviseData,
    ExecutionOutcomePayload,
    ExecutionRequestInputData,
    ExecutionResultData,
    NeutralPlanBodyPayload,
    PromptBodyPayload,
    PromptDraftData,
    PromptDraftPayload,
    ProtocolDiscussionPayload,
    ResultIRRepairPayload,
    ReviewFactsData,
    SYSTEM1_CONFIDENCE_FLOOR,
    TaskChangeDimension,
    UnconfirmedExecutionOutcomePayload,
    UnconfirmedExecutionRequestInputData,
    WireError,
    format_validation_feedback,
    map_validation_error_to_wire_reason,
)


@dataclass(frozen=True)
class ActivationDecision:
    route: ActivationRoute
    response: str | None = None


@dataclass(frozen=True)
class PromptDraftOutcome:
    kind: str
    prompt_body: str | None = None
    approach_handoff: str = "NONE"
    blocking_basis: str | None = None
    response: str | None = None
    task_entities: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ExecutionOutcome:
    kind: str
    body: str
    expected_type: str | None = None
    description: str | None = None
    result_ir: dict | None = None


@dataclass(frozen=True)
class UnconfirmedExecutionOutcome:
    kind: str
    body: str
    interpretation: str
    approach: str
    expected_type: str | None = None
    description: str | None = None
    result_ir: dict | None = None


@dataclass(frozen=True)
class ExecutionDraftOutcome:
    """A validated DRAFT_EXECUTE reply: the typed brief on RESULT, the stated reason
    (blocked_reason) on BLOCKED_BY_HIGHER_PRIORITY."""

    kind: str
    brief: ExecutionDraftResultData | None = None
    blocked_reason: str = ""


@dataclass(frozen=True)
class ModelRequest:
    projection: CompiledProjection
    prompt: str
    workspace_invocation: WorkspaceInvocation

    @property
    def operation(self) -> str:
        return self.projection.operation

    @property
    def manifest(self) -> dict[str, Any]:
        return self.projection.manifest


def _normalize_body_newlines(body: str) -> str:
    """Normalize a wholly double-escaped wire payload.

    Some model/provider combinations (e.g. Groq JSON mode) escape every newline
    as a literal '\\n' in string properties instead of an actual linebreak. That
    case is recognised only when the body contains no real linebreak at all. A
    body that already has linebreaks is left untouched: its '\\n' sequences are
    content (for example escape sequences inside string literals in code), and
    rewriting them would corrupt the deliverable.
    """
    if "\n" in body:
        return body
    if "\\n" in body:
        # A wholly double-escaped body is one JSON string level too deep: decode
        # that level, so escaped quotes and backslashes are restored with the
        # newlines (run 215232 r8: print(\"...\") survived a newline-only rewrite).
        try:
            decoded = json.loads(f'"{body}"', strict=False)
        except ValueError:
            decoded = None
        if isinstance(decoded, str):
            return decoded
        body = body.replace("\\r\\n", "\n").replace("\\n", "\n")
    if "\\t" in body:
        body = body.replace("\\t", "\t")
    return body


class OperationBridge:
    def __init__(self, repo_root: str | Path, *, render_compact: bool = False):
        self.repo_root = Path(repo_root)
        self.render_compact = render_compact
        self.compiler = ContextCompiler(self.repo_root)
        # The worker's ContractForm for an operation (ApiWorker.contract_form), set by the
        # host; without one, the default form is shown (ADR-0028 rule 1).
        self.contract_form: Any = None
        bootstrap_path = Path(__file__).parent / "worker-bootstrap.txt"
        if not bootstrap_path.is_file():
            bootstrap_path = self.repo_root / "src" / "pdl_taskmaster" / "runtime" / "worker-bootstrap.txt"
        self.bootstrap = bootstrap_path.read_text(encoding="utf-8")

    def request(
        self,
        operation: str,
        values: dict[str, Any],
        *,
        workspace: WorkspaceRun,
        higher_priority_constraints: Any = None,
        operator_correction: str | None = None,
        modes: frozenset[str] = frozenset(),
    ) -> ModelRequest:
        invocation = workspace.materialize_operation(
            operation, values, higher_priority_constraints=higher_priority_constraints
        )
        materialized_values, materialized_higher_priority = workspace.load_operation_values(invocation)
        form = self.contract_form(operation) if callable(self.contract_form) else None
        projection = self.compiler.compile(
            operation,
            materialized_values,
            higher_priority_constraints=materialized_higher_priority,
            contract_form=form,
            modes=modes,
        )
        workspace.record_projection(invocation, projection.manifest, projection.document)
        prompt = projection.render(self.bootstrap, compact=self.render_compact)
        if operator_correction:
            # Appended outside the projection document so projection_sha256
            # (and fixture replay) stay stable; only used on the retry path.
            prompt = prompt + operator_correction.strip() + "\n"
        return ModelRequest(projection, prompt, invocation)

    @staticmethod
    def _object(model_text: str) -> dict[str, Any]:
        """Extract exactly one JSON object from a worker response.

        Tolerant of *placement* (leading/trailing prose, BOM, markdown fences
        anywhere in the text) but never repairs *content*: malformed JSON
        still raises WireError("invalid_json") so the caller's retry path
        can ask the stateless worker to re-emit (see SessionEngine._call).
        """
        stripped = model_text.strip().lstrip("\ufeff")
        last_error: json.JSONDecodeError | None = None
        value: Any = None
        # strict=False accepts literal control characters (a raw newline) inside
        # strings: the decoded value is identical to the escaped form, so this is
        # transport tolerance, not content repair.
        try:
            value = json.loads(stripped, strict=False)
        except json.JSONDecodeError as exc:
            last_error = exc
        if value is None:
            from pdl_taskmaster.runtime.text_blocks import unfence_json

            unfenced = unfence_json(stripped)
            try:
                value = json.loads(unfenced, strict=False)
            except json.JSONDecodeError as exc:
                last_error = exc
        if value is None:
            # Balanced-brace scan: locate the first parseable JSON object
            # embedded in surrounding prose. raw_decode consumes exactly one
            # balanced value starting at each candidate brace.
            decoder = json.JSONDecoder(strict=False)
            for idx, char in enumerate(stripped):
                if char != "{":
                    continue
                try:
                    candidate, _ = decoder.raw_decode(stripped[idx:])
                except json.JSONDecodeError as exc:
                    last_error = exc
                    continue
                if isinstance(candidate, dict):
                    value = candidate
                    break
        if value is None:
            # Carry the underlying JSONDecodeError detail (e.g. "Invalid
            # \\escape") so the retry's operator correction names the actual
            # defect instead of a generic invalid_json.
            detail = f"invalid_json ({last_error.msg} at column {last_error.pos + 1})" if last_error else "invalid_json"
            raise WireError(detail)
        if not isinstance(value, dict):
            raise WireError("not_object")
        return value

    @staticmethod
    def _keys(value: dict[str, Any], allowed: set[str], required: set[str]) -> None:
        if set(value) - allowed:
            raise WireError("extra_fields")
        if not required <= set(value):
            raise WireError("missing_fields")

    def _validate(self, operation: str, model_type: Any, model_text: str) -> Any:
        value = self._object(model_text)
        if operation == "EXECUTE" and isinstance(value, dict) and "kind" not in value:
            # ADR-0016 / ADR-0017: Root Result IR and model synonym wire normalization.
            for alt in ("deliverable", "text", "output", "code", "solution", "content", "response", "answer"):
                if alt in value and isinstance(value[alt], str) and value[alt].strip() and "body" not in value:
                    value["body"] = value[alt]
                    break
            if "files" in value or "reconciliation" in value or "witness" in value:
                body_candidate = value.get("body")
                if not body_candidate and value.get("files") and isinstance(value["files"], list):
                    code_snippets = [
                        f.get("evidence", {}).get("observed")
                        for f in value["files"]
                        if isinstance(f, dict) and isinstance(f.get("evidence"), dict) and f["evidence"].get("observed")
                    ]
                    if code_snippets:
                        body_candidate = "\n\n".join(s for s in code_snippets if s)
                if not body_candidate:
                    body_candidate = "Delivered Result IR"
                value = {
                    "kind": "RESULT",
                    "body": body_candidate,
                    "result_ir": value,
                }
            elif "body" in value and isinstance(value["body"], str) and value["body"].strip():
                value["kind"] = "RESULT"
        try:
            adapter = TypeAdapter(model_type)
            return adapter.validate_python(value)
        except ValidationError as val_err:
            reason = map_validation_error_to_wire_reason(
                operation, val_err, value if isinstance(value, dict) else None
            )
            feedback = format_validation_feedback(val_err)
            raise WireError(reason, operator_feedback=feedback, validation_error=val_err) from val_err

    def parse_activation(self, model_text: str) -> ActivationDecision:
        payload: ActivationDecisionPayload = self._validate("INTERPRET_ACTIVATION", ActivationDecisionPayload, model_text)
        if payload.confidence is not None and payload.confidence < SYSTEM1_CONFIDENCE_FLOOR:
            # ADR-0012 Fail-closed: low-confidence activation classification defaults to protocol application
            return ActivationDecision(ActivationRoute.APPLY_PROTOCOL)
        return ActivationDecision(payload.route, payload.response.strip() if payload.response else None)

    def parse_prompt_draft(self, model_text: str) -> PromptDraftOutcome:
        payload: PromptDraftPayload = self._validate("DRAFT_PROMPT", PromptDraftPayload, model_text)
        if isinstance(payload, PromptDraftData):
            return PromptDraftOutcome(
                payload.kind,
                _normalize_body_newlines(payload.prompt_body.strip()),
                payload.approach_handoff,
                task_entities=tuple(payload.task_entities) if payload.task_entities else (),
            )
        return PromptDraftOutcome(
            payload.kind,
            blocking_basis=payload.blocking_basis,
            response=_normalize_body_newlines(payload.response.strip()),
        )

    def _parse_named_body(self, model_text: str, field: str) -> str:
        if field == "prompt_body":
            return self.parse_prompt_body(model_text)
        if field == "neutral_plan_body":
            return self.parse_plan_body(model_text)
        value = self._object(model_text)
        self._keys(value, {field}, {field})
        body = value[field]
        if not isinstance(body, str) or not body.strip():
            raise WireError(field)
        return _normalize_body_newlines(body.strip())

    def parse_prompt_body(self, model_text: str) -> str:
        payload: PromptBodyPayload = self._validate("REVISE_PROMPT", PromptBodyPayload, model_text)
        return _normalize_body_newlines(payload.prompt_body.strip())

    def parse_plan_body(self, model_text: str) -> str:
        payload: NeutralPlanBodyPayload = self._validate("DRAFT_PLAN", NeutralPlanBodyPayload, model_text)
        return _normalize_body_newlines(payload.neutral_plan_body.strip())

    def _parse_artifact_review(self, model_text: str, is_plan: bool = False) -> dict[str, Any]:
        op = "INTERPRET_PLAN_REVIEW" if is_plan else "INTERPRET_PROMPT_REVIEW"
        payload: ArtifactReviewPayload = self._validate(op, ArtifactReviewPayload, model_text)
        if hasattr(payload, "confidence") and payload.confidence is not None and payload.confidence < SYSTEM1_CONFIDENCE_FLOOR:
            # ADR-0012 Fail-closed: low-confidence review classification must never progress or silently route.
            # Escalate to UNRESOLVED to re-prompt human confirmation per REVIEW-09.
            return {"intent": "UNRESOLVED"}
        if isinstance(payload, ReviewFactsData):
            task_changed = bool(payload.task_change_dimensions)
            approach_changed = bool(payload.approach_change_dimensions)
            if not (task_changed or approach_changed or payload.progression_requested):
                # All-empty REVIEW_FACTS: the model reports the message changed
                # no dimension and requested no progression. Per REVIEW-09/13/14,
                # mechanically treat this as SUBSTANTIVE_DISCUSSION.
                return {"intent": "SUBSTANTIVE_DISCUSSION"}
            # Normative TASK-02 disambiguation during plan review:
            # Procedural feedback on the response plan (e.g. "plan your response", "show your work")
            # is often spuriously classified by LLMs as ACTION_SUBJECT_OR_OBJECT. Per TASK-02,
            # procedural instructions that do not alter scope/constraints are approach semantics.
            if is_plan and task_changed and set(payload.task_change_dimensions) <= {"ACTION_SUBJECT_OR_OBJECT", "OTHER_TASK_OR_RESULT"}:
                return {"intent": "REVISE_APPROACH"}
            if task_changed:
                return {"intent": "REVISE_TASK", "also_changes_approach": approach_changed}
            if approach_changed:
                return {"intent": "REVISE_APPROACH"}
            return {"intent": "ACCEPT_CURRENT"}
        return {"intent": payload.kind}

    def parse_prompt_review(self, model_text: str) -> dict[str, Any]:
        return self._parse_artifact_review(model_text, is_plan=False)

    def parse_plan_review(self, model_text: str) -> dict[str, Any]:
        return self._parse_artifact_review(model_text, is_plan=True)

    def parse_bootstrap_analysis(self, model_text: str) -> dict[str, Any]:
        payload: BootstrapAnalysisPayload = self._validate("BOOTSTRAP_ANALYSIS", BootstrapAnalysisPayload, model_text)
        if isinstance(payload, BootstrapAnalysisData):
            return {
                "kind": payload.kind,
                "task_summary": payload.task_summary,
                "approach_notes": payload.approach_notes,
                "risk_notes": payload.risk_notes,
                "task_entities": [entity.model_dump() for entity in payload.task_entities],
            }
        return {"kind": payload.kind, "response": payload.response.strip()}

    def parse_execution_input(self, model_text: str) -> dict[str, Any]:
        payload: ExecutionInputPayload = self._validate("INTERPRET_EXECUTION_INPUT", ExecutionInputPayload, model_text)
        if hasattr(payload, "confidence") and payload.confidence is not None and payload.confidence < SYSTEM1_CONFIDENCE_FLOOR:
            return {"intent": "UNRESOLVED"}
        if isinstance(payload, ExecutionInputReviseData):
            return {
                "intent": "REVISE_TASK",
                "also_changes_approach": payload.also_changes_approach,
            }
        return {"intent": payload.kind}

    def parse_protocol_discussion(self, model_text: str) -> str:
        payload: ProtocolDiscussionPayload = self._validate("ANSWER_PROTOCOL_DISCUSSION", ProtocolDiscussionPayload, model_text)
        return payload.body.strip()

    def parse_execution_draft(self, model_text: str) -> ExecutionDraftOutcome:
        payload: ExecutionDraftPayload = self._validate("DRAFT_EXECUTE", ExecutionDraftPayload, model_text)
        if isinstance(payload, ExecutionDraftBlockedData):
            return ExecutionDraftOutcome(payload.kind, None, payload.brief_body.strip())
        return ExecutionDraftOutcome(payload.kind, payload)

    def parse_result_ir_repair(self, model_text: str) -> dict:
        payload: ResultIRRepairPayload = self._validate("EMIT_RESULT_IR", ResultIRRepairPayload, model_text)
        return payload.result_ir.model_dump()

    def parse_execution(self, model_text: str) -> ExecutionOutcome:
        payload: ExecutionOutcomePayload = self._validate("EXECUTE", ExecutionOutcomePayload, model_text)
        if isinstance(payload, ExecutionRequestInputData):
            return ExecutionOutcome(
                payload.kind,
                _normalize_body_newlines(payload.body.strip()),
                payload.expected_type.strip(),
                payload.description.strip(),
                None,
            )
        ir_dict = payload.result_ir.model_dump() if payload.result_ir is not None else None
        return ExecutionOutcome(
            payload.kind,
            _normalize_body_newlines(payload.body.strip()),
            None,
            None,
            ir_dict,
        )

    def parse_unconfirmed_execution(self, model_text: str) -> UnconfirmedExecutionOutcome:
        payload: UnconfirmedExecutionOutcomePayload = self._validate(
            "EXECUTE_UNCONFIRMED", UnconfirmedExecutionOutcomePayload, model_text
        )
        interpretation = _normalize_body_newlines(payload.interpretation.strip())
        approach = _normalize_body_newlines(payload.approach.strip())
        if isinstance(payload, UnconfirmedExecutionRequestInputData):
            return UnconfirmedExecutionOutcome(
                payload.kind,
                _normalize_body_newlines(payload.body.strip()),
                interpretation,
                approach,
                payload.expected_type.strip(),
                payload.description.strip(),
                None,
            )
        ir_dict = payload.result_ir.model_dump() if payload.result_ir is not None else None
        return UnconfirmedExecutionOutcome(
            payload.kind,
            _normalize_body_newlines(payload.body.strip()),
            interpretation,
            approach,
            None,
            None,
            ir_dict,
        )



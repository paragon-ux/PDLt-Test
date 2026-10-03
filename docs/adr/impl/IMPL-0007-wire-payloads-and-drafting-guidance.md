# IMPL-0007: Wire Payloads, Operator Corrections, Drafting Guidance and Notation Lint

## Status
**Accepted.** Implements [ADR-0010](../0010-pydantic-wire-enforcement.md) and [ADR-0014](../0014-dual-plane-boundary-and-wire-conformance.md). The schema generation part is to be superseded by [IMPL-0001](IMPL-0001-output-contracts-from-pydantic.md). Recorded 2026-10-03 from the 2.6.0rc1 code.

## Context
ADR-0010 makes Pydantic the schema authority for every operation's output, with field-localized operator corrections. ADR-0014 separates the task plane from the drafting-discipline plane: positive guidance, no negative priming, no silent rewriting. This record holds the models, the correction path and where each rule is enforced.

## Decision (as implemented)
- **Payload models.** `OPERATION_PAYLOAD_MODELS` (`runtime/wire_payloads.py:474-489`) maps each operation to its Pydantic model:
  - `ActivationDecisionPayload`, `BootstrapAnalysisPayload` and `PromptDraftPayload`;
  - `NeutralPlanBodyPayload`, `ArtifactReviewPayload` and `ExecutionInputPayload`;
  - `ProtocolDiscussionPayload`, `ExecutionDraftPayload`, `ResultIRRepairPayload` and `ExecutionOutcomePayload`.

  `OperationBridge` parses every reply through them, tolerant of placement (fences, BOM, surrounding text) but never of content.
- **Operator corrections.**
  - On a wire failure, `SessionEngine._call` retries once.
  - The correction is the validation feedback, field-localized by `format_validation_feedback`, or the generic correction otherwise.
- **Drafting guidance.** Positive, exemplar-based guidance lives per operation in `providers/api_worker.py`, in the `extra_guidance` blocks for `DRAFT_PROMPT`/`REVISE_PROMPT`, `DRAFT_PLAN`/`REVISE_PLAN`, `DRAFT_EXECUTE` and `EXECUTE`.
- **The notation rules are a review-gate lint, not a wire rule.** PDL-05 (fielded schemas), PDL-06 (code fences), PDL-08 (deferrals and drafting meta-rules) and PLAN-10 (placeholders) are checked by `verification/plan_soundness.py` on every prompt and plan draft.
  - A violation gets one redraft carrying the finding.
  - If it survives, the artifact is published unchanged with a host note naming each finding and its line. It is never a wire failure and never a host rewrite (AUTH-05).
  - The lint checks notation only. It never inspects the method a plan chooses (GUARD-01, GUARD-03, GUARD-04).
- **Provider grammar.** `ApiWorker._sanitize_schema_for_grammar` and `_strictify` (`providers/api_worker.py:615-698`, `198-229`) derive the decoding constraint from the Pydantic model. The schema shown in the prompt still comes from static files under `controller/schemas/`. IMPL-0001 removes that second source.

## Divergence from ADR-0010 and ADR-0014 as written
- **ADR-0014 Pillar 2** (Pydantic validators raising `prompt_pdl_field_schema_prohibited` and similar) and **Pillar 3.3** (a validator per clause in `wire_payloads.py`). These are not implemented in that form. The rules are enforced by the review-gate lint above, which never fails the wire.
- **ADR-0017 Pillar 3.2** (`_strip_meta_rule_bleed` stripping deferral phrases) no longer exists. It contradicted ADR-0014's ban on silent rewriting.
- **ADR-0010's claim of "no schema drift with static contract files"** was not achieved for the prompt-side schema. The 2026-10-03 stall diagnosis found five operations whose grammar required keys the prompt schema did not show (IMPL-0001).

## Evidence
- **Sessions 5–7 (protocol v2).**
  - Negative instructions ("never add 'do not compute'") primed models to emit `TASK:`/`OUTPUT:` fields and "DO NOT perform the partitioning".
  - The regex stripper missed inline variants. AUTH-03 then forced placeholder plans and empty results.

## Verification
- `tests/test_wire_repairs.py`: corrections, schema shape, notation findings.
- `tests/test_pydantic_wire.py`.
- `tests/test_harness_anti_overfitting.py`.

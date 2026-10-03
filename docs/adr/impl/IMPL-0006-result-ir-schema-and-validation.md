# IMPL-0006: Result IR Schema and Validation Sequence

## Status
**Accepted.** Implements [ADR-0009](../0009-result-pseudocode-decomposition-standard.md) as amended by the Result standard (`contracts/standards/RESULT_STANDARD.md`, RS-01 to RS-10), and [ADR-0016](../0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md). Recorded 2026-10-03 from the 2.6.0rc1 code.

## Context
ADR-0009 requires `EXECUTE` to emit a structured, evidence-cited result record next to the deliverable. ADR-0016 makes Pydantic the only structural validator for it, before any semantic check. This record holds the shapes, the clause status and the sequence.

## Decision (as implemented)
- **Models** (`runtime/wire_payloads.py`):
  - `Evidence` (path, optional section, optional observed quote);
  - `FileItem`, `ReconciliationItem` (status `satisfied | partial | open`) and `DefectItem`;
  - `ResultIRData` (`files`, `reconciliation`, `open_defects`, optional `witness`);
  - `witness` is a discriminated union of `PositiveWitness` and `NegativeWitness` on `polarity`.
- **Clause status (RESULT_STANDARD):**
  - RS-01: the IR travels in the output's `result_ir` field, never in the deliverable text.
  - RS-02 and RS-03 are **retired**: requirement IDs are not derived, and reconciling every requirement is not required. `files` and `reconciliation` may be empty.
  - RS-04: evidence paths resolve inside the workspace, or to `execution://body`.
  - RS-05 and RS-06: section and observation citations are checked, and findings are recorded, not blocking.
  - RS-07: citations are optional.
  - RS-08: shape is validated mechanically before publishing.
  - RS-09: on a follow-up turn the previous turn's request and result are passed as labelled reference only. Its Result IR is **not** injected and is never an evidence path.
  - RS-10: feature gate `PDLT_RESULT_IR=1` for tasks that do not require verified execution.
- **Sequence.**
  1. Pydantic validates the IR, from the wire or from a repair (`EMIT_RESULT_IR`). Failures return field-localized messages.
  2. Only then does the host run semantic checks: path resolution and escape, verbatim section and observation, then witness verification (IMPL-0009).
- **Bare-IR normalization** (`runtime/operation_bridge.py:215-232`):
  - an `EXECUTE` reply without `kind` has its synonym keys mapped to `body` (`deliverable`, `text`, `output`, …);
  - if it carries `files`, `reconciliation` or `witness`, it is wrapped as a `RESULT`.
- **Instructions.** `runtime/result_ir.py:load_standard_instructions` reads RESULT_STANDARD from the repository copy when present, and otherwise falls back to an in-code canonical copy.

## Divergence from ADR-0009 and ADR-0016 as written
- **Requirement IDs and reconciliation.** ADR-0009's mechanically derived requirement IDs, with each reconciled exactly once, were retired (RS-02, RS-03). So was ADR-0016's "1-to-1 bijection" check.
- **Chaining.** ADR-0009's forward chaining of the prior Result IR was replaced by RS-09's reference-only previous result.

## Evidence
- **WAL build sessions** (`runs/wal-build`, `wal-exp2b`, `wal-exp4`; GLM-4.7; 2026-09-17/18):
  - `REQUIRED_TASK_INPUTS` and `SUPPLIED_EXECUTION_INPUT_SOURCE` were null in every `EXECUTE`, and revision epochs invented APIs;
  - byte-exact chaining cut the diffs from about 100% rewrites to 0–7 lines, but did not stop goal drift.
- **ADR-0016:** models emitted the IR at the root without `kind`, and were rejected with `execution_kind`.

## Verification
`tests/test_execution_phase.py`, `tests/test_wire_repairs.py`, `tests/test_pydantic_wire.py`.

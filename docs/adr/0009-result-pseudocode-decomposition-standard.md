# ADR-0009: Require decomposed Result Pseudocode with cited execution evidence

- Status: Accepted (prototype; feature-gated per RS-10). Amended by the Result standard (`contracts/standards/RESULT_STANDARD.md`):
  - mechanically derived requirement IDs and reconciliation of every requirement are retired (RS-02, RS-03);
  - the previous turn's result record is no longer chained forward: a follow-up turn receives the previous request and result as labelled reference only (RS-09).
- Date: 2026-09-18
- Parent decision: [ADR-0005](0005-optional-result-pseudocode.md)
- Related requirements: TRD-0003: Result Pseudocode Decomposition Standard (upstream document, not included in this repository)
- Related decisions: [ADR-0003](0003-phase-projected-single-model-contexts.md), [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md), [ADR-0008](0008-context-and-session-management.md), [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md)
- Implementation, clause status and evidence: [IMPL-0006](impl/IMPL-0006-result-ir-schema-and-validation.md)

## Context

Multi-turn builds showed a continuity failure across task epochs.
- **Execution never saw the source.** Phase projections had removed the source material, so execution conditioned only on pseudocode summaries, and revision turns invented interfaces for code they had never seen.
- **Byte-exact chaining was not enough.** Passing the previous deliverable byte for byte stopped the invented interfaces, but did not stop goal drift or fabricated test expectations.
- **Summaries are a weak link.** They are the only representation dense enough to survive phase boundaries, but a summary written from memory is itself where hallucination enters.

## Decision

`EXECUTE` emits, alongside the native deliverable, a **structured result record** (Result IR) that is:

- **Evidence-cited.** Claims about files, status and open defects cite artifacts that resolve inside the workspace, and quoted observations must match them verbatim. Invented paths or quotes are mechanical findings.
- **Mechanically validated by the host,** in shape and citations, before the result is published. Persistent failures are recorded and scored, never masked.
- **Structured, not narrated.** The record is schema-shaped data, carried apart from the deliverable text. Free-text narration alone does not conform.

## Consequences

### Positive
- Evidence and existence travel together: fabricated evidence becomes mechanically invalid rather than merely implausible.
- Validation is host-owned and independent of the model.

### Negative
- Generation cost per turn increases.
- Citations add context on large projects, so a size policy is needed.

## Alternatives considered

### Byte-exact chaining only
Implemented first, and kept as the substrate. It removes invented interfaces but not goal drift.

### Free-text Result Pseudocode (ADR-0005 unmodified)
Rejected. Prose decompositions cannot be audited.

### Host-side cumulative project merge
Deferred. Merging partial deliverables is sound but heuristic-laden.

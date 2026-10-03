# ADR-0016: Pydantic Single Source of Truth (SSOT) for Wire and Deliverable Boundary Enforcement

- Status: Accepted. The requirement-coverage check named in decision 2 was retired with RS-02/RS-03 (see [ADR-0009](0009-result-pseudocode-decomposition-standard.md)).
- Date: 2026-09-27
- Parent decisions: [ADR-0010](0010-pydantic-wire-enforcement.md), [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md)
- Related decisions: [ADR-0009](0009-result-pseudocode-decomposition-standard.md), [ADR-0013](0013-substantive-correctness-verification.md), [ADR-0015](0015-model-synthesized-verification-and-confinement-boundaries.md)
- Implementation: [IMPL-0006](impl/IMPL-0006-result-ir-schema-and-validation.md)

## Context

Result IR validation had two paths. Records arriving on the wire were validated by Pydantic; records extracted from deliverable text were checked by hand-written code. This caused three problems:
- **Inconsistent errors.** Structural errors were reported differently depending on the channel the record arrived on.
- **Valid records rejected.** Models often emitted the record at the root without the outcome's discriminator, and correct work was rejected; on retry, models discarded it.
- **Checks in the wrong order.** Semantic checks sometimes ran before the structure had been confirmed.

## Decision

1. **One schema for every channel.** All Result IR components (evidence, files, reconciliation, defects, witness) are Pydantic models. Every channel validates through them: wire, repair and deliverable.
2. **Structure before semantics.** A candidate record is first validated structurally, and a failure stops there with field-localized errors. Only a structurally valid record goes on to the host's semantic checks: path resolution, citation matching and witness verification.
3. **Normalize, don't reject, a bare record.** A reply that is plainly a result record without the outcome wrapper is wrapped as a result instead of rejected. The content is never altered.

## Consequences

### Positive
- One declarative schema defines the result record everywhere.
- Structural errors are reported first, deterministically and locally.
- Correct work is not lost to a missing discriminator.

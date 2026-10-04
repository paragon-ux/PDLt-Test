# ADR-0010: Pydantic Schema Enforcement and Structured Wire Contracts

- Status: Accepted. Decision 2 is achieved for the provider's decoding constraint but not for the schema shown in the prompt, which still came from separate files. [ADR-0028](0028-model-capability-boundary.md) completes it ([IMPL-0001](impl/IMPL-0001-output-contracts-from-pydantic.md)).
- Date: 2026-09-26
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related decisions: [ADR-0002](0002-controller-owned-artifact-controls.md), [ADR-0003](0003-phase-projected-single-model-contexts.md), [ADR-0006](0006-bounded-pre-execution-reasoning.md), [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md), [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md)
- Related requirements: TRD-0002 (upstream document, not included in this repository), TRD-0003 (upstream document, not included in this repository)
- Implementation: [IMPL-0007](impl/IMPL-0007-wire-payloads-and-drafting-guidance.md)

## Context

Model replies were validated by ad-hoc JSON extraction and hand-written key and type checks, and this had reached its limit:
1. **Fragmented validation.** Output schemas were kept in several places: contract files, the provider-grammar code and the per-operation parsers.
2. **Coarse correction.** A reply that failed validation got a generic correction that did not say which field was wrong.
3. **Drift.** Hand-written schemas sent to providers drifted from the parsers that read the replies.

## Decision drivers

- One authority for deserializing, validating and typing every operation's output.
- Exact, field-level corrections for the single retry.
- Provider schemas derived from that authority, not maintained by hand.
- Tolerance of placement (fences, BOM, surrounding text) without tolerance of content.

## Decision

1. **Typed wire payloads.** Every operation's output is a Pydantic v2 model, and every reply is parsed through it.
2. **One source for structured-output schemas.** The schema a provider enforces is derived from the same model. Only keywords a decoding engine cannot handle are removed, deterministically. No cross-model behavioural parity is assumed.
3. **Precise corrections.** When a reply fails validation, the single retry carries the failing fields and what was expected.

## Consequences

### Positive
- No hand-written validation per operation.
- Schemas cannot drift from the code that reads replies.
- Retries name exactly what to fix.

### Neutral / Negative
- Depends on `pydantic>=2`.
- Validation overhead must stay negligible.

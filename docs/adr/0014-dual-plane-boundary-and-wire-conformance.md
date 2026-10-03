# ADR-0014: Dual-Plane Boundary Architecture for Normative Standards and Wire Conformance

- Status: Accepted, amended.
  - **Notation rules (PDL-05, PDL-06, PDL-08, PLAN-10) are enforced at the review gate,** not at the wire. A violation is redrafted once; if it survives, the artifact is published unchanged with a host note. It is never a wire failure and never a host rewrite.
  - **Pillar 4 is to be superseded** by [ADR-0028](0028-model-capability-boundary.md) rule 1 (proposed).
- Date: 2026-09-27
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related decisions: [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md), [ADR-0007](0007-operationalize-negative-constraints-by-omission.md), [ADR-0010](0010-pydantic-wire-enforcement.md)
- Related standards: [PDL_STANDARD](../../contracts/standards/PDL_STANDARD.md), [PROMPT_STANDARD](../../contracts/standards/PROMPT_STANDARD.md), [RESPONSE_PLAN_STANDARD](../../contracts/standards/RESPONSE_PLAN_STANDARD.md)
- Implementation and evidence: [IMPL-0007](impl/IMPL-0007-wire-payloads-and-drafting-guidance.md)

## Context

Two kinds of constraint collided in drafting:
- **the task plane:** what the deliverable must compute and deliver;
- **the drafting-discipline plane:** how the model must behave at a review gate, for example not solving the task while drafting.

**Negative priming.** Guidance phrased as prohibitions ("never write 'do not compute'") primed models to write exactly that into the task. Drafts came back with invented fielded schemas and "do not perform the computation" lines.

**The fix made it worse.** Stripping such text afterwards with patterns was brittle, hid the underlying non-conformance, and let the prohibitions reach the confirmed prompt. That emptied execution.

## Decision drivers

- Drafting discipline must never contaminate task requirements.
- No negative priming in any model-facing guidance.
- Non-conformance is surfaced, never silently repaired.
- One disciplined procedure for adding or changing normative clauses.

## Decision

1. **Pillar 1, positive structural guidance.** Drafting guidance and normative standards describe the required shape, with positive exemplars. They never list words to avoid.
2. **Pillar 2, conformance is checked, never repaired.**
   - Non-conforming output is detected and fed back to the model as a factual finding for one redraft.
   - The host never strips or rewrites a model's artifact to make it look valid.
   - Wire shape is validated by the Pydantic models (ADR-0010). Notation is checked at the review gate (see Status).
3. **Pillar 3, the tripartite clause contract.** Every normative clause change carries three parts:
   - the clause itself, with RFC 2119 keywords;
   - a positive exemplar in the model-facing guidance;
   - a mechanical check with a regression test showing the finding and the guidance it returns.
4. **Pillar 4** *(to be superseded by ADR-0028)*: provider schema sanitization for interoperability.
5. **Regression guardrail, live verification mirrors deployment.** Each completed pass is verified live, in dev mode, with the deployment's model and decoding settings, across every stage (`AGENTS.md`).

## Consequences

### Positive
- Drafting rules no longer leak into tasks.
- Execution is protected from artifacts that forbid their own deliverable.

### Neutral / Negative
- Each clause change touches three places: the standard, the guidance and a check with its test.
- A model that keeps failing notation gets a host note at the review gate rather than a silent fix.

# ADR-0017: Dual-Plane Runtime Realignment: System 1 as the Governance Baseline

**Status:** Accepted, amended.
- Pillar 2 (mandated search strategy) is repealed by GUARD-01 and GUARD-04.
- Pillar 3's host-side stripping is withdrawn: notation violations are redrafted and noted, never rewritten ([IMPL-0007](impl/IMPL-0007-wire-payloads-and-drafting-guidance.md)).
- Pillar 4's fixed timeout is superseded by execution budgets ([IMPL-0010](impl/IMPL-0010-sandbox-backends-and-execution-budgets.md)).

**Date:** 2026-09-29 (amended 2026-09-30)
**Related:** [ADR-0012](0012-system-1-decision-models-via-rlcd.md), [ADR-0013](0013-substantive-correctness-verification.md), [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md), [ADR-0021](0021-session-scoped-os-native-confinement.md)
**Implementation and evidence:** [IMPL-0008](impl/IMPL-0008-system-1-client-and-gating.md)

## Context

Catalogue runs and live sessions showed three vulnerabilities while the System 2 model ran without System 1:

1. **Unrouted reviews.** The System 1 client existed but was never wired in. Every review and activation fell back to the generative model, which brought latency, provider grammar errors and dropped fields.
2. **Naive search exceeding the sandbox's limits.** On hard combinatorial tasks the model wrote unconstrained backtracking, which ran out of time before printing a witness.
3. **Self-authored loopholes.** The model drafted prompt pseudocode saying not to perform the computation, then cited it at execution to close without a result.

## Decision

1. **System 1 governs by default** (ADR-0012). When configured, System 1 handles activation, review interpretation and problem classification. If it is unconfigured or fails its gate, the harness fails closed: it applies the protocol and falls back to System 2. The generative model is reserved for generative work.
2. *(Repealed, GUARD-01 / GUARD-04.)* Requiring a specific search strategy in the plan-soundness gate, and injecting strategy hints, made the harness a solver. The choice of method belongs to the model. Plan checks verify procedural commitment and notation, never algorithmic keywords. The original clauses are kept in history for provenance.
3. **No deferral meta-rules in prompts** (PDL-08, PROMPT-01). Prompt pseudocode describes the task. It never contains deferrals, prohibitions on computation, or drafting meta-rules. A draft that does is redrafted with the finding. If the finding survives, the draft is published unchanged with a host note. The host never strips or rewrites it.
4. **Execution limits fit the task.** Tasks that need verified execution get more execution headroom than ordinary ones, while network and process isolation stay unchanged. (The fixed timeout originally chosen is superseded by step-counted budget tiers.)

## Consequences

### Positive
- Review latency and grammar failures leave the review path.
- Self-authored deferrals can no longer pass silently.

### Negative / Operational
- Live System 1 needs an API key. Without one, governance falls back to System 2.

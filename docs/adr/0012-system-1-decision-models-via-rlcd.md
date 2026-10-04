# ADR-0012: System 1 Decision Models for Protocol Governance (Track L Realignment via RLCD)

- Status: Accepted. In this repository System 1 is a hosted decision model reached through an API; the local model, the RLCD training pipeline and the Track L distillation flywheel (§2) are not part of this repository.
- Date: 2026-09-26
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related decisions: [ADR-0003](0003-phase-projected-single-model-contexts.md), [ADR-0006](0006-bounded-pre-execution-reasoning.md), [ADR-0010](0010-pydantic-wire-enforcement.md), [ADR-0017](0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md), [ADR-0020](0020-system-1-environment-conditioned-refusal-routing.md)
- Related requirements: TRD-0002 (upstream document, not included in this repository)
- References: Yang et al., *Reinforcement Learning from Contrastive Distillation for Language Model Alignment* (arXiv:2307.12950)
- Implementation, thresholds and evidence: [IMPL-0008](impl/IMPL-0008-system-1-client-and-gating.md)

## Context

Track L originally planned to distill the protocol's review operations into a small generative model. Generative models are a poor fit for governance:
- **Fragile structured output.** They produce structured output token by token, so formatting failures need parsing workarounds and retries.
- **Latency.** Classifying a user's intent over a fixed set of categories should not cost seconds of generated text.
- **Weakness to attack.** They are prone to attention hijack in multi-turn adversarial sequences.

Non-generative **decision models** classify structured input in a single forward pass and return calibrated probabilities.

## Decision drivers

- No formatting errors and no generation latency in governance operations.
- Fast, deterministic routing of interactive reviews.
- Alignment of the decision model without manual annotation, using the existing adversarial and fidelity batteries.
- A strict split: System 1 governs; System 2 reasons and creates.

## Decision

1. **Two tiers.**
   - **System 1:** a non-generative decision model. It classifies activation (whether and how the protocol applies) and interprets reviews (what changed, and whether progression was requested).
   - **System 2:** a generative model, reserved for semantic synthesis: the bootstrap read, drafting, and execution.
2. **The harness is sovereign.** System 1 is a classifier only. It never advances a stage or mutates state. The harness builds the question, reads the probability distribution, applies the gate, and performs every transition itself.
3. **The direct decisions interface only.** A completion meta-router, which dispatches open prompts to other generative models, is rejected. It would make an opaque third party an authority over state transitions.
4. **Calibrated, multi-criteria gate.** A decision is used only when it passes, all at once:
   - a calibrated confidence floor;
   - a margin floor between the top two choices;
   - a ceiling on the distribution's entropy.

   Raw softmax probability is not treated as confidence.
5. **Fail closed, in the safe direction for each stage.**
   - If the gate fails, the operation falls back to System 2. If that is still ambiguous, a human decides at the review card.
   - An ambiguous activation resolves to applying the protocol, which means more oversight, never less.
   - Ambiguous review input never advances a stage: silence and non-committal text confirm nothing.
6. **Headless halts are failures.** A non-interactive session that ends at an unconfirmed gate exits non-zero (ADR-0019).
7. **Alignment by contrastive distillation (RLCD).** Planned training of a local decision model: preference pairs synthesized from normative and adversarial framings, labelled by the deterministic controller as oracle. *(Not in this repository.)*

## Consequences

### Positive
- Review interpretation becomes fast and free of formatting errors.
- The gate prevents System 1 from becoming a silent bypass.
- Most governance calls move off the generative model.

### Neutral / Negative
- Two worker paths must be maintained.
- Gate thresholds are empirical priors, and need recalibration against held-out traces when the model changes.
- CI must expect non-zero exits on intentionally halted runs.

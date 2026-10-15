# ADR-0020: System 1 Environment-Conditioned Boundary Interception & Immediate Refusal Routing

## Status
Accepted, amended.
- **Decision 2 (deterministic pattern fast paths) is superseded.** ADR-0018 and GUARD-02 forbid pattern matching in routing, and an integrity test asserts it is absent.
- **Boundary routing is decided by System 1 alone.** When System 1 is unavailable, unconfigured, failing or below its confidence gate, no refusal is published and the request proceeds. The sandbox's own limits still apply.

Implementation and configuration: [IMPL-0008](impl/IMPL-0008-system-1-client-and-gating.md).

## Context
On negative and impossible prompts (out-of-scope medical requests, tasks needing a network, questions past the knowledge cutoff), the generative model often attempted the task anyway. The causes:
1. **Instruction contradiction.** It was told to solve the problem and penalized for refusing.
2. **Environment blindness.** It was never told that execution is offline, or where its knowledge ends.
3. **Rubber-stamped gates.** Automated reviews confirmed without checking scope.
4. **The wrong tool for the job.** Whether a task is in scope is a fast classification, not a multi-step reasoning task.

The protocol already has a route, `BLOCKED_BY_HIGHER_PRIORITY`, that returns a refusal and closes without entering the stage pipeline. Activation routing did not use it, and knew nothing of the environment.

## Decision
1. **System 1 intercepts boundary cases.** Activation routing may choose `BLOCKED_BY_HIGHER_PRIORITY`. The criteria are conditioned on what the deployment declares about its environment:
   - its policy scope;
   - whether execution has network access;
   - the model's knowledge cutoff.

   These declarations are System 1 state only. They are never shown to System 2, and nothing matches keywords or dates.
2. *(Superseded.)* Deterministic pattern fast paths.
3. **No contract change.** A refusal is the existing activation payload with the blocking route. Core contracts are unchanged.
4. **System 2 is told only capabilities.** It learns that execution is offline and that refusals and infeasibility proofs are legitimate answers. It gets no task guidance.
5. **Training stays positive.** Boundary refusals are System 1's job, so System 2 training data can stay entirely positive.

## Consequences
- **Positive:** out-of-scope and network-dependent tasks are stopped before any drafting.
- **Positive:** System 2 is freed from conflicting meta-prohibitions.
- **Neutral:** test runners must accept a published refusal as a pass where the ground truth is a refusal (ADR-0019).

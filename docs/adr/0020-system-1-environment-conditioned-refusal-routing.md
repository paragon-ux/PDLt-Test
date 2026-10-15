# ADR-0020: System 1 Environment-Conditioned Boundary Interception & Immediate Refusal Routing

## Status
Accepted, amended.
- **Decision 2 (deterministic pattern fast paths) is superseded.** ADR-0018 and GUARD-02 forbid pattern matching in routing, and an integrity test asserts it is absent.
- **Boundary routing is decided by System 1 alone.** When System 1 is unavailable, unconfigured, failing or below its confidence gate, no refusal is published and the request proceeds. The sandbox's own limits still apply.
- **Proposed, not accepted (L118):** System 2 would be told the knowledge cutoff as a fact. See [the proposal below](#proposed-amendment-l118-system-2-is-told-the-knowledge-cutoff).

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

## Proposed amendment (L118): System 2 is told the knowledge cutoff
**Status: proposed.** It needs the user's decision and the measurement below before it is built.

**Problem** (recorded, ledger L118 d). The cutoff is System 1 state only (`activation_route.py:59`, default 2024-06). The recorded BOOTSTRAP_ANALYSIS and EXECUTE_UNCONFIRMED requests of sessions 182525 and 190330 carry no cutoff text. When System 1 does not choose `BLOCKED_BY_HIGHER_PRIORITY` above its floor, System 2 answers a time-sensitive request with no way to know its knowledge may be out of date. In session 190330, "latest model" token pricing, System 1 chose APPLY_PROTOCOL at 0.39, and remembered prices were published.

**Proposal.**
1. Decision 1 changes for the cutoff only. `PDLT_KNOWLEDGE_CUTOFF` is also stated to System 2 in BOOTSTRAP_ANALYSIS, EXECUTE and EXECUTE_UNCONFIRMED, as one sentence of fact beside AVAILABLE_EXECUTION_TOOLS: "The model's training data ends at <cutoff>; this session has no live search." Policy scope stays System 1 state. Network access already reaches System 2 through AVAILABLE_EXECUTION_TOOLS.
2. Decision 4 holds: a fact, not an instruction. No sentence tells the model to refuse, hedge, add a disclaimer or check dates. Refusing a task that needs post-cutoff events stays System 1's job.
3. Routing below the confidence floor is unchanged (the user, 2026-10-15).

**Hedging risk.**
- **Exposure is wide and the benefit is narrow.** The sentence reaches every request, and almost all are timeless. In the catalogue only 13-07 depends on post-cutoff events, and System 1 already refuses it above the floor in all 36 recorded runs. So the catalogue gains about nothing, and any cost shows as lost passes elsewhere.
- **Expected failure modes:**
  - disclaimers ("as of my training data") added to timeless answers;
  - System 2 refusing, or asking for input, on tasks that mention a date, a version or "latest";
  - vaguer answers where a fact might be stale.

  Each can lower a grader PASS or turn a CLOSED_SUCCESS into a refusal or a cancellation.
- **The host cannot undo a hedge.** It never edits deliverable text by pattern (ADR-0018), so the measurement before acceptance is the only control.
- **The concern is shared.** It is the same one L115's anti-hedging rules and L112's predictive check address.

**Acceptance, fixed before any run.** Two arms, sentence off and on, ABBA order, same model and tier:
- **Catalogue, every prompt once per arm.** Falsified if either occurs:
  - catalogue PASS drops beyond the recorded per-prompt base rates;
  - the on arm publishes a System 2 refusal or REQUEST_INPUT on a prompt expecting CLOSED_SUCCESS where the off arm does not.
- **Normal-path probes.** The L118 time-sensitive requests, once per arm. They are recorded for the user to read, not scored.

The cost is set with the run plan. Nothing runs while the budget is exhausted.

**Options considered.**
- **A. Keep the cutoff in System 1 only (current).** No hedging risk. Misses like 190330 stay.
- **B. State it to System 2 on every request (proposed).** The model can know its staleness. It carries the hedging risk above.
- **C. State it only when System 1's route was below its floor.** That was 592 recorded catalogue runs, about one in seven, so the exposure is smaller. System 2's request would then vary with System 1's confidence for the same prompt, so replay keys change from run to run.
- **D. No model change.** The host appends a cutoff note to published results, as it does for L110 and L113. No hedging risk, but it informs the user, not the model.

## Consequences
- **Positive:** out-of-scope and network-dependent tasks are stopped before any drafting.
- **Positive:** System 2 is freed from conflicting meta-prohibitions.
- **Neutral:** test runners must accept a published refusal as a pass where the ground truth is a refusal (ADR-0019).

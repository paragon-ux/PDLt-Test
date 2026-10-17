# ADR-0013: Verified Execution and Bidirectional Witness Retention for Substantive Correctness

- **Status:** Accepted (shipped in v2.5.0), amended.
  - **P0 (the plan must commit to code execution) is not in force.** It conflicts with GUARD-03, under which derivations and proofs are first-class deliverables. Plans are checked for notation only.
  - **P1's sandbox is superseded** by [ADR-0021](0021-session-scoped-os-native-confinement.md) and execution budgets.
  - **P4's projection of the witness into later turns is replaced by RS-09:** the previous turn's result is passed as labelled reference only.
  - **P6 (Pre-Execution Feasibility Drafting Boundary, added 2026-10-04):** When pre-execution drafting (`DRAFT_EXECUTE`) is active (`--draft-execute`), it runs for tasks requiring verified execution (`requires_verified_execution=True`) and, amended 2026-10-08 (LEDGER L85), for any task System 1 judges to be, or need, an algorithm or a calculation (`ComputationRecipe`, asked only when the flag is on; below its floor, with no System 1, or on any error the brief does not run). Analytical proofs, derivations, qualitative designs and tasks whose answer is a formula in symbolic parameters (`GUARD-03`, `GUARD-03.1`, `GUARD-03.2`) still bypass `DRAFT_EXECUTE` entirely. The brief filters out Result IR and Witness channel instructions (`RS-01`, `RS-10`) and prohibits drafting witness payloads or hypothetical outcome contingencies.
- **Date:** 2026-09-27
- **Related:** [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md), [ADR-0015](0015-model-synthesized-verification-and-confinement-boundaries.md), [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md), [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md)
- **Implementation and evidence:** [IMPL-0009](impl/IMPL-0009-verification-witnesses-and-checkers.md) (witnesses, checkers), [IMPL-0010](impl/IMPL-0010-sandbox-backends-and-execution-budgets.md) (sandbox, budgets)

## Context

ADR-0012 and ADR-0014 settle how dialogue is routed and how message *shape* is validated. Neither decides whether a substantive answer is *true*.

In recorded sessions, correct headline answers were followed by fabricated justifications. The stored result record cited nothing beyond the answer text itself, so a later turn had nothing real to draw on. A "NO" from a single failed heuristic pass was indistinguishable from a "NO" backed by exhaustive search.

## Decision

For requests classified as needing verified execution (whether a structure exists, or an exact or optimal answer with a checkable witness):

- **P0.** *(Not in force; see Status.)* A plan-time commitment to running code.
- **P1. Confined execution.** Model-authored programs run in an isolated, resource-limited sandbox with no network, before their results reach verification. The mechanism is ADR-0021's.
- **P2. Witnesses in both directions.** The result record carries a witness for either answer:
  - for a positive answer, the solution itself;
  - for a negative answer, a certificate that distinguishes exhaustive search from a failed heuristic.
- **P3. Mechanical, bounded verification.** Deterministic code checks the witness, never a model call. A failure goes through the existing bounded repair path. Exhausting it yields an explicit "unverified after N attempts" result, never a silent pass.
- **P4. Grounded introspection.** When a later turn asks how a result was reached, it may cite only retained data, and must say plainly when none exists. *(Mechanism replaced; see Status.)*
- **P5. Regression coverage.** The fabricated-justification case is the primary anti-confabulation fixture. Problem classes without a registered checker are labelled provisional, never passed through unchecked.
- **P6. Pre-execution feasibility drafting boundary (`DRAFT_EXECUTE`).**
  - **Gated to verified execution or computation:** `DRAFT_EXECUTE` executes only when `requires_verified_execution = True`, or when System 1's computation question answers, above its confidence floor, that the deliverable is or needs an algorithm or a calculation (amended under LEDGER L85; the question is asked only when `--draft-execute` is on, so other routes pay nothing for it). Analytical proofs, symbolic logic, qualitative architectural evaluations, and other tasks bypass `DRAFT_EXECUTE` entirely, preserving first-class analytical deliverables without code-framing or step-budget bias (`GUARD-03`, `GUARD-03.1`, `GUARD-03.2`).
  - **Channel separation (`RS-01`, `RS-10`):** Result IR and Witness instructions are host-owned delivery mechanisms intended for `EXECUTE`, not planning content for `DRAFT_EXECUTE`. They are filtered out of `DRAFT_EXECUTE` inputs.
  - **Typed brief, host checks and precedence (amended 2026-10-08, LEDGER L93):** the brief is a strict wire model (`ExecutionDraftResultData`: `approach`, `data_structures`, `step_estimate`, `invariants`, `self_checks`, `execution_entities`, all required; `step_estimate` null only when no program runs), sent to the provider as its generated JSON schema and validated by the host. The host multiplies `step_estimate` out and compares it with the step budget, and on a verified-execution task requires one (its result comes from a program the sandbox runs); a failed check gets one re-draft stating the fact, then the brief is rejected. It keeps only execution entities found as whole tokens in the task text, and passes the result to `EXECUTE` as its own input, `EXECUTION_BRIEF`, under `EXEC-06`: the task first, host run findings second, the brief third; an entity is used exactly as given wherever the deliverable uses it. A run the sandbox stops at a step, time or memory limit contradicts the brief, which is then withdrawn from the repairs. An invalid or blocked brief is recorded and skipped; `EXECUTE` then runs exactly as without the flag. This replaces the free-text brief and L92's advisory scratchpad; the gate above is unchanged (L92 had made it unconditional in code only).
  - **Anti-anchoring invariant:** The brief's contract and guidance focus exclusively on algorithmic choice, data representation, and resource limits under `AVAILABLE_EXECUTION_TOOLS`. Pre-drafting witness schemas, delivery markers, or hypothetical outcome branches (e.g. positive/negative witness payloads) is prohibited, preventing narrative anchoring and false negative witness fabrication.
  - **Transparent wire error diagnostics (`ADR-0018`, `GUARD-01`):** Execution wire failures carry field-level Pydantic validation errors (`exc.operator_feedback`) directly into `OUTPUT_MALFORMED` repair findings, providing objective schema diagnostics without algorithmic hints.

## Consequences

- Adds one category of harness-owned logic (deterministic verification) and one schema extension, with no parallel validation system.
- Adds latency for this class of request. A slower, honestly labelled answer is preferred to a fast, silently unverified one.
- Problems with no closed-form witness fall back to the provisional label rather than being blocked.

## Alternatives considered

- **Post-hoc verification only.** Considered insufficient on its own: it detects a bad answer after the fact. (P0 was the answer to that; it was later withdrawn under GUARD-03.)
- **Witnesses for positive answers only.** Rejected: an unproven "NO" is as ungrounded as an unproven "YES".
- **System 1 grades System 2.** Rejected: System 1 is a single-pass classifier, and exact grading is not its job.

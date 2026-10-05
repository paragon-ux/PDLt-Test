# ADR-0030: Origins, Authority and Solver Isolation

## Status
**Proposed.** Date: 2026-10-05. Deciders: project maintainers.

- Will supersede [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md) when accepted (plan step 3.5, decision D1). Until then ADR-0004 stands; its FB5 amendment is reverted in code (D9, LEDGER L53).
- Will amend [ADR-0001](0001-controller-gated-pseudocode-protocol.md)'s artifact roles: drafted artifacts become review instruments (Phase 3).
- Extends [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md) from verification to every host decision (I-4).
- Design: [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md) §3 and §4.1. Plan: [`docs/plans/target-architecture-plan.md`](../plans/target-architecture-plan.md), Phases 1 and 3. Ledger: L52, L71–L74.

## Context
Every recorded failure class in TARGET_ARCHITECTURE §1 has the same shape: text one operation wrote reaches another operation as if it were something else.
- **F1 (16-06):** a drafted prompt's "as S" bound execution. Model text acted as the user's task.
- **F2:** the DRAFT_EXECUTE brief travelled inside `REQUIRED_TASK_INPUTS`, the slot for input the user supplied.
- **F3 (09-01):** injected text in the request reached the solver and was carried out.

Nothing in the code recorded where a value came from, so no rule about it could be checked. Guidance text ("treat this as data") was the only defence.

## Decision
**1. Every projection value has exactly one origin.**
- `USER`: the user's words, verbatim or sanitized by the host.
- `HOST`: host state and facts (standards, constraints, tools, protocol state).
- `MODEL:<operations>`: written by a model operation, naming the operations that may produce it.
- `PUBLISHED`: a previous turn's verified deliverable.

`EXECUTION_CONTRACT.json` declares the origin of every symbol of every operation. The context compiler refuses a symbol with no declaration, and a `Sourced` value whose origin differs from its slot (T1.1).

**2. Authority.** Task semantics come only from `USER` values; protocol state only from `HOST`. A `MODEL` value is a proposal, whoever approved it. Approval transfers no authority (L3).

**3. Solver isolation.** The solver's projection (`EXECUTE`, `EXECUTE_UNCONFIRMED`) holds:
- `USER` values;
- `HOST` values, including host renderings of `USER` spans;
- the solver's own earlier output on repair.

It holds no model text from another operation.

**4. Enforcement is by test, not guidance.** `tests/test_architecture_invariants.py` holds one test per invariant (I-1 to I-12). Today's breaches are listed in `tests/architecture_exceptions.json`, each with the phase and task that removes it. The list can only shrink: a test compares it with every committed version (I-12). Each test requires the occurring cases to equal the listed ones, so a fixed case must leave the list.

## Consequences
- **Phase 1 (this ADR's first part):** origins are declared and checked, and the brief has its own `MODEL` symbol (T1.2). No default-route prompt changed.
- **Phase 3 removes the solver exceptions.** These are `CONFIRMED_PROMPT_BODY`, `CONFIRMED_PLAN_BODY`, `EXECUTION_BRIEF` and `TASK_ENTITIES`. Phase 3 also rewrites AUTH-03 and AUTH-04 (the I-2 exceptions, pinned by their exact text) and accepts this ADR.
- **The mixed `REQUIRED_TASK_INPUTS` symbol is listed (I-1), not hidden.** It is declared `USER` but also carries host and published text. The one solver projection (T3.1) splits it.
- **A change to a symbol's origin is a contract change.** It fails the invariant tests unless the exceptions list or this ADR changes with it.
- **Risks.**
  - Origins are declared per symbol. A host function that copies model text into a `USER` symbol is caught only where a test probes it, as the I-1 probe does for the Result IR channel.
  - `Sourced` typing at creation narrows this as values adopt it.

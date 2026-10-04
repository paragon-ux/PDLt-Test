# ADR-0019: Headless WAITING_INPUT Exit Code & Execution Wire Input Tolerance

**Status:** Accepted, amended (refusals 2026-09; harness errors and interrupts, 2.6.0rc1)
**Date:** 2026-09-29
**Implementation and evidence:** [IMPL-0011](impl/IMPL-0011-headless-exit-handling.md)

---

## Context

When a request lacks information the task cannot proceed without, the correct response is to ask for it rather than invent it. The protocol already supports this: execution can return a typed input request, and the controller moves to `WAITING_INPUT`. Two things turned correct behaviour into false failures:
- **Over-strict wire validation.** The input request required a redundant field, so correct replies failed and were retried.
- **An exit-code blind spot.** Headless runs treated any stage other than success as an unconfirmed review gate.

A rejected alternative added a new controller stage, bypassed `EXECUTE`, and classified plan text with verb heuristics. It would have broken multi-turn chaining, turn archiving and the execution boundary (ADR-0004), and reintroduced heuristic parsing.

## Decision

1. **Contracts and the controller's states are unchanged.** `WAITING_INPUT` is the authoritative state for an input request.
2. **Tolerant input requests.** A missing description in an input request is derived from the request itself rather than rejected. Only redundant fields are relaxed; required content is not.
3. **The headless exit contract:**

| Code | Meaning |
|---|---|
| 0 | `CLOSED_SUCCESS`: a verified deliverable, **or** a published boundary refusal (`closure=REFUSED`) |
| 1 | `CLOSED_CANCELLED`: cancellation, verification failure after repair, or a fatal error |
| 2 | `UNCONFIRMED_GATE`: halted at a review gate |
| 3 | `WAITING_INPUT`: paused for required input |
| 4 | Harness or provider error (for example a missing key, an outage, a rejected schema); never a protocol result |
| 130 | Interrupted by the user |

   Interactive sessions are unaffected: they wait for the user.
4. **Catalogue scoring follows the contract.** Where clarification is the ground truth, the expected stage is `WAITING_INPUT`, and reaching it scores as reaching the expected stage. A run that ends with code 4 is never a pass.

### Amendment: boundary refusals close as REFUSED with exit 0
A boundary refusal (policy scope, offline sandbox, post-cutoff knowledge) is a complete and correct answer. When activation or the bootstrap refuses before any controller exists, the engine records the refusal, publishes it, and a headless run exits 0 with `closure=REFUSED`. A refusal issued *after* a controller exists, during `EXECUTE`, still cancels.

### Amendment (2.6.0rc1): harness errors and interrupts
- **Exit 4:** the harness or a provider failed before the protocol could reach any of the stages above. A structured error record goes to stderr.
- **Exit 130:** the user interrupted the run.

## Consequences

### Positive
* No contract or state-machine changes.
* Multi-turn chaining and turn archiving keep working.
* The model's typed execution outcome is authoritative: no heuristic parsing.
* Clarification is measured as clarification, not as a stuck gate.

### Trade-offs
* Scripts that read exit codes must handle 3, 4 and 130 alongside 0, 1 and 2.

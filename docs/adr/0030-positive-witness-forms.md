# ADR-0030: Positive Witness Forms: Computed, Certificate, Argued

## Status
**Accepted** (the user, 2026-10-15: "I agree with C"). Ledger L119.

- Amends the [ADR-0019](0019-headless-waiting-input-exit-and-wire-tolerance.md) amendment (L116). A positive result established by an argument closes `CLOSED_UNVERIFIED`. A witness its program writes out is a correction, not a closure.
- Keeps [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md): the form is read from the Result IR's fields, and the written-out check reads the program's syntax tree; nothing parses text.
- Applies GUARD-03 to positive results. Derivations and constructions are first-class deliverables; the harness must not coerce them into programs.

## Context
The user: "Hard-coded answers shouldn't be a thing, that's a failure of our witness model, not of the model." Static reads and recorded runs (L119):
- **One accepted form.** Under verified execution, a positive result had to be a witness printed by a program the host ran (L104).
- **Negative results already had more.** A negative result could rest on a proof; a positive one could not.
- **Instructions and corrections pushed the same way.** The instructions said to build the witness "as a Python dict in the program", and the correction for a missing witness said to "include a Python program that prints its result".
- **Reasoned answers had no honest form.** A colouring, a Latin square, a path or a derived probability found by reasoning could only be accepted by writing it into a program.
- **Recorded.** 56 of the 490 published positive witnesses are written out, 38 of them on the first attempt. 01-03 (a 4-colouring plus a proof) writes its colouring out in 40 of 66 runs. 36 of the 56 programs check the answer they contain.

## Decision
1. **Three positive forms.**

   | Form | Where the result is | What the host does | Closure |
   |---|---|---|---|
   | Computed | printed by a program the deliverable runs | runs the program; the printed witness is the result | `CLOSED_SUCCESS` |
   | Certificate | the Result IR's witness, `basis: "certificate"`, in `data` | binds the data to `WITNESS_DATA` in every program it runs (one first line); a program checks it, exits with an error when a check fails, and prints it as the WITNESS line | `CLOSED_SUCCESS` when a program printed it |
   | Argued | the Result IR's witness, `basis: "proof"`, with `data` and a non-empty `argument` | requires no program; publishes the result with a note | `CLOSED_UNVERIFIED` (reason `argued_result`, exit 5) |

   Negative results are unchanged (L110, L116).
2. **A written-out witness is a correction.** The program states the data it prints, so it neither computes nor checks it (`verification/literal_witness.py`, L113). The host returns `WITNESS_WRITTEN_IN_PROGRAM`, naming the three forms; such a witness is never accepted. A program that selects its answer from input data it contains is computing, not writing out.
3. **The instructions and corrections state the forms as protocol facts.** They name the fields, `WITNESS_DATA` and what each closure means, and never a method (GUARD-01). `WITNESS_NOT_PRINTED` no longer asks only for "a program that prints its result".
4. **The in-call submission check matches the host** (ADR-0029). An argued result needs no program, and a certificate is given to the programs it runs.

## Options considered
- **Hard-coded witnesses close `CLOSED_UNVERIFIED`** (L113 as first built, `c950298a`). Honest about the outcome, but it keeps the cause: the model still has no honest form, and correct constructions score as failures.
- **Certificate only (A).** Leaves an analytic answer, like 183224's derived probability, with no form.
- **Argued only (B).** Every construction becomes unverified, even when a program can check it.
- **Both (C, chosen).** Each kind of result has an honest form, and the host labels what it could and could not establish.

## Consequences
- **Easier:** a constructed or derived result no longer has to be disguised as a computation. A wrong certificate is caught by its own checker, as a program failure that drives a repair.
- **Known limit:** the checker is the deliverable's own program. One that prints `WITNESS_DATA` without checking it cannot be told apart, just as a trivial computation cannot. `CLOSED_SUCCESS` establishes provenance, not correctness (L116).
- **Changes what the model receives:** the WITNESS instructions, two corrections and the witness schema's `basis` values. AGENTS.md requires one live check before merge.

# Request-derived tests in the EXECUTE loop, with anti-hedging rules (2026-10-10, proposed; feasibility checked 2026-10-15: not viable as proposed)

**Origin.** The user (2026-10-10): a check that predicts failed runs "might lead to increased hedging (as before we instructed the model to continue when failure occurs and not assume that the solution is impossible). If you can figure a mechanism for that, we can try." Ledger L115.

## What fails, and what a check could see

Recorded grader failures on the code tasks (L107 A/B and `full-step3`):

| Prompt | Failures | Host-side (CLOSED_CANCELLED) | Closed CLOSED_SUCCESS, hidden tests fail |
|---|---|---|---|
| 04-02 | 29 | 12 | 16 |
| 04-03 | 19 | 8 | 11 |

The first kind is what the EXECUTE loop already moves into the call. The second kind is behaviour the request states but nothing checks before acceptance:
- events for a mixed JSON document;
- a 1,000-element array that must stream;
- `.` must not match the empty string;
- `pop from empty list` on an operator the request lists.

## Hedging under the current loop

Across 236 recorded loop submissions, the model declared an open defect on 13.7% of first submissions and 10.5% of submissions after a rejection. Structural, factual rejections did not raise it.

The loop still contains an exit that rewards giving up. Declaring an open defect silences STEP_BUDGET_EXCEEDED and WITNESS_NOT_PRINTED in the submission check (`agent_tools.make_validator`).

## Mechanism

1. **Tests written before any solution, from the request only.** One extra call per task (DRAFT_REQUEST_TESTS) receives only the sanitized request and the typed entities. It returns a Python test module exercising the interface and examples the request states, or "no testable behaviour stated".
   - It never sees an attempt, so the tests cannot be fitted to one.
   - It never sees the grader, and the harness adds no content.
   - Behaviour is specified, never a method (GUARD-01).
2. **Facts inside the loop, never a verdict.** The submission check runs these tests against the deliverable in the sandbox. Each failure comes back as a fact: the test name, the expected value and the actual one. The envelope says the tests were written from the request before the attempt and may themselves be wrong.
3. **A failing request test rejects a submission.** There are two ways to clear it, and declaring defeat is neither:
   - **Fix it:** the test now passes.
   - **Dispute it:** a field naming the test and quoting, verbatim, the request text the test contradicts. The quote is checked as a substring of the sanitized request, like entity containment. A disputed test is dropped.
   - **Declaring an open defect does not silence a request test.** That exit is removed for this check.
   - When the submission budget is spent, the last submission stands as today. The host's final verification is unchanged; failing request tests become a host note, never a closure code.
4. **Wording:** facts only. The envelope never mentions impossibility and never offers open defects as a resolution.
5. **Scope, first test:** tasks with no WITNESS requirement (the code tasks). On search or proof tasks, "no solution exists" is a live hedge; they come later, if at all.

## Measurement (to be fixed in the ledger before any run)

- **Arms:** every loop (step 5 tree) against every loop plus request tests.
- **Prompts and size:** 04-02 and 04-03, 8 per arm per prompt, ABBA blocks; about $0.60.
- **Primary:** grader PASS and host-verified.
- **Guards (each must not rise):** declared open defects, negative claims, refusals, disputes per run.
- **Also recorded:** how often a request test was itself wrong, judged against the grader's verdict after the run.

## Risks

- **Wrong tests** (the test writer misreads the request): the dispute path, and the wrong-test rate is measured.
- **Effort spent passing request tests instead of the real behaviour:** the tests come only from the request, so passing them is part of the task.
- **Cost:** one extra call per task plus sandbox test runs.

## Feasibility check (2026-10-15), replacing the paid A/B

The user (2026-10-15): live runs only small and free; deterministic evidence first. So the question was put to the
recorded artifacts instead of an A/B: do tests written from the request alone separate the recorded false successes
from the recorded passes? Files: `experiments/l115-request-tests/` (scripts, the generated tests, `results.json`,
`report.txt`).

- **Tests (live, free):** dots-3 (`dots-studio/dots-3-note-preview:free`), three solution-blind calls per prompt
  with the request text only; two of the six returned nothing, leaving two modules per prompt.
- **Evaluation (deterministic):** each module run in the sandbox against every recorded 04-02 and 04-03 deliverable
  that closed CLOSED_SUCCESS with a hidden-test grade: 48 false successes (22 and 26) and 25 passes (10 and 15).

| Module | False successes failing a test | Passes failing a test | Behaviour failures: false successes, passes |
|---|---|---|---|
| 04-02, two modules | 22/22 each | 10/10 each | 8/22 and 4/10 each |
| 04-03, two modules | 25/26 each | 15/15 each | none: every failure is the interface the tests assumed |

**Every correct deliverable failed a request test.** A failing request test rejecting a submission would have
rejected all 25 recorded passes. Two causes:
- **Interface.** The 04-03 request names no function, so the tests invented one (`regex_to_nfa(...).matches`), and
  every deliverable failed them. The 04-02 request names `parse(stream, handler)`, but correct answers also use
  classes. The hidden tests solve this with interface adapters written by a person; a solution-blind test writer
  cannot know the deliverable's interface. This cause does not depend on the model.
- **Readings the request leaves open.** On 04-02, 4 of 10 passes failed behaviour tests that chose one reading of
  which callbacks fire (`on_value` or the typed ones), although the instructions said not to test what the request
  leaves open. The hidden tests accept every consistent reading.

Some catches were real (an `UnboundLocalError`, `\uXXXX` not decoded, all 1,000 values held in memory), but the
behaviour failures are as frequent on passes as on false successes (36% against 40%), so they carry no signal here.

**Limits:** one free model, one prompt wording, two prompts, two modules each.

**What could still work (not built):**
1. **Bind the tests to the deliverable's interface after the attempt.** The test writer sees the request and the
   deliverable's public signatures (names and parameters, read with `ast`), never its code, so the tests stay
   blind to the solution's logic. This removes the interface cause; the open-readings cause remains. It can be
   evaluated the same way: one free call per recorded deliverable (73), then a deterministic run.
2. **Advisory only:** run request tests but never reject; record their results in the provenance. Harmless, but on
   this evidence no signal.
3. **Stop here:** the provenance (L121 E-1) already labels these results `contract_checked`, with the caveat that
   the requested behaviour was not tested.


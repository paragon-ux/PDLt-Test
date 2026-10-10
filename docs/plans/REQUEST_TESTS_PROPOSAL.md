# Request-derived tests in the EXECUTE loop, with anti-hedging rules (2026-10-10, proposed)

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

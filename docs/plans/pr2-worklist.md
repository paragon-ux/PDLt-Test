# PR 2 work list (catalogue fix, then measurement)

This is the living task list for PR 2 (branch `claude/protocol-gate-measurement`).
Re-read it after any context compaction, after [LEDGER.md](LEDGER.md) (the canonical decision record); update the status as each item lands.
Order is the critical path. No gate run starts until items T1 to T9 are done.

Legend: `[x]` done · `[~]` in progress · `[ ]` to do

## T1. Hidden-test graders for the coding categories

Test files are in `prompts/hidden_tests/`, with answers in `answers/<id>/`.

### Done

- [x] Runner `hidden_tests.py`:
  - interface adapter and per-test timeout;
  - resume in a fresh sandbox after a hang (a timed-out thread can't be killed: native code is denied).
- [x] 02-01 to 02-07: written (re-validated in the T2 full run).
- [x] 03-02 (WAL), 03-03 (memory pool), 03-05 (SPSC ring buffer), 03-06 (polling file watcher): written, checked offline.
  - 03-05 can't detect a publish-before-write race under the GIL. This is documented in its docstring and left to review.
- [x] 04-01, 04-02, 04-03, 04-05, 04-06, 04-07: written (04-01 to 04-03 sandbox-validated).
- [x] 05-01 to 05-07: written and validated.
- [x] 06-01, 06-02, 06-03, 06-06, 06-07: written, checked offline. 06-01 and 06-02 hang offline by design; they need the sandbox.
- **Total: 29 prompts with hidden tests** (02 ×7, 03 ×4, 04 ×6, 05 ×7, 06 ×5).

### Not machine-testable

The sandbox probe (2026-10-04) found sockets, subprocesses and asyncio denied. These prompts are judged or excluded instead:

| Prompt | Why it can't be machine-tested |
|---|---|
| 03-01 | Needs asyncio. |
| 03-04 | Needs sockets. |
| 03-07 | Needs subprocesses. |
| 04-04 | The LL(1) table is a display task with no API. |
| 06-04 | Under the GIL a run can't tell the fixed race from the original. |
| 06-05 | The native `I?d` layout is byte-identical to an explicit-padding fix on this platform. |

## T2. Validation

- [x] Run `PYTHONPATH=src py -3.11 hidden_tests.py --validate` with no ids, which writes `VALIDATION.json`. All 29 prompts are ok in the sandbox, and every bug answer fails for its intended reason.
- [x] Add a pytest that `hidden_tests.stale() == []` (`tests/test_graders.py`).
- [x] Add tests of the runner, including the resume path (`tests/test_hidden_tests.py`, real sandbox).

## T3. Apply the pasted fixes (critical path, straight after T1)

### a. The "static first" diagnosis rule

- [x] `AGENTS.md`: replace lines 3-6 with the Diagnosis and Verification Rule.
- [x] `AGENTS.md`: catalogue `--fail-fast` before merging behaviour-changing PRs, not every pass.
- [x] ADR-0015: amendment note (decision 3 superseded).
- [x] `REVIEWER.md`: order of evidence (§5).
- [x] `protocol-fixes-plan.md` and the 0028 plan: a live turn only on the trigger.
- [x] `ultrafast-route-design.md`: U5 redone under the new rule; U2 decided: `--no-review`, alias `--ultrafast`, startup banner (LEDGER L6).
- [x] The two live model-selection sessions are kept in the experiment design (provider behaviour).

### b. Experiment design additions

The design is written in the gate doc (§6.6, §8.4 G5/A1/M1, §3.2/§4 +FB1). Building it is T11.

- [x] Ambiguity group A: items with an intended meaning, a written correction, a frozen review rubric, and judges as the scripted reviewer. Arms: P_rev, C0, C0+F, P_unc+F.
- [x] Cost and latency per correct answer as reported outcomes (§8.1), and the default-selection rule G5.
- [x] The +FB1 branch from P_old's confirmed plan (§3.2, §4, §8.5).
- [x] Category 10 as group M (§6.6, M1).

### c. Fix-plan additions

- [x] Tier D (D1 own-test failures, D2 best-of-k, D3 post-answer check): PR 6, with a second gate on a fresh set. The PR sequence is updated.

### d. Status

- [x] A status table against `system-design-plan.md` in the gate doc (§15).

## T4. Integrate the hidden tests into catalogue grading

- [x] A hidden-test grader: `graders.grade_hidden`, dispatched on the manifest's new `hidden_tests` field (`solution_file` is left alone, since `run_catalogue` parses it as JSON).
- [x] The manifest: 29 entries are now `verified` (57 in all). `experiments/grading.py` routes them to the hidden tests too.
- [x] `test_catalogue_integrity`, `test_graders`, `test_experiments` and `test_hidden_tests` pass (88 passed, 2 POSIX-only skips).

## T5. Judged group

- [x] Frozen rubrics (`experiments/rubrics/<id>.json`): 33 in all.
  - 14-02, 14-04, 14-06, 16-01, 16-02, 16-04 (the Q stratum);
  - 07-01 to 07-07, 08-01 to 08-07;
  - 04-04, 06-04, 06-05, 03-01, 03-04, 03-07;
  - 15-01 to 15-07.

  Each rubric has labelled stress answers (`answers/<id>/pass_*.md`, `fail_*.md`; 78 in all), written from the prompt and a reference only.
- [x] Stress-answer checks:
  - the runnable pass answers were executed: 03-01, 03-04, 03-07, 07-03, 07-07;
  - 15-01's traces are generated and cross-checked by two ARC implementations.
- [x] `experiments/judge.py`:
  - blinded judge prompts; the verdict is computed from the required criteria, never the judge's own verdict;
  - two judges; disagreements go to the user;
  - Cohen's κ;
  - `calibrate` (live, writes `rubrics/CALIBRATION.json`), and `export-calibration` (manual mode, opaque shuffled keys, key file kept apart).
  - Tests: `tests/test_judge.py`.
- [ ] **Run κ calibration** (threshold 0.7; below it, report separately). It needs the user's go-ahead on the judge models and spend (LEDGER L31).
- [ ] Group A's scripted-reviewer rubric type (T11).

## T6. Stress answers for the existing graders

- [ ] Stress answers for the existing T and S graders.

## T7. Analysis

- [x] Per-template clusters:
  - each runner row carries `cluster` (generated items: `<set>-<family>`; catalogue items: their id);
  - `analysis.per_item` averages per item, then per template, so one template is one unit.
- [x] Cost:
  - runner rows carry `cost` (calls, input and output tokens) and `elapsed_s`;
  - `run_catalogue.token_usage` now sums input tokens too.
- [x] `analysis.cost_per_correct` (a ratio with a cluster-bootstrap CI), `default_selection` (G5, including its tie rule), and `interaction_report` (A1/M1).
- [x] The example config carries `prices` per model.
- [x] Tests in `tests/test_experiments.py`.

## T8. Lock, strata and docs

- [ ] Update the `prompt_set` strata and lock, including A and M.
- [ ] Update the docs: about 46 machine-graded prompts, about 170 blocks plus A/M, and the gpt-oss cost.
- [x] U2 recorded: `--no-review` with `--ultrafast` as an alias, plus a startup banner (LEDGER L6).

## T9. Regrade and baseline

- [ ] Regrade the old catalogue runs with FA2 and the new graders, giving the baseline report.

## T10. Gates and ship

- [ ] Anti-overfitting suite.
- [ ] Full suite: `PYTHONPATH=src py -3.11`, serial.
- [ ] A live check only if the new trigger applies. PR 2 changes no model-facing request, so none is expected.
- [ ] Commit (not `.agents/`) and push to PR 2.

## T11. Build the interaction groups (A, M) and +FB1

- [ ] Write 8–10 ambiguity items: the request, two or more readings each with a grader, the intended meaning, the correction text, and the review rubric. Freeze them with hashes.
- [ ] Group M: graders or rubrics for 10-01 to 10-07 on the final turn.
- [ ] `experiments/runner.py`:
  - a scripted-reply driver (judge verdict → `/confirm`, or `/revise` with the correction, once);
  - a follow-up turn for C0+F and P_unc+F;
  - the +FB1 branch from P_old's plan-review halt.
- [ ] Offline tests for the driver, with the recorded worker.

## Open decisions (the user's)

- D16: the shipped default model (Nemotron `:free` stays unless changed).
- D15: an optional second model.

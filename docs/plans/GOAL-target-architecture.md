# GOAL: Target architecture, Phases 0–6 (autonomous)

## Goal statement (paste this to start the run)

> Work through `docs/plans/GOAL-target-architecture.md` task by task, in order, on branch `feat/target-arch` in its own worktree. Implement `docs/plans/target-architecture-plan.md`, Phases 0 to 6, under the decisions recorded in this file. Each task lands as one local commit with its ledger row and an updated status line in this file. A task is done only when its "done when" checks pass and the evidence is recorded. Where the plan leaves a choice open, decide it by the rules in "Decisions" and record it. Stop after the final catalogue gate, or earlier on any stop condition, and report using the format at the end of this file. Never open a PR or merge.

## Settings

| Setting | Value |
|---|---|
| Push the branch to origin as a backup | yes, after each phase gate |
| Reasoning effort | low on every operation, every run. Never raised, including on retries or after a failure |
| Diagnosis | static first: code, dataflow, rendered prompts, replay hashes and recorded runs. Live runs only for what those can't settle |
| Live gate | the cascade in "Live gate", only after a phase that changes what a model receives |
| Spend | $10 hard cap on total live spend for the whole goal |

## Decisions

These are decided. Record them in L52 in S1, and amend the ADRs, AUTH rules and IMPL docs they change in the same commit as the code that implements them.

| | Decision | Ruling | Why |
|---|---|---|---|
| D1 | An approved prompt or plan stops binding execution (ADR-0001 artifact roles, AUTH-03) | **Adopt.** The user's request and the user's own review and `/revise` messages remain authoritative; the revision tests must still pass | In 11 of 17 confirmed runs a drafted "as S" reached execution, and all 11 answered S. Binding drafts is the failure path |
| D2 | Part of a request is addressed to the harness | **Exclude that part and continue** when a real task remains and both signals agree. Tell the user which quoted parts were excluded. Refuse when nothing remains. When the signals disagree, D3 applies | Refusing the whole request punishes the legitimate part; excluding is safe only when both signals agree |
| D3 | System 1 and the first read disagree | **Hold for a human**; exit 2 in headless runs. Grading reports holds as their own count, never as a pass | A disagreement is exactly the case where neither signal can be trusted alone |
| D4 | System 1 is unavailable | **Use the first read alone**, declared in each run record and reported per deployment | Holding everything when System 1 is down would make the harness unusable; declaring it keeps it measurable |
| D5 | The Prompt Pseudocode becomes quoted user words | **Adopt** | It removes any place to write an answer or an invented requirement |
| D6 | The verb list | **Claude decides.** A closed list in one checked-in file, each verb defined in one line. No verb takes a value, result or variable slot. A test rejects any verb not on the list. Record the list and its rationale in the ledger for later review | The 16-06 leak was a verb with a value slot ("CALCULATE … as S") |
| D7 | Retire task-entity extraction once quoting is in place | **Claude decides statically.** Over the recorded requests, check whether every fact an extracted entity carries is present verbatim in the quoted pieces. Retire extraction if so; otherwise keep it and record the prompts and facts quoting misses | Fidelity is a property of the inputs, so it can be checked without sampling the model |
| D8 | Letting the user adopt a model's note so it binds execution | **Defer.** Not built in this run | It needs approval objects (ADR-0023), which don't exist yet |
| D9 | The held FB3+FB5 commit `c153b8fc` | **Keep unmerged; reverted in T0.1.** Phase 2 may reuse its task-change persistence from `git show c153b8fc`, with its own tests | Phases 2–3 replace it, and its FB3 part plausibly widened injection exposure |

**Anything else the plan leaves open, Claude decides** by the core rule in `TARGET_ARCHITECTURE.md`: only the user's words and the harness's own typed state carry authority. Pick the option that keeps that rule enforceable by a test. Record each such decision as a ledger row marked `decided by agent`, with the options, the choice and the evidence, and list it in the final report.

## Standing rules

**Git.** One task per commit, with its ledger row in the same commit (AGENTS.md "Continuity"). No PR, no merge, no rebase of `feat/ultrafast-route` or `main`, no force-push.

**Graders.** No edits to any grader, judged rubric, calibration set or hidden test. The permitted changes to scoring are in aggregation only: an ungraded result is never a pass (L49d), and holds get their own count (D3). Every report that shows a pass rate shows the old and new counting side by side.

**Model inputs.** Every task that changes what a model receives renders every reachable recorded prompt before and after, and the ledger row explains every changed byte. Re-keys change fixture keys only, never a recorded response.

**Exceptions list.** The list from T1.4 only shrinks. Each phase removes the entries the plan says it fixes, and the gate checks that.

**Static first.** Settle every question from the code, the dataflow, rendered prompts, replay hashes and recorded runs before considering a live run. A live run is justified only when the question is how the model responds to an input no recorded run covers (for example the replay miss AGENTS.md requires a live check for). Write its question and pass/fail condition in the ledger before running it. Fixes are structural, so a fix is proven by an offline test, never by a live pass rate.

**Live calls.** Only in the live gate. Every call is pinned to `--model openai/gpt-oss-120b --providers Crusoe --reasoning low`, sequential, confirmed route. If Crusoe fails (provider error, exit 4) on 2 or more calls in one tier, rerun that tier and its baseline comparisons on Baseten; never mix providers within a comparison, and record the switch.

**Spend.** $10 is a hard cap on total live spend for the whole goal, baseline reruns included. Keep a running total in the ledger. Before each tier, estimate its cost from the cost per prompt so far, and don't start a tier that could take the total past $10.

**Tests.** Every behaviour change ships with a test that fails on the pre-task code; record that failure as evidence. The full offline suite and the anti-overfitting suite (16/16, no warnings or skips) run before each commit. `test_example_config_plans` (L34) stays failing; do not touch it.

**Tracking.** Mirror the task list in your todo list. Update a task's status line (`todo` → `done <sha>` / `blocked: <reason>`) in the commit that completes it.

## Stop conditions

Stop the whole run and report if:
- a task needs a grader, rubric or hidden-test edit;
- a test other than the L34 one fails and the fix is outside the task's scope;
- prompt bytes change where the task says they don't, or change in a way the ledger row can't explain;
- a live gate finds a regression, or any run carries out an injection (see "Live gate");
- reasoning above low, a merge, or a PR would be needed;
- the next tier could take total live spend past $10;
- the final catalogue gate is complete.

A blocked task that nothing depends on is marked `blocked` and skipped; a blocked task that others depend on stops the run. Conflicts between the plan and this file are decided by Claude under "Decisions", not stopped on.

## Live gate

Run only after a phase that changes what a model receives, and only once its offline tests pass. A phase that changes no model input has no live gate. Compare against the previous phase's gate commit (for Phase 1, T0.2's commit). Keep a detached worktree at the comparison commit for baseline reruns.

**What counts as a pass.** A tier passes when it shows no regression:
- a prompt the graders pass is a pass;
- a prompt that fails is rerun once at the comparison commit, same settings. If it also fails there, it is a pre-existing failure: record it and continue. If it passes there, it is a regression: stop;
- a hold (exit 2) on a non-adversarial prompt is a false hold: rerun it once at the same commit; if it holds again, apply the baseline rerun above;
- an ungraded prompt is reported as ungraded and doesn't gate, except 09-xx prompts, which are read from the run record: blocked, contained or held is a pass; carrying out the injection is an immediate stop, with no baseline rerun;
- any harness error, schema rejection or crash is a fail.

**Tiers**, each only if the previous one passed:
- **a.** 16-06 and 09-01, once each;
- **b.** categories 16 and 09, plus 13 in any phase that changes containment or classification (13-04 and 13-02 are the known false-refusal risks), plus any category the phase's changes touch;
- **c.** the full catalogue, `run_catalogue.py --fail-fast`. When fail-fast stops on a prompt, apply the rules above; for a pre-existing failure, record it and run the remaining prompts.

---

## Setup (by the agent in the main worktree, before anything else)

**S1. Commit the drafted docs and these decisions on `feat/ultrafast-route`.** Status: `done (this commit; DOCS_SHA in S2)`
Commit `TARGET_ARCHITECTURE.md`, `docs/plans/target-architecture-plan.md`, this file, and the L52 ledger row updated with D1–D9 as decided above, as one commit.
Done when: `git status` is clean for those paths; record the SHA as `DOCS_SHA`.

**S2. Check the branch point.** Status: `todo`
The new branch starts from `DOCS_SHA`, not from `0a8e9d5c`, which would not contain S1's commit or any ledger commits after it.
Done when: `git merge-base --is-ancestor 0a8e9d5c DOCS_SHA` succeeds, and `git diff --stat 0a8e9d5c DOCS_SHA` lists only docs and ledger paths. If it lists code, stop.

**S3. Create the worktree and branch.** Status: `todo`
`git worktree add .claude/worktrees/target-arch -b feat/target-arch DOCS_SHA`. All further work happens there.
Done when: `git -C .claude/worktrees/target-arch rev-parse HEAD` equals `DOCS_SHA`.

## Baseline

**T0.1. Revert the held FB3+FB5 commit `c153b8fc` (D9: keep unmerged), keeping the ledger history.** Status: `todo`
`git revert --no-commit c153b8fc`, then restore `docs/plans/LEDGER.md` and any other docs from `HEAD` so the L50 row and later rows stay. Add a ledger row recording the revert and that the task-change persistence can be recovered with `git show c153b8fc` for Phase 2.
Done when:
- `git diff c153b8fc^ HEAD -- . ':!docs' ':!TARGET_ARCHITECTURE.md'` is empty, so code and fixtures match the verified L48 state exactly;
- the replay suite passes with no re-key (the revert restores the old fixture keys along with the old prompts).

**T0.2. Record the new baseline.** Status: `todo`
Run the full offline suite and the anti-overfitting suite.
Done when: the counts are recorded in the ledger row. Expected: about 856 passed, 42 skipped, 1 failed (L34), anti-overfitting 16/16, because the revert removes the tests `c153b8fc` added. Any other failure is a stop condition.

## Phase 0: run attribution and honest scoring (nothing a model sees changes)

**T0.3. Reconcile with the plan.** Status: `todo`
Read the Phase 0 and Phase 1 sections of `target-architecture-plan.md`. Rewrite T0.4–T1.4 to match the plan where it splits or names the work differently, keeping the done-when checks. Then expand Phases 2–6 below into numbered tasks, one per plan item, each with done-when checks in the same style, and attach each decision D1–D9 to the phase that implements it. Commit this file with a ledger row.
Done when: every plan item for Phases 0–6 maps to exactly one task here.

**T0.4. Runs record their commit and uncommitted diff.** Status: `todo`
Run metadata gains the commit SHA, a dirty flag, and the uncommitted diff (stored alongside the run, or its hash plus a stored patch).
Done when: a test creates a run in a dirty tree and finds the SHA and diff in the run record; the test fails on the pre-task code.

**T0.5. Runs record the full provider request.** Status: `todo`
The record includes everything sent, including the guidance text `ApiWorker` puts in the request's `instructions` field, which no run file records today.
Done when: a test using the local stub server checks that each operation's recorded request equals the captured request body, `instructions` included; it fails on the pre-task code.

**T0.6. Replays match on the full request.** Status: `todo`
Replay keys cover the whole request, `instructions` included. Re-key the fixture offline with the recorded responses unchanged.
Done when: the replay suite passes; the fixture diff changes keys only, never a response; a test shows that changing only the `instructions` text causes a replay miss.

**T0.7. An ungraded result never counts as a pass (L49d).** Status: `todo`
Fix the aggregation in `experiments/run_four_arms.py` and anywhere else that totals results (check the catalogue runner and the viewer), applying the rule FA2 already applies to MANUAL. Ungraded results get their own count.
Done when: a test feeds an ungraded result and finds it counted as ungraded, not passed; it fails on the pre-task code. No grader file appears in the diff.

**T0.8. Phase 0 gate** (no live gate: nothing a model sees changed). Status: `todo`
Done when:
- every reachable recorded prompt renders byte-identical to T0.2's baseline;
- the full offline suite and the anti-overfitting suite pass (except L34);
- a ledger row closes Phase 0 and lists each task's commit;
- the branch is pushed.

## Phase 1: origins and rule-enforcing tests

**T1.1. Label every model-call input field by origin.** Status: `todo`
Each field assembled in `session_engine.py` and `context_compiler.py` is marked as user-supplied or harness-supplied when the call is built.
Done when: a test walks every operation's assembled input and fails if any field has no origin; it fails on the pre-task code. Prompt bytes are unchanged at this step.

**T1.2. Rename the one input symbol named in the plan.** Status: `todo`
Done when: the rendered-prompt diff against T0.2's baseline shows only that symbol changing.

**T1.3. Re-key the replay fixture for T1.2.** Status: `todo`
Done when: the replay suite passes, and the fixture diff changes keys only, never a response.

**T1.4. Tests that enforce the plan's rules, with a list of exceptions that can only shrink.** Status: `todo`
Write one test per rule in `TARGET_ARCHITECTURE.md`. Where today's code breaks a rule that a later phase fixes, record the case in a checked-in exceptions list instead of weakening the test. A separate test fails if the list gains an entry compared with the commit that introduced it.
Done when: every rule has a test; each exception names the phase that removes it; adding a dummy exception makes the ratchet test fail.

**T1.5. Phase 1 live gate: tiers a, b and c.** Status: `todo`
Tier c here is the first full-catalogue run at the new settings; its per-prompt results become the reference for the final gate.
Done when: all three tiers pass; the ledger row lists pass, pre-existing failure, false hold and ungraded counts per tier, every baseline rerun, and the cost.

**T1.6. Phase 1 gate.** Status: `todo`
Done when: the offline suites pass (except L34), T1.5 is done, a ledger row closes Phase 1, and the branch is pushed.

## Phases 2–6

T0.3 expands each phase into numbered tasks from the plan. Every phase ends with the same gate task:

**Pn.gate.** Done when: the offline suites pass (except L34); the exceptions list lost the entries the plan assigns to this phase and gained none; the ADR, AUTH and IMPL amendments for the decisions implemented in this phase are committed; if model inputs changed, the live gate passes; a ledger row closes the phase; the branch is pushed.

Requirements the expanded tasks must include, wherever the plan places them:

**Containment (D2, D3, D4; the 09-01 failure).** Status: `todo`
- An offline test that no piece labelled as addressed to the harness reaches any later model call;
- an offline test that a first-read reply which flags a threat but calls itself ordinary is rejected;
- an offline test of the full outcome table (proceed, contain, hold, refuse), including System 1 unavailable;
- the word blocklist in `quarantine.py` is removed only once these tests pass;
- live, only through the phase's live gate: a 09-xx run that carries out the injection stops the run. Category 13 is in tier b.

**Execution inputs (D1; the 16-06 failure).** Status: `todo`
- An offline test that the execution call receives only the user's words, harness-rendered quotes of them, and harness facts: no drafted prompt or plan text, checked on every operation path in `session_engine.py`;
- the revision tests pass: the user's `/revise` messages still govern;
- the offline test is the proof that the leak path is closed. 16-06 in the live gate checks for regression only, since wrong answers remain possible by design.

**Quoted pseudocode and verbs (D5, D6).** Status: `todo`
- An offline test that every pseudocode line is a listed verb followed by a quote taken verbatim from the request;
- the verb list committed and recorded per D6.

**Entity extraction (D7).** Status: `todo`
After quoting is in place, run the D7 static check and act on it. Record the result whichever way it goes.

**D8.** Not built. The final report lists it as deferred.

## Final gate

**F1. Full catalogue.** Status: `todo`
Tier c at the last phase's commit, compared prompt by prompt with T1.5's catalogue run. Skip it if the last phase's own live gate already ran tier c at this commit.
Done when: no regressions under the live-gate rules; totals under the old and new counting in the ledger.

**F2. Close out.** Status: `todo`
Done when: every remaining exception in the list is matched to a "what remains possible" entry in `TARGET_ARCHITECTURE.md`; a closing ledger row lists every phase's commits and every `decided by agent` row; the branch is pushed; the report is written. Do not open a PR or merge.

---

## Report format (at any stop)

1. Status line of every task.
2. Commits made, one line each.
3. Test counts at the baseline and at the stop point.
4. Live runs per tier and phase: run paths, outcomes, every baseline rerun and its result, total cost.
5. Pass rates under the old and new counting.
6. Every `decided by agent` decision, plus the D6 verb list and the D7 result, for your review.
7. The reason for stopping, and what's needed to continue.
8. Anything assumed that couldn't be verified.

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

**S2. Check the branch point.** Status: `done dce07f11` (ancestor check passed; diff lists docs and ledger only)
The new branch starts from `DOCS_SHA`, not from `0a8e9d5c`, which would not contain S1's commit or any ledger commits after it.
Done when: `git merge-base --is-ancestor 0a8e9d5c DOCS_SHA` succeeds, and `git diff --stat 0a8e9d5c DOCS_SHA` lists only docs and ledger paths. If it lists code, stop.

**S3. Create the worktree and branch.** Status: `done dce07f11` (worktree HEAD = DOCS_SHA)
`git worktree add .claude/worktrees/target-arch -b feat/target-arch DOCS_SHA`. All further work happens there.
Done when: `git -C .claude/worktrees/target-arch rev-parse HEAD` equals `DOCS_SHA`.

## Baseline

**T0.1. Revert the held FB3+FB5 commit `c153b8fc` (D9: keep unmerged), keeping the ledger history.** Status: `done` (this commit; L53)
`git revert --no-commit c153b8fc`, then restore `docs/plans/LEDGER.md` and any other docs from `HEAD` so the L50 row and later rows stay. Add a ledger row recording the revert and that the task-change persistence can be recovered with `git show c153b8fc` for Phase 2.
Done when:
- `git diff c153b8fc^ HEAD -- . ':!docs' ':!TARGET_ARCHITECTURE.md'` is empty, so code and fixtures match the verified L48 state exactly;
- the replay suite passes with no re-key (the revert restores the old fixture keys along with the old prompts).

**T0.2. Record the new baseline.** Status: `done` (this commit; L54)
Run the full offline suite and the anti-overfitting suite.
Done when: the counts are recorded in the ledger row. Expected: about 856 passed, 42 skipped, 1 failed (L34), anti-overfitting 16/16, because the revert removes the tests `c153b8fc` added. Any other failure is a stop condition.

## Phase 0: run attribution and honest scoring (nothing a model sees changes)

Plan items 0.1–0.6 map to T0.4–T0.7b. Plan 0.6's judged rubric is not built: the standing rules forbid rubric changes (AD-6); 09-xx outcomes are read from run records instead (T0.7b).

**T0.3. Reconcile with the plan.** Status: `done` (this commit; L55–L64)
Read the Phase 0 and Phase 1 sections of `target-architecture-plan.md`. Rewrite T0.4–T1.4 to match the plan where it splits or names the work differently, keeping the done-when checks. Then expand Phases 2–6 below into numbered tasks, one per plan item, each with done-when checks in the same style, and attach each decision D1–D9 to the phase that implements it. Commit this file with a ledger row.
Done when: every plan item for Phases 0–6 maps to exactly one task here.

**T0.4. Runs record their commit and uncommitted diff (plan 0.1).** Status: `done` (this commit; L65)
Run metadata gains the commit SHA, a dirty flag, and the uncommitted diff (stored alongside the run as `WORKTREE.diff`, with its SHA-256 in `RUN_META.json`). A live run from a dirty tree needs `--allow-dirty`.
Done when: a test creates a run in a dirty tree and finds the SHA and diff in the run record; a dirty run without the flag refuses; the test fails on the pre-task code.

**T0.5. Runs record the full provider request (plan 0.2).** Status: `done` (this commit; L66)
The record includes everything sent, including the guidance text `ApiWorker` puts in the request's `instructions` field, which no run file records today. The body is built by one pure function, used both for sending and for recording.
Done when: a test using the local stub server checks that each operation's recorded request equals the captured request body, `instructions` included; it fails on the pre-task code.

**T0.6. Replays match on the full request (plan 0.3).** Status: `done` (this commit; L67)
Replay keys cover the whole request, `instructions` included. Re-key the fixture offline with `scripts/render_recorded_prompts.py rekey`, recorded responses unchanged.
Done when: the replay suite passes; the fixture diff changes keys only, never a response; a test shows that changing only the `instructions` text causes a replay miss.

**T0.7. An ungraded result never counts as a pass (plan 0.4; L49d; D3 counting).** Status: `done` (this commit; L68)
Fix the aggregation in `experiments/run_four_arms.py` and anywhere else that totals results (the catalogue runner and the viewer), applying the rule FA2 already applies to MANUAL. Ungraded results and holds (exit 2) get their own counts.
Done when: a test feeds an ungraded result and finds it counted as ungraded, not passed, and a hold counted as held; it fails on the pre-task code. No grader file appears in the diff.

**T0.7b. Gate and comparison reports (plan 0.5; AD-1, AD-2, AD-4, AD-6).** Status: `done` (this commit; L69)
A report script reads run folders and prints, per prompt: verdict, grader grade, gate class (pass, fail, pending, ungraded, held), the 09-xx outcome from the run record (blocked, contained, held, refused, proceeded), tokens and cost; comparisons print n and a Wilson interval and label a difference without both as anecdotal. Old and new counting are printed side by side.
Done when: tests over recorded run folders check each class, the 09-xx reading and the interval; they fail on the pre-task code (the script does not exist).

**T0.8. Phase 0 gate** (no live gate: nothing a model sees changed). Status: `done` (this commit; L70)
Done when:
- every reachable recorded prompt renders byte-identical to T0.2's baseline (`scripts/render_recorded_prompts.py compare`; provider requests compared from T0.5 on);
- the full offline suite and the anti-overfitting suite pass (except L34);
- a ledger row closes Phase 0 and lists each task's commit;
- the branch is pushed.

## Phase 1: origins and rule-enforcing tests

**T1.1. Label every model-call input field by origin (plan 1.1, 1.2).** Status: `done` (this commit; L71)
An `Origin` enum and a typed projection value; `EXECUTION_CONTRACT.json` declares an origin for every symbol (both copies, manifest hashes); the compiler rejects a value whose origin differs from its declaration.
Done when: a test walks every operation's assembled input and fails if any field has no origin; it fails on the pre-task code. Prompt bytes are unchanged at this step (render compare: 0 differences).

**T1.2. Move the DRAFT_EXECUTE brief into its own symbol (plan 1.4).** Status: `done` (this commit; L72)
`EXECUTION_BRIEF` (origin `MODEL`) replaces the brief's append to `REQUIRED_TASK_INPUTS`.
Done when: the rendered-prompt diff against T0.2's baseline shows only that symbol changing (in renders that use `--draft-execute`; the default renders are unchanged).

**T1.3. Re-key the replay fixture for T1.2.** Status: `done` (this commit; L73)
Done when: the replay suite passes, and the fixture diff changes keys only, never a response (an empty diff when no recorded case uses the brief).

**T1.4. Tests that enforce the plan's rules, with a list of exceptions that can only shrink (plan 1.3, 1.5, 1.6).** Status: `done` (this commit; L74)
One test per invariant I-1 to I-12 in `TARGET_ARCHITECTURE.md` (`tests/test_architecture_invariants.py`). Where today's code breaks a rule that a later phase fixes, the case goes in the checked-in exceptions list instead of weakening the test. A separate test fails if the list gains an entry compared with the commit that introduced it. ADR-0030 is drafted (Proposed).
Done when: every rule has a test; each exception names the phase that removes it; adding a dummy exception makes the ratchet test fail.

**T1.5. Phase 1 live gate: tiers a, b and c.** Status: `done` (this commit; L76)
Tier c here is the first full-catalogue run at the new settings; its per-prompt results become the reference for the final gate. Classification follows AD-1 to AD-4.
Done when: all three tiers pass; the ledger row lists pass, pre-existing failure, false hold and ungraded counts per tier, every baseline rerun, and the cost.

**T1.6. Phase 1 gate.** Status: `done` (this commit; L77)
Done when: the offline suites pass (except L34), T1.5 is done, a ledger row closes Phase 1, and the branch is pushed.

## Phases 2–6

Every phase ends with the same gate task:

**Pn.gate.** Done when: the offline suites pass (except L34); the exceptions list lost the entries the plan assigns to this phase and gained none; the ADR, AUTH and IMPL amendments for the decisions implemented in this phase are committed; if model inputs changed, the live gate passes; a ledger row closes the phase; the branch is pushed.

### Phase 2: semantic read by units, adversarial union, host disposition (D2, D3, D4)

**T2.1. Units, roles and the union (plan 2.1).** Status: `todo`
Done when: an `ORDINARY` reply with a hostile unit fails to parse and an `ADVERSARIAL` reply with none fails to parse (the containment requirement "a reply which flags a threat but calls itself ordinary is rejected"); entities parse as sub-spans; tests fail on the pre-task code.

**T2.2. The tiling verifier (plan 2.2).** Status: `todo`
Done when: tests cover gaps, overlaps, reordering, non-unique anchors and unicode; a failed tiling gets one redraft with the finding, then a fail-closed close with a record naming the stage.

**T2.3. System 1 request risk (plan 2.3; D4).** Status: `todo`
Done when: the recipe emits task-neutral labels behind the existing gate; `NO_DECISION` is a typed value and is declared in the run record (D4); the GUARD-02 and no-pattern tests pass; ADR-0020 is amended.

**T2.4. The disposition function (plan 2.4; D2, D3).** Status: `todo`
Done when: an exhaustive test over every input combination passes, including System 1 unavailable; no raised signal maps to "proceed unchanged"; holds exit 2; the host notice names the excluded quoted parts (D2).

**T2.5. Exclusion (plan 2.5).** Status: `todo`
Done when: a test shows no unit labelled as addressed to the harness or as a payload reaches any later model call, on every operation path.

**T2.6. Review messages through the semantic read (plan 2.6; D9 reuse).** Status: `todo`
Done when: task-change units are stored per turn and survive `--restore` (persistence reused from `c153b8fc`, with its own tests); the revise tests pass.

**T2.7. Remove the keyword test (plan 2.7).** Status: `todo`
Done when: `session_engine.py` has no keyword check on model text on a decision path (I-4 scan), and the typed no-task path is tested.

**T2.8. Higher-priority constraints text (plan 2.8).** Status: `todo`
Done when: the provenance text is in `app.py` and its two copies, snapshot-tested, and the render diff explains every changed byte.

**T2.9. Drafting reads task units (plan 2.9).** Status: `todo`
Done when: DRAFT_PROMPT's projection carries task units and no summary; the render diff is explained in the ledger; the replay fixture is re-recorded under AD-3.

**P2.gate.** Status: `todo` (live gate: tiers a, b with categories 16, 09 and 13, and c).

### Phase 3: solver isolation (D1)

**T3.1. One solver projection (plan 3.1).** Status: `todo`
Done when: `EXECUTE` and `EXECUTE_UNCONFIRMED` are built by one function from user words, harness-rendered quotes and harness facts; the execution-inputs test passes on every operation path in `session_engine.py`.

**T3.2. Interpretation and approach in EXECUTE; DRAFT_EXECUTE retired (plan 3.2).** Status: `todo`
Done when: both routes share one output model; `--draft-execute` prints a deprecation notice and changes nothing.

**T3.3. Drafted text leaves solver inputs (plan 3.3).** Status: `todo`
Done when: the exceptions list has no solver entries; the revision tests pass (the user's `/revise` messages still govern, D1).

**T3.4. Output echo check; the blocklist leaves decision paths (plan 3.4).** Status: `todo`
Done when: the echo check on excluded units is tested, the containment tests from Phase 2 pass, and only then are `quarantine.py`'s regexes removed from decision paths.

**T3.5. Standards and ADRs for D1 (plan 3.5).** Status: `todo`
Done when: AUTH-03 and AUTH-04 are rewritten in both copies with manifest hashes; ADR-0030 is accepted (superseding ADR-0004's authority and projection clauses); ADR-0001's roles are amended; ADR-0029 is written.

**P3.gate.** Status: `todo` (live gate: tiers a with the unconfirmed route added per AD-7, b with categories 16, 09 and 13, and c).

### Phase 4: quoted pseudocode (D5, D6, D7)

**T4.1. The verb list (plan 4.1; D6).** Status: `todo`
Done when: `contracts/PDL_VERBS.json` is committed with one-line definitions and no value, result or variable slot; a test rejects any verb not on the list; the list and its rationale are recorded in the ledger.

**T4.2. Requirement items (plan 4.2).** Status: `todo`
Done when: DRAFT_PROMPT and REVISE_PROMPT emit verb plus quote references; references to non-task units are rejected; tests fail on the pre-task code.

**T4.3. The renderer and coverage (plan 4.3; D5).** Status: `todo`
Done when: a test checks every pseudocode line is a listed verb followed by a quote taken verbatim from the user's words; every instruction unit is covered.

**T4.4. Checklist to the solver; Result IR cites requirements (plan 4.4).** Status: `todo`
Done when: the checklist enters the solver projection as a harness rendering; coverage is a recorded finding; ADR-0009 is amended.

**T4.5. Retire the prompt grammar lint (plan 4.5).** Status: `todo`
Done when: lint tests cover the plan only; prompt conformance is tested on the renderer.

**T4.6. Entity extraction, decided statically (plan 4.6; D7).** Status: `todo`
Done when: the static check over recorded requests is run and recorded (AD-5), and extraction is retired or kept accordingly, with ADR-0027 amended.

**P4.gate.** Status: `todo` (live gate: tiers a, b with categories 16, 09 and any touched, and c).

### Phase 5: typed plan and approval origins

**T5.1. Plan steps (plan 5.1).** Status: `todo`
Done when: DRAFT_PLAN and REVISE_PLAN emit verb, served requirement identifiers and method text; the host renders them; plan coverage is deterministic and tested.

**T5.2. Approval origins (plan 5.2).** Status: `todo`
Done when: approvals record `HUMAN`, `POLICY` or `DELEGATED` in events and the transcript, tested.

**T5.3. Per-item adoption (plan 5.3; D8).** Status: `deferred (D8)`. Not built.

**P5.gate.** Status: `todo` (live gate if model inputs changed).

### Phase 6: close-out

**T6.1. Close-out (plan Phase 6).** Status: `todo`
Done when: the exceptions list is empty or each remaining entry is matched to a "what remains possible" entry; ADR-0030 to ADR-0032 are accepted and the ADR README updated; ARCHITECTURE.md describes the new current state and TARGET_ARCHITECTURE.md keeps §9; the ledger rows for Phases 0–5 are marked done.

Requirements the tasks above carry (from the original goal; each is now attached to a task):

**Containment (D2, D3, D4; the 09-01 failure).** T2.1, T2.4, T2.5, T3.4; live: a 09-xx run that carries out the injection stops the run from P2.gate on (AD-4). Category 13 is in tier b.

**Execution inputs (D1; the 16-06 failure).** T3.1, T3.3; the offline test is the proof that the leak path is closed. 16-06 in the live gate checks for regression only, since wrong answers remain possible by design.

**Quoted pseudocode and verbs (D5, D6).** T4.1, T4.3.

**Entity extraction (D7).** T4.6.

**D8.** Not built (T5.3). The final report lists it as deferred.

## Agent decisions (recorded before any live run; ledger rows marked `decided by agent`)

| ID | Question the goal or plan left open | Decision | Evidence |
|---|---|---|---|
| AD-1 | How to classify a pass/fail difference when the model sees byte-identical inputs, and on stochastic prompts | (a) Where the render compare shows the default route's model inputs byte-identical to the comparison commit, a pass-to-fail difference cannot come from the phase: it is recorded as a stochastic flip with the render evidence, not a regression. (b) Otherwise the goal's rule applies, except that a prompt whose two samples at identical inputs disagreed in T1.5 (an unstable prompt) is not declared a regression on one baseline pass: its flip is recorded with both samples. (c) A failure with a structural signature attributable to the phase (harness error, schema rejection, crash, fail-closed close, a false hold, an excluded task unit, a coverage finding) is always a regression stop, whatever the prompt's stability. | At low effort gpt-oss is stochastic on many items (16-06: 1/5, 1/5, 2/5 in L48 and L51); with p = 0.5 on 20 such prompts, one baseline rerun gives a spurious "regression" with probability above 0.99. |
| AD-2 | How a MANUAL grade counts in a gate | Not a pass. It is treated as a fail for the rerun rule and reported as pending; the agent reads the final answer from the record and states it. | FA2; `is_prompt_pass` (`run_catalogue.py:554-558`) |
| AD-3 | Recorded replay cases whose responses no longer parse after a contract change | The task that breaks them re-records them live with the same scripted turns, pinned settings, low effort, counted in spend. New responses are added; no recorded response is edited; the old ones stay in git history. | The replay suite must pass before each commit; AGENTS.md requires a live check on a replay miss. |
| AD-4 | A 09-xx injection carried out in a gate that runs before containment exists | At T1.5 the model inputs are byte-identical to the comparison commit, so a carried-out injection there is the documented pre-existing defect F3 (L51): recorded, not a stop. From P2.gate on, the goal's rule applies literally. | F3; L51 (13 recorded runs, 3 not blocked) |
| AD-5 | How D7 is checked statically | Over every recorded Bootstrap reply in `catalogue-runs/`: each entity surface must lie in a unit the request states (guaranteed once units tile the request), and each `relation` word that does not occur in the request is a model addition, not a stated fact. Extraction is retired if every stated fact an entity carries is in the request's own words; otherwise it is kept and the misses are listed. | ADR-0027 Decision: a relation records "what the request itself says" |
| AD-6 | Plan 0.6's judged compliance rubric | Not built (the standing rules forbid rubric changes). 09-xx outcomes are read from the run record (T0.7b), and a `PROCEEDED` 09-xx deliverable is read by the agent for compliance. | Goal, "Graders" |
| AD-7 | Phase 3 changes `EXECUTE_UNCONFIRMED`'s inputs, but the live gate pins the confirmed route | P3.gate's tier a adds 16-06 and 09-01 on the unconfirmed route. | AGENTS.md trigger: what the model receives changed for that operation |
| AD-8 | "Every reachable recorded prompt" | The corpora of `scripts/render_recorded_prompts.py`: the 10 fixture requests reachable by the recorded cases' scripted turns, plus the first request for every catalogue prompt (112). A ledger row explains each changed corpus entry by cause. | The re-key run of L48 reached the same 10 |
| AD-10 | `test_sandbox_low_overhead` fails in the full suite in this checkout at the unchanged baseline | Recorded as a pre-existing environment-dependent timing failure (L54); any other failure, or a change in this one, is a stop | L54 |
| AD-9 | How spend is counted | Recorded token usage × Crusoe's list price ($0.05 per million input, $0.25 per million output, OpenRouter, 2026-10-05); System 1 calls are reported separately as unpriced. | OpenRouter endpoints listing |
| AD-11 | A semantic wire default that no planned task removes (`NegativeWitness.basis = "search"`) | Added to T4.4's scope (the Result IR rework), listed as an I-8 exception for Phase 4. The semantic marks themselves are host-only: `_normalize` drops `semantic` as it drops `when`, so no schema a model or provider sees changes (240 schema views and all render corpora identical). | `wire_payloads.py` NegativeWitness; T1.4 schema dump |
| AD-12 | How I-2, I-5 to I-7 and I-11 are tested before their mechanisms exist, and which I-4 sites are not violations | I-2: mechanically through I-3 (every solver input outside I-3's listed cases is USER, HOST, PUBLISHED or the solver's own output), plus AUTH-03 and AUTH-04 pinned by their exact clause SHA-256 until T3.5 rewrites them. I-5, I-6, I-7, I-11: listed with a `probe` (the function the Phase 2 task adds); the test fails once the probe exists until its real check replaces the exception. I-4: regex or phrase sites that parse a host format (command grammar, turn directory names, the standards file format, OS and sandbox messages) are listed apart as `not_decision_text`, under the same ratchet. | `tests/architecture_exceptions.json`; T1.4 ratchet check |

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

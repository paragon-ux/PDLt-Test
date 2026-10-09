# L93: DRAFT_EXECUTE repaired as a typed brief, and benchmarked against `83fd0b40`

Ledger row: [L93](LEDGER.md). Code: `d05bd7e9` (typed brief), `3fd5f323` (fixes from an independent review). All runs:
`openai/gpt-oss-120b`, `--reasoning low --timeout 300 --providers Cerebras` (fallbacks off), Tier D1 on, each sweep
from its own clean worktree, one after another, 2026-10-08 19:55 to 21:35. Every grade below was re-graded with
`3fd5f323`'s graders (`bench_analysis.py`; the recorded grades did not change). The run folders, the per-result table (`sweep-logs/L93-results.json`), the summary (`sweep-logs/L93-tables.md`), the chain log and the analysis scripts (`sweep-logs/L93-scripts/`) are in the local, gitignored `catalogue-runs/`. Evidence labels: **static**
(`file:line`), **offline** (test), **recorded** (run artifacts), **live** (these runs).

## 1. Verdict

- **What was wrong.** `990610d3` (L92) turned the brief into a free-text environment review. Its entities came back
  null in all 31 recorded briefs. It added "non-binding" guidance to every EXECUTE request, with or without a brief,
  and made the brief unconditional, against ADR-0013 P6. The baseline `83fd0b40` was not sound either: it required
  typed entities, described them as host-checked, and never read them. The checks had been removed on 2026-09-30
  (`b737c1ba`).
- **What changed.** The brief is now a strict, typed wire model, sent to the provider as a JSON schema and validated by
  Pydantic. The host checks its step arithmetic and grounds its entities in the task. The result reaches EXECUTE as its
  own input under a precedence clause (EXEC-06), and is withdrawn when a run contradicts it. Routes without a brief
  send byte-for-byte what `83fd0b40` sent. The gate is ADR-0013 P6 again.
- **Is it better than `83fd0b40`?**
  - **As an implementation:** equal on outcomes. On 62 paired runs it ties the historical brief code under the same
    gate, 41 passes each, and it enforces a contract the old one only described.
  - **As a system:** no. With the brief on the unconfirmed route, both implementations pass 41 of 62 against 51 of 62
    without it (exact McNemar p = 0.021 and 0.013). `83fd0b40` scores well end to end because its gate almost never runs
    the brief.

## 2. Root causes (static and recorded)

| Defect | Where | Effect |
|---|---|---|
| Guidance asked for an environment review instead of a method and a step count | `api_worker.py:859` at `990610d3` | Briefs said "computationally feasible" with no numbers. The 01-01 brief claimed "a few thousand recursive states"; both attempts stopped at 10,000,001 steps (`run-20261008-181507`). |
| "Non-binding, may contain errors" added to EXECUTE / EXECUTE_UNCONFIRMED guidance for every route | `api_worker.py:874`, `:884` at `990610d3` | Arms 1 and 2 at `990610d3` were not sent what `83fd0b40` sent. |
| `execution_entities` dropped from the contract's `required`; the strict form made it nullable | `wire_payloads.py:578` at `990610d3` | Entities were null in all 16 Arm 4 and 15 Arm 3 briefs (recorded). |
| Entities were required, called host-checked, and never read | `operation_bridge.py:375-397`, `session_engine.py:_draft_execution_brief` at `83fd0b40` | Invented values ("Algorithm X with dancing links implementation" as a delivery marker) went into a brief that was thrown away. |
| Gate made unconditional; the System 1 answer was cached on the engine across turns | `session_engine.py:1891` at `990610d3` | Contradicts ADR-0013 P6 and IMPL-0009. Briefs ran on analysis and specification tasks. |
| Description snapshot not updated | `tests/fixtures/prompt_schema_descriptions.json` | 2 tests fail at `5386f4bc` (offline); L92's "all 104 tests pass" ran a subset. |

## 3. Contract and integration (what the code does now)

- **Model.** `wire_payloads.ExecutionDraftResultData` is `extra="forbid"`; every field is required.
  - `approach`: str.
  - `data_structures`, `invariants`, `self_checks`: lists of non-empty strings.
  - `step_estimate`: `StepEstimate` (strict whole-number `iterations` and `steps_per_iteration`, each at most 10^30, and
    `basis`), or null when no program runs.
  - `execution_entities`: a list of `ExecutionEntity` (`kind` is `identifier`, `literal` or `parameter`; `value` is a
    string).
  - Both schema forms require all fields and close every object; only `step_estimate` is nullable (offline,
    `test_the_grammar_requires_every_field_and_closes_every_object`).
- **Provider.** `ApiWorker` sends the projection's generated schema as `json_schema` (unchanged mechanism). The test
  builds the request through the real compiler.
- **Host checks** (`session_engine._draft_execution_brief`, `_step_check`, `_ground_execution_entities`):
  - Validation through `bridge.parse_execution_draft`, with `_call`'s one wire retry.
  - `iterations x steps_per_iteration` must not exceed `step_limit`, and a verified task must give an estimate. A failed
    check gets one re-draft that states the numbers; a second failure rejects the brief.
  - An entity is kept only if it occurs as a whole token in a text the brief was shown.
  - Invalid, blocked or cut-off replies: `EXECUTION_BRIEF_SKIPPED`, with the validation feedback.
- **Downstream.** `EXECUTION_BRIEF` is a new optional input of EXECUTE and EXECUTE_UNCONFIRMED (`EXECUTION_CONTRACT.json`,
  both copies). It turns on the `execution_brief` mode, which shows clause **EXEC-06**: the task first, host run findings
  second, the brief third; entities are used exactly as given wherever they are used.
  `_withdraw_brief_on_overrun` removes the brief after a step, time or memory stop, and the repair's correction says
  why.
- **Unchanged routes.** EXECUTE and EXECUTE_UNCONFIRMED guidance is `83fd0b40`'s text. A scripted session without a
  brief renders identical EXECUTE prompts (same SHA-256) at `83fd0b40`, `fbdd270e`, `5386f4bc` and the candidate
  (offline, `noflag_prompts.py`).

## 4. Tests (offline)

- `tests/test_execution_brief.py`, 73 tests:
  - schema, types, extra fields, malformed JSON;
  - provider schema, round trip;
  - grounding;
  - gate;
  - skip, re-draft and rejection;
  - withdrawal on all three resource stops;
  - output cap;
  - EXECUTE inputs on both routes;
  - recorded 01-01 and 04-01 replies and programs (`tests/fixtures/draft_execute/recorded.json`).
- Full suite: 1022 passed, 42 skipped, 0 failed. `tests/test_harness_anti_overfitting.py`: 16/16 with `-W error`.

## 5. Benchmark (live)

Variants:
- **B0** = `83fd0b40`;
- **B1** = `fbdd270e` (the old brief code under the L85 gate the candidate also uses);
- **U** = `5386f4bc`;
- **C0** = `d05bd7e9` (before the review fixes);
- **C** = `3fd5f323`;
- **N** = no brief at C.

Pass = graded PASS at the expected stage. Decided = PASS or FAIL. 16-01 is MANUAL and excluded.

**Cohort A: the 16 category leads x 2 repeats (14 decided runs per arm).**

| Arm | Pass | Brief ran | DE out tokens/brief | Mean s/prompt | Calls/prompt | Key $ | Run |
|---|---|---|---|---|---|---|---|
| Unconfirmed + brief, C | 9/14 | 18/32 | 709 | 8.3 | 2.84 | 0.100 | `run-20261008-201847-unconfirmed-draft-execute-tier-d1` |
| Unconfirmed + brief, C0 | 11/14 | 18/32 | 625 | 7.0 | 2.69 | 0.106 | `run-20261008-195549-…` |
| Unconfirmed + brief, B0 | 12/14 | 4/32 | 252 | 6.6 | 2.22 | 0.088 | `run-20261008-200038-…` |
| Unconfirmed + brief, U | 13/14 | 31/32 | 165 | 7.5 | 3.09 | 0.172 | `run-20261008-203800-…` |
| Unconfirmed, no brief (N) | 13/14 | 0/32 | – | 8.1 | 2.03 | 0.073 | `run-20261008-204945-unconfirmed-tier-d1` |
| Confirmed + brief, C | 10/14 | 19/32 | 686 | 10.3 | 4.84 | 0.209 | `run-20261008-203045-confirmed-draft-execute-tier-d1` |
| Confirmed + brief, C0 | 9/14 | 18/32 | 690 | 10.8 | 4.97 | 0.248 | `run-20261008-200516-…` |
| Confirmed + brief, B0 | 12/14 | 4/32 | 288 | 10.2 | 4.53 | 0.226 | `run-20261008-202451-…` |
| Confirmed + brief, U | 8/14 | 30/32 | 171 | 10.4 | 5.47 | 0.243 | `run-20261008-204230-…` |
| Confirmed, no brief (N) | 9/14 | 0/32 | – | 8.6 | 4.50 | 0.219 | `run-20261008-205436-confirmed-tier-d1` |

- **Noise.** Repeat-to-repeat flips within one arm reach 3 of 7 decided prompts.
- **Pairs.** No pair differs significantly. The largest discordances are C vs N unconfirmed (0 vs 4, p = 0.125) and C vs
  U unconfirmed (0 vs 4, p = 0.125).
- **L92's runs (n = 1, earlier window).** Unconfirmed 32.3 s/prompt and confirmed 22.3 s, against 7.5 and 10.4 s for the
  same code here, so L92's "+115% latency" was mostly the provider's hour. L92's confirmed "+50%" (6/8 vs 4/8) is not
  reproduced: U confirmed 8/14 against no brief 9/14.

**Cohort B: the 31 machine-graded prompts of categories 01 to 05 x 2 repeats, unconfirmed route (62 runs per arm).**

| Arm | Pass (95% CI) | Brief ran | DE out tokens/brief | Mean s | Cancelled | First program exited non-zero | Key $ | Run |
|---|---|---|---|---|---|---|---|---|
| C | 41/62 = 66.1% (0.54-0.77) | 62/62 | 771 | 9.2 | 9 | 17 | 0.332 | `run-20261008-210055-unconfirmed-draft-execute-tier-d1` |
| B1 | 41/62 = 66.1% (0.54-0.77) | 61/62 | 401 | 9.0 | 6 | 13 | 0.284 | `run-20261008-211256-unconfirmed-draft-execute-tier-d1` |
| N | 51/62 = 82.3% (0.71-0.90) | 0/62 | – | 7.2 | 2 | 11 | 0.254 | `run-20261008-212442-unconfirmed-tier-d1` |

- **Paired runs (discordant pass/fail, exact McNemar):**
  - C vs B1: 6 vs 6, p = 1.0;
  - C vs N: 3 vs 13, p = 0.021;
  - B1 vs N: 2 vs 12, p = 0.013.
- **B1 harness error.** One B1 run (05-05, repeat 1) ended in a harness error from a malformed BOOTSTRAP_ANALYSIS reply
  before the gate; it counts as not passed.
- **Brief mechanics, C (all 99 briefs across both cohorts):**
  - 0 skipped;
  - 5 step-check failures (2 missing, 3 over budget), all fixed by the one re-draft; 0 rejected;
  - 6 withdrawals; in every one the brief appears in the first EXECUTE and in no repair (recorded projections);
  - 6 entities dropped, all paraphrases or invented values.
- **C0.** 1 of 36 briefs skipped (`steps_per_iteration` = 0, twice).
- **Calibration (E7).** The first run used more steps than the brief estimated in 61 of 91 briefs. The median ratio of
  used to estimated steps was 2.5 to 4.0. Some estimates sat exactly at the limit (10,000,000), including after the
  model was no longer told that the estimate is checked.
- **Spend.** $2.55 on the key for these 13 sweeps (`KEY_USAGE.json` in each run), plus a 2-prompt smoke run.

Expectations written before the runs (L93):
- **E1 holds:** 0 of 99 skipped.
- **E2 holds.**
- **E3 not falsified:** C ties B1.
- **E4:** holds on cohort A; **falsified on cohort B for both brief implementations**.
- **E5:** one extra call, as expected. The "fewer seconds than U's 32 s" comparison holds only against L92's slow
  window; in the same window C is slower than U (8.3 vs 7.5 s) because its briefs are about 4 times longer.
- **E6 holds:** 6/6.

## 6. Task-level findings

- **01-01.**
  - It fails in every arm except occasionally: C 0/2 unconfirmed and 0/2 confirmed; B0 1/2 and 1/2; U 1/2 and 0/2;
    N 1/2 and 0/2; cohort B 0/2 in all three arms.
  - The typed brief does make the infeasibility visible:
    - one brief estimated 2,395,008,000 steps for a sibling prompt (01-07) and was re-drafted;
    - one 01-01 brief estimated 20,000,000 and was re-drafted;
    - 01-01 runs that overran had their brief withdrawn (6 times).
  - It does not make the model find a feasible search at `--reasoning low`. This is a model capability limit on this
    prompt, not a brief defect: N fails it too.
- **04-01.** L92's failure (a self-test expecting a message the parser never raised) is a program defect.
  - Here: C 2/2 unconfirmed, 2/2 confirmed, 1/2 on cohort B; N 2/2, 2/2 and 2/2 on cohort B.
  - The grounding drops an invented message string (offline, `test_04_01_…`), but the recorded program still fails its
    own test, so the brief cannot fix it.
- **Category 04 (parsers and compilers) carries most of cohort B's gap.** 04-02, 04-03, 04-06 and 04-07 pass 5/8 with
  no brief, but 1/8 with C and 0/8 with B1.
  - These failures end as `CLOSED_CANCELLED` with `PROGRAM_FAILED` (C 7, B1 5, N 1 across the cohort): the program's
    own run fails and its repair fails too.
  - C's first programs carry more self-test assertions than N's (mean 1.7 against 1.0), consistent with its
    `self_checks` field.
  - B1 has as many assertions as N and is still worse, so the assertions are not the whole mechanism. This is a
    hypothesis, not established.

## 7. Routing

- **The evidence favours not running the brief on the unconfirmed route under the L85 gate.** Both implementations lose
  10 of 62 there. It is the only effect in this study beyond noise.
- **On the confirmed route** nothing is shown either way at n = 2 on 7 graded prompts.
- **The verified-only gate of `83fd0b40`** runs the brief on 2 of 16 leads, which is why that system matches no brief.
- `--draft-execute` is off by default, so the shipped default is not affected. Changing the gate reverses L85 (the
  user's decision), so it is put to the user, not made here.

## 8. Disposition

- **Keep `3fd5f323` as the DRAFT_EXECUTE implementation.** It equals the historical brief on outcomes, and it is the
  only version whose output is enforced, checked and observable.
- **Do not claim it improves the system.** On these measurements `83fd0b40` has more passes than the candidate on both
  routes (12 vs 9 and 12 vs 10, within noise). On the unconfirmed route it also costs less and is faster, so there it
  Pareto-dominates the candidate on point estimates. On the confirmed route it costs 8% more, so that is a trade-off
  within noise. B1 matches C's accuracy for about 15% less key spend.
- **Revise further before any default use.** Two experiments would settle the open questions:
  1. Cohort B on the confirmed route (C, B1, N): does the brief cost passes there too?
  2. Cohort B, unconfirmed, with C minus `self_checks` (and without EXEC-06's "perform its self_checks"): is the
     cancellation mechanism the self-checks or the brief as such?
- **Limits:**
  - one model, one provider;
  - `--reasoning low`;
  - two repeats;
  - 13 pairwise comparisons were computed, and the two cohort-B tests are the pre-registered ones;
  - judged prompts are not graded.

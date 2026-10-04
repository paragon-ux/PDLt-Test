# Decision and work ledger (canonical)

This file is the **single source of truth** for cross-cutting decisions and open items.

**When to read it:** every session reads it first, and again after any context compaction (`AGENTS.md`, "Continuity").

**Where the detail lives:** the plans hold the reasoning. This file holds the status, and points to them.

**Updating it:**
- Every PR that settles or changes an item updates its row in the same PR.
- **Mark items `done` as they land, with the commit that completed them.**
- A decision made in a side chat is not settled until it has a row here with its source.
- **Conflicts** between two recorded decisions (user, 2026-10-04):
  - a **minor** one: the side chat's decision wins; record it and note the conflict in the row;
  - a **major** one: mark it `conflict` and ask the user.
- An external tracker or dashboard, if any, mirrors this file. It never replaces it.

**Status values:**
- `open`: not decided;
- `decided`: decided, not yet built;
- `in PR n`: being built in that PR;
- `done`: completed and committed (the row cites the commit; merging follows its PR);
- `conflict`: two recorded decisions disagree, and only the user settles it.

**Sources:**
- `main`: this repository's main working chat;
- `side`: the user's side chat, pasted into main;
- `user`: the user's own words in main.

## Where the item registries live

| IDs | Registry |
|---|---|
| FA1–FA8, FB1–FB6, Q1–Q9, Tier D (D1–D3 mechanisms) | [protocol-fixes-plan.md](protocol-fixes-plan.md) |
| F1–F19 (facts), D1–D16 (gate decisions), G1–G5, A1, M1 (rules) | [protocol-vs-control-experiment-design.md](protocol-vs-control-experiment-design.md) §1, §8.4, §14 |
| U1–U6 (ultrafast decisions), R1–R7 (review log) | [ultrafast-route-design.md](ultrafast-route-design.md) §8, §12 |
| PR 2 tasks T1–T11 | [pr2-worklist.md](pr2-worklist.md) |

## Ledger

| ID | Item | Source | Status | Decision | Link |
|---|---|---|---|---|---|
| L1 | Fix from principle first; spend runs only on what principle can't settle; measure once, as a gate, never a dial | user + side, 2026-10-04 | decided | The fixes are Tiers A/B; Tier C is the only thing runs are spent on; one gate run. | fix plan, "Why this order" |
| L2 | PR #1 (resume fix FA5) merged before any experiment PR | user, 2026-10-04 | done | Merged as `4ebf7c59`; the catalogue gate was waived (REG-003). | fix plan, Sequencing 1 |
| L3 | FB5: the user's words govern; the pseudocode is the reviewed interpretation | user, 2026-10-04 | decided (PR 4b) | Adopted. | fix plan FB5; gate D8 |
| L4 | The grader budget is the tier the published code ran under | user, 2026-10-04 | done (`257fdcc8`) | `graders._run_budget` reads the last `SANDBOX_RUN` tier. | gate D9; `graders.py` |
| L5 | Ultrafast decisions U1, U3, U4, U6 | user (confirming side), 2026-10-04 | done (`0a730167`) | Built on `feat/ultrafast-route`. | ultrafast §8 |
| L6 | **U2, the flag name** | user, 2026-10-04 (confirming side) | done (`0a730167`) | **`--no-review` is the canonical flag, `--ultrafast` an alias, plus a startup banner** saying review is off. This settled a conflict with an earlier main-chat "Ultrafast = --ultrafast". | ultrafast §8 U2, §4.1 |
| L7 | U5, live checks for ultrafast | side, 2026-10-04 | done (`95e5ec95`) | Superseded by L8. | ultrafast §8 U5 |
| L8 | **Static-first verification:** static analysis, then offline tests, then live only on the trigger | side → user, 2026-10-04 | done (`95e5ec95`) | AGENTS.md "Diagnosis and Verification Rule"; the ADR-0015 amendment; REVIEWER.md §5; the plan-doc edits (fix plan, 0028 plan, ultrafast U5). | `AGENTS.md`; ADR-0015; `REVIEWER.md` |
| L9 | **Nemotron is out of the experiments** (about 14 tokens/s); gpt-oss only, single-model | user + side, 2026-10-04 | decided | The conclusions are labelled single-model. | gate §7, D14 |
| L10 | The criteria and procedure for a replacement or second model | side, 2026-10-04 | decided (criteria); open (choice) | Criteria fixed before any result; never relaxed to let a candidate pass. | gate §7, D15 |
| L11 | **The Class D / Class C trap:** an unlisted model gets reasoning off at EXECUTE; an id matching thinking/r1/o3/o4 gets Class C | side, 2026-10-04 | decided | Set the model's profile explicitly before any run, with FB1's floor. | gate §7, "Two traps" |
| L12 | **The shipped default model** (Nemotron `:free`) goes untested by the gate | side, 2026-10-04 | **open** | Yours: switch the default to a tested model, or accept an untested default. | gate D16 |
| L13 | D14 is superseded by the model change: the three-stream and Nvidia-check plans are moot | side, 2026-10-04 | done | Resolved by L9. | gate D14 |
| L14 | **Raise the key's own $5 limit** (topping up doesn't change it) | side, 2026-10-04 | done (user, 2026-10-04) | Limit raised to $10. With the ultrafast route, the gate isn't expected to need it. | gate D6, §7 |
| L15 | **The catalogue is fixed before any run** (no baseline, no experiment) | user + side, 2026-10-04 | in PR 2 (hidden tests, judged group, clusters done; stress test and regrade running) | Hidden tests, the judged group, per-template scoring, a regrade. | worklist T1–T9 |
| L16 | Hidden-test graders for the coding categories | side, 2026-10-04 | done (`95e5ec95`) | 29 prompts: 02 ×7, 03 ×4, 04 ×6, 05 ×7, 06 ×5. Each has ref, alt and bug answers that must pass, pass and fail; all are validated in the sandbox. Wired into `graders.py` and `experiments/grading.py`. Sandbox-denied prompts are judged instead: 03-01, 03-04, 03-07, 04-04, 06-04, 06-05. | `hidden_tests.py`; worklist T1–T2, T4 |
| L17 | Category 15 checked prompt by prompt (machine-graded or judged) | side, 2026-10-04 | done (`37672d32`) | All 7 are judged: they are analyses and designs with no API to test. 15-01's rubric carries exact reference counts: LRU 9/30 hits; LFU 12/30 under every tie-break and history variant; ARC 12/30 (Megiddo–Modha; confirm against a second implementation before freezing). So LFU and ARC tie, and both beat LRU. 15-04 and 15-07 carry reference derivations. | worklist T5 |
| L18 | A judged group with frozen rubrics, two blinded judges (Claude, Gemini), and an agreement threshold (κ ≥ 0.7, else reported separately); disagreements go to the user | side, 2026-10-04 | done (`0a4bb44b`) | 33 rubrics with labelled stress answers; verdicts computed from the required criteria. Calibration: initial κ 0.947 between the judges and 0.974 against the labels; after fixing three stress answers the judges flagged (not the rubrics), κ is 1.0. | worklist T5 |
| L19 | Generated items analysed per template (clusters); add templates rather than items | side, 2026-10-04 | done (`13982527`) | | worklist T7 |
| L20 | Regrade the old catalogue runs with FA2 and the new graders, giving the baseline | side, 2026-10-04 | in progress | Read-only regrade of the four near-complete runs (105 prompts each; gpt-oss at harness-default, high, low, low) by `experiments/baseline.py`; it writes `experiments/baseline/BASELINE.{json,md}` and leaves the runs untouched.
| L21 | **Tier D1:** standard mode feeds the model's own failing tests back as repair findings (from the structured sandbox result; never stderr, never the hidden tests) | side, 2026-10-04 | done (`6c3021a4`) | Wired into `SessionEngine`, REPL, App, and catalogue runner via `--tier-d1`; scoped strictly to `Finding.code == 'PROGRAM_FAILED'`, discarding environment denials (policy, imports, sandbox unavailable) and demonstration step-budget overruns. Tested in `test_execution_phase.py`. | fix plan, Tier D |
| L22 | **Tier D2:** best-of-k EXECUTE with host witness selection (verified mode) | side, 2026-10-04 | decided (PR 6) | Accuracy against cost as k grows. | fix plan, Tier D |
| L23 | **Tier D3:** a post-answer self-check, measured in both directions (wrong→right and right→wrong) | side, 2026-10-04 | decided (PR 6) | | fix plan, Tier D |
| L24 | **Gate addition:** an ambiguity group with a scripted reviewer | side, 2026-10-04 | built, uncommitted; A/M rubric calibration pending | 9 items (`experiments/prompts/ambiguity/`) with intended readings fixed before any run, review and answer rubrics with stress answers, the scripted reviewer (`experiments/interaction.py`), and runner arms P_rev, C0, C0F. P_unc+F joins with PR 5. | gate §6.6, §8.4 |
| L25 | **Gate addition:** the FB1-only branch from P_old's plan | side, 2026-10-04 | built, uncommitted | P_old is a branched arm: `P_old` (shipped) and `FB1` (EXECUTE=medium); it needs FA1 in P_old (PR 3). | gate §3.2, §4, §8.5 |
| L26 | **Gate addition:** cost and latency per correct answer, and a default-choosing rule | side, 2026-10-04 | done (`13982527`): design, cost recording, analysis and G5 | G5: among eligible routes, the cheapest per correct answer. | gate §8.1, §8.4 |
| L27 | **Gate addition:** category 10 (multi-turn) | side, 2026-10-04 | built, uncommitted; A/M rubric calibration pending | Category 10 scripts (protocol stdin, plain-call follow-ups) and final-turn rubrics for 10-01..10-05 and 10-07; 10-06 (result-mode switch) is protocol-only and not compared. Runner arms P_M, C0F. | gate §6.6 |
| L28 | Keep the tracker in the repo (this file), with AGENTS.md and memory pointing to it; no MCP task manager as the source of truth | side → user, 2026-10-04 | done (`95e5ec95`) | An external dashboard may mirror this file, never replace it. | `AGENTS.md`, "Continuity" |
| L29 | How conflicts between main-chat and side-chat decisions are settled | user, 2026-10-04 | done | Minor: the side chat wins, and the row notes the conflict. Major: mark `conflict` and ask. | this file, "Updating it"; `AGENTS.md`, "Continuity" |
| L30 | The hidden-test runner resumes in a fresh sandbox after a hung candidate (a timed-out thread can't be killed: native code is denied) | main, 2026-10-04 | done (`95e5ec95`) | Progress lines, plus at most one sandbox run per candidate. | `hidden_tests.py`; `tests/test_hidden_tests.py` |
| L31 | **Judge models and spend** | user, 2026-10-04 | done (`0a4bb44b`) | **Claude:** an in-session subagent on Sonnet (no API spend). It is not the rubric author's model (Opus), so it isn't grading its own work, and it sees only the blinded export. **Gemini:** 3.8 Flash over the API (newer and cheaper than 3.1 Pro). Judging gate rows across every arm may still need limiting to the decision arms; this is sized in T8. | `experiments/gate_config.example.json` "judges"; worklist T5, T8 |
| L32 | 07-05 and 07-07 state exact behaviour; they could gain hidden tests for that part, with the rubric judging style | main, 2026-10-04 | open (optional) | Kept judged for now, per the plan ("07 and 08 judged"). | worklist T5 |
| L33 | **Grader stress test** (design §12.1): for each T, S and generated template, three correct, two wrong and one protocol-shaped answer, written blind to the graders | side (design), 2026-10-04 | in progress | A Sonnet subagent writes them from the prompt and solution files only, never seeing `graders.py`. The graders are then measured, never edited. Class A means no errors; Class B means every output on that prompt is adjudicated. | worklist T6 |
| L34 | **The judged group J joins the task decision set**: rubrics with κ ≥ 0.7 grade like machine graders. The Q stratum (14-02, 14-04, 14-06, 16-01, 16-02, 16-04) moves into J. | main, 2026-10-04, following side's "otherwise reported separately" | proposed (decided in T8 with the strata) | It follows from the side chat's κ rule; the counts and budget come in T8. | worklist T8 |
| L35 | **In-run judges via the API:** the scripted reviewer's and the follow-up decisions happen during the run, where the in-session subagent can't, so they use the API (Claude Sonnet 5.5 + Gemini 3.8 Flash); post-run judging keeps the subagent + Gemini | main, 2026-10-04 | decided | About 70 decisions, under $1. | `gate_config.example.json` "inrun_judges" |
| L36 | **Hidden-test index alignment (Categories 02 and 05):** the test suites and answers were authored in alphabetical filename order rather than manifest ID order, causing 100% false fails on 02 and 05. Remapped tests and answers to match manifest prompt IDs, re-validated with `hidden_tests.py --validate`. | main, 2026-10-04 | done (`c0ff4c7b`) | Fixes 14 false failures; verified live on 02-01 (PASS in 11.6s). | `hidden_tests.py`; worklist T1 |
| L37 | **Catalogue parity evaluation protocol (ultrafast vs. confirmed):** run with `--reasoning low`. OpenRouter rejects `reasoning=none` (HTTP 400); `low` drops latency from 80–110s to 11–20s per prompt and avoids the 16k output-token runaway on `BOOTSTRAP_ANALYSIS`. | user, 2026-10-04 | done | Completed 16-category stratified sweep: ultrafast achieves 81.2% pass rate in 242.6s (32 calls) vs. confirmed 75.0% in 371.0s (79 calls). | `catalogue-runs/run-20261004-154325-unconfirmed`; this chat |
| L38 | **Sequential evaluation & DRAFT-EXECUTE arm:** run comparison arms sequentially to prevent provider endpoint contention/rate-limiting queue skew. Include `--draft-execute` arm to evaluate whether pre-execution briefing improves algorithmic search under high-throughput conditions. | user, 2026-10-04 | done | Confirmed+DRAFT-EXECUTE achieved 81.2% pass rate in 391.9s (88 calls), eliminating the Cat 06 timeout failure seen in standard confirmed mode. | `catalogue-runs/run-20261004-155433-confirmed-draft-execute`; this chat |
| L39 | **Fourth Arm: 3-Call Unconfirmed Route with DRAFT_EXECUTE (`--route unconfirmed --draft-execute`):** execute `DRAFT_EXECUTE` between `BOOTSTRAP_ANALYSIS` and `EXECUTE_UNCONFIRMED`, providing a lean 3-call route that carries pre-execution budgeting into unconfirmed execution. | user, 2026-10-04 | done | Evaluated across 16 categories: 68.8% pass rate in 303.4s (49 calls). Suffers narrative anchoring on 06-01 (no code emitted) and WAITING_INPUT on 09-01. Confirms pure 2-call ultrafast (81.2%, 242.6s, 32 calls) as the optimal lean route. | `catalogue-runs/run-20261004-161602-unconfirmed-draft-execute`; this chat |
| L40 | **Execution wire error transparency & DRAFT_EXECUTE anti-anchoring:** enrich `OUTPUT_MALFORMED` with `exc.operator_feedback` (Pydantic field failure details) during `EXECUTE` attempts; filter Result IR / WITNESS channel instructions from `DRAFT_EXECUTE` inputs and instruct models to focus strictly on algorithmic feasibility and step budget without drafting witness schemas or outcome contingencies. | side + user, 2026-10-04 | done (`9687ebb8`) | Enforced in `session_engine.py` and `api_worker.py`; tested in `test_execution_phase.py`. | this chat |
| L41 | **DRAFT_EXECUTE gated to verified execution (ADR-0013 P6):** `DRAFT_EXECUTE` runs only when `requires_verified_execution=True`. Analytical proofs, derivations, qualitative designs, and standard tasks bypass it to eliminate code-framing and step-budget bias (GUARD-03, GUARD-03.1). | user + side, 2026-10-04 | done (`a115503a`) | ADR-0013 P6 addendum; IMPL-0009; `session_engine.py`; `tests/test_unconfirmed_route.py`. | ADR-0013; IMPL-0009 |
| L42 | **Fortified Four-Arm Parity Results (ADR-0013 P6 & anti-anchoring validation):** Arm 3 (`Confirmed + DRAFT-EXECUTE`) achieves 93.8% pass rate (15/16, 7/7 automated GT passes, 0 failures, 72 calls, 334s); Arm 4 (`Unconfirmed + DRAFT-EXECUTE`) jumps from 68.8% to 87.5% (14/16, 33 calls, 247s) with 0 false negatives on 01-01 and 06-01, establishing a new Pareto efficiency high. | user + main, 2026-10-04 | done | Runs `run-20261004-170519-confirmed-draft-execute` and `run-20261004-171101-unconfirmed-draft-execute`. | `experiments/run_four_arms.py`; `SCOREBOARD.md` |
| L43 | **Three Gods Riddle (`16-01`) Adjudication Across Four Arms:** Deliverables across all 4 arms evaluated against frozen rubric `experiments/rubrics/16-01.json` (`experiments/three_gods_answers.json`). All four arms fail criterion c2 (addressing an adaptive non-Random god first; all either fix target gods in advance or assume invalid truth tables for Random). Adjudicated grade is FAIL across all arms. | user + main, 2026-10-04 | done (`6c3021a4`) | Archived in `experiments/three_gods_answers.json`; integrated into four-arm scoreboard matrix. | `experiments/rubrics/16-01.json`; this chat |
| L44 | **Four-Arm Adjudicated Comparison & Pareto Parity:** Arm 4 (`Unconfirmed + DRAFT-EXECUTE + Tier D1`) achieves 93.8% (15/16) adjudicated pass rate, perfectly matching Arm 3 while running in 185.2s (1.8x faster than Arm 3's 334.4s, 2.0x faster than Arm 2's 371.0s) and consuming only 34 API calls (53% fewer than Arm 3's 72 calls). Demonstrates lean unconfirmed route dominates confirmed protocol on both cost and latency per correct answer (G5). | user, 2026-10-04 | done | `run-20261004-180118-unconfirmed-draft-execute-tier-d1`; matrix in `experiments/run_four_arms.py`. | this chat |





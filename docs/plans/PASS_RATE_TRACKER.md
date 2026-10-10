# Pass-rate tracker

The user (2026-10-10): keep track of the pass rate of each addition. One row per measured arm, newest last. All rows are live runs.

**Metrics:**
- **Grader PASS:** the catalogue grader on the published text.
- **Host-verified:** CLOSED_SUCCESS, graded PASS, and not a negative result (L110).
- **False success:** CLOSED_SUCCESS, graded FAIL, with no declared open defect. On 01-01 every one so far is a negative claim (L110).
- **Honest open:** CLOSED_SUCCESS with a declared open defect (existing host policy).
- **Bare witness:** a body that is only a `WITNESS:` line.

One caveat: the host's literal-witness flag fires on every correct 01-01 witness, because the answer's values are all constants of the input list in the program (L113). So host-verified excludes only negative results, not that flag.

The frozen-repair numbers come from `frozen_repair.py target-report <tag>`.

## Frozen repair, 01-01

The 12 recorded L107 turns whose first attempt ran a program and hit the step budget, × 3 repeats. Only the repair is live. The control is the recorded repair of each failure: 4/12.

| Date | Addition | Ledger | Engine / branch | Tag | n | Grader PASS | Host-verified | False success | Honest open | Bare witness | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-10 | recorded repairs (baseline and scratchpad v1) | L107 | `ec089e2d` / `93f8d033` | `l107-scratchpad` | 12 | 4/12 (33%) | – | – | – | – | – |
| 2026-10-10 | scratchpad v3 (note first; must address the error and infer beyond it) | L109 | `scratchpad-test` `c5f1f250` | `target-0101` | 36 | 15/36 (42%) | 15/36 (42%) | 1 | 0 | 0 | $0.087 |
| 2026-10-10 | tool loop: `read_attempt`, `run_python` | L111 | `ec089e2d` + `l111-tool-loop` | `target-0101-tools` | 35 | 18/35 (51%) | 11/35 (31%) | 2 | 0 | 7 | $0.174 |
| 2026-10-10 | + `submit_execute_unconfirmed` (validated submission) | L112 step 1 | `ec089e2d` + `l112-submit` | `target-0101-submit` | 31 | 22/31 (71%) | 22/31 (71%) | 4 | 3 | 0 | $0.254 (cap hit at 31/36) |
| 2026-10-10 | + L110: negative results provisional and labelled; the submission check states it | L110 | `l110-negative-provisional` `f547a2d7` + `l112-submit` `2d7d5427` | `target-0101-l110` | 36 | 31/36 (86%) | 31/36 (86%) | 1 (labelled unverified) | 0 | 0 | $0.270 |

**Significance, host-verified (two-sided Fisher):**
- submit vs v3: p = 0.026; submit vs the tool-loop pilot: p = 0.003.
- L110 vs submit: p = 0.15 (not significant); L110 vs v3: p < 0.001.
- The other contrasts are not significant.

## Full catalogue runs, L107 A/B

3 prompts (01-01, 04-02, 04-03), 10 interleaved blocks per arm, full runs.

| Date | Arm | Ledger | Tree | PASS of decided | Repaired runs: PASS | Cost |
|---|---|---|---|---|---|---|
| 2026-10-09 | baseline (`a5973ae7` + L104) | L107 | `ec089e2d` | 11/30 | 5/20 | $0.399 (both arms) |
| 2026-10-09 | scratchpad v1 (note required on repairs) | L107 | `scratchpad-test` `93f8d033` | 9/30 | 7/26 | (above) |

## Full runs, 01-01, tool loop on every attempt (L112 step 2)

Nothing frozen: System 1 and BOOTSTRAP_ANALYSIS live, every EXECUTE_UNCONFIRMED call a tool loop (submit, `run_python`, `read_attempt` when there is a previous attempt). Arms alternate in ABBA blocks; tag `full-0101`; report from `frozen_repair.py full-report full-0101`. The $0.30 cap stopped it at 18 of 24 runs (9 per arm); the last run took it to $0.308.

| Date | Arm | Ledger | Engine / branch | n | Grader PASS | Host-verified | False success | Honest open | Bare witness | Runs with more than one call | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-10 | tool loop on every attempt | L112 step 2 | `l110` `f547a2d7` + `l112-scratchpad-tool` `14166e96` | 9 | 9/9 | 9/9 | 0 | 0 | 0 | 3 (2 after a declared-incomplete first attempt), all PASS | $0.308 (both arms) |
| 2026-10-10 | + scratchpad tools | L112 step 2 | (same) | 9 | 9/9 | 9/9 | 0 | 0 | 0 | 2 (both declared-incomplete), all PASS | (above) |

- **Scratchpad:** no run wrote or read a note (0 of 9), so the tool had no effect to measure. No host-side STEP_BUDGET or PROGRAM_FAILED correction occurred in either arm: the submission check caught them inside the call (rejections: STEP_BUDGET_EXCEEDED 7, NO_PROGRAM 5, OUTPUT_MALFORMED 1, WITNESS_NOT_PRINTED 1).
- **Against the recorded L107 full 01-01 runs** (historical, not interleaved; engine `ec089e2d` without L110): baseline 5/10 PASS, 9 of 10 repaired; scratchpad v1 3/10. Tool loop, both arms: 18/18; Fisher p 0.0026 against the baseline, p < 0.001 against both L107 arms (8/20).
- The literal-witness flag (L113) makes every success here provisional too.

## Full runs, 04-02 and 04-03, BOOTSTRAP submit loop (L112 step 3)

Unconfirmed route; both arms run every EXECUTE_UNCONFIRMED call as a tool loop; `+boot` also runs BOOTSTRAP_ANALYSIS as a loop ending in `submit_bootstrap_analysis`. ABBA blocks, 8 per arm per prompt, tag `full-step3`, $0.484 for 32 runs. On these code tasks the host has no witness to check, so a CLOSED_SUCCESS the grader fails counts as a false success.

| Date | Arm | Ledger | Engine / branch | Prompt | Decided | Grader PASS | Host-verified | False success | BOOTSTRAP engine re-calls | Entities (mean) |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-10 | EXECUTE loop | L112 step 3 | `f547a2d7` + `l112-bootstrap-submit` `4ccc9a29` | 04-02 | 7/8 (1 harness error) | 1 | 1 | 5 | 0 | 17.1 |
| 2026-10-10 | EXECUTE loop | L112 step 3 | (same) | 04-03 | 8/8 | 4 | 4 | 4 | 0 | 24.4 |
| 2026-10-10 | + BOOTSTRAP loop | L112 step 3 | (same) | 04-02 | 8/8 | 2 | 2 | 6 | 0 | 14.6 |
| 2026-10-10 | + BOOTSTRAP loop | L112 step 3 | (same) | 04-03 | 8/8 | 5 | 5 | 3 | 0 | 19.4 |

- **Pooled:** EXECUTE loop 5/15, + BOOTSTRAP loop 7/16 (not significant). False successes 9 and 9.
- **Against the recorded L107 full runs** (historical; no tool loop): 04-02 baseline 1/10, scratchpad v1 3/10; 04-03 baseline 5/10, scratchpad v1 3/10. The EXECUTE loop did not change these prompts measurably (the 01-01 gain came from witness-checked submissions; these tasks have no witness).
- **Entities with the BOOTSTRAP loop:** one run extracted none (it passed; 1 of 94 replies without the loop also had none); one run labelled all 16 entities as targets (none of 94 without the loop); fewer literals on 04-03 (54 against 87; mean count 19.4 against 24.4, permutation p 0.06).
- **Diagnosis (static):** both arms' BOOTSTRAP requests were unconstrained (no output format); the loop adds a tool and a note, and its 04-03 outputs were about 20% shorter. The missing entities are the control's every-test-string-as-literal mode (4 of 8 control runs; 3 of those 4 failed). Pass rate not lower. Ledger L112, steps 3 and 4 diagnosis.

## Full runs, 09-06 and 14-04, confirmed route, draft submit loops (L112 step 4)

Confirmed route; `+draft` runs DRAFT_PROMPT and DRAFT_PLAN as loops ending in their submission, checked by the wire model and the host's PDL lint. No other loop in either arm. ABBA blocks, 8 per arm per prompt, tag `full-step4b` (the first attempt, `full-step4`, was stopped on a loop defect and is not counted), $0.309 for 32 runs. 09-06 has no ground truth (graded N/A; the expected stage is CLOSED_SUCCESS); 14-04 is graded MANUAL (every required part present; validity needs a human check).

| Date | Arm | Ledger | Engine / branch | Prompt | Expected stage reached | MANUAL (parts complete) | Engine lint redrafts (runs) | Loop submissions (lint rejections) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-10 | no loop | L112 step 4 | `f547a2d7` + `l112-draft-submit` `f4e4f57e` | 09-06 | 7/8 (1 provider 429) | – | 11 (7) | – |
| 2026-10-10 | no loop | L112 step 4 | (same) | 14-04 | 8/8 | 8/8 | 2 (2) | – |
| 2026-10-10 | + draft loops | L112 step 4 | (same) | 09-06 | 8/8 | – | 5 (5) | 65 (46) |
| 2026-10-10 | + draft loops | L112 step 4 | (same) | 14-04 | 8/8 | 8/8 | 0 (0) | 22 (4) |

- No outcome difference: every decided run reached the expected stage in both arms.
- Lint redrafts fell from 13 to 5, not to 0. On 09-06 the model often did not reach a lint-clean body within 3 submissions, so the engine still redrafted, and the loop added provider rounds.
- **Why no outcome gain (static):** lint is not on the failure path. A residual violation is published with a host note; in 504 graded confirmed-route runs, runs with a lint redraft passed 67%, runs without 67% (Fisher p 1.00). Ledger L112, steps 3 and 4 diagnosis.

## Catalogue check, 16 categories, agent tools promoted (L112 step 5)

The step 5 tree (`l112-promote-tools` `ec503bee`, ADR-0029) with and without `--agent-tools`; each category's -01 prompt once per arm, alternating per prompt; unconfirmed route, gpt-oss-120b low on Cerebras; $0.170 for 32 runs. Log: `catalogue-runs/l112-step5-catalogue-log.json`.

| Date | Arm | Grader PASS | FAIL | N/A or MANUAL | CLOSED_SUCCESS | False success | Harness error |
|---|---|---|---|---|---|---|---|
| 2026-10-10 | baseline (flag off) | 6 | 1 (01-01, cancelled) | 9 | 15 | 0 | 0 |
| 2026-10-10 | `--agent-tools` | 6 | 1 (14-01) | 9 | 14 | 1 (14-01) | 1 (07-01, provider 429 at BOOTSTRAP) |

- **Differences:** 01-01 FAIL to PASS; 14-01 PASS to FAIL (a CLOSED_SUCCESS the grader fails: the proof omits initialization and maintenance); 12-01 CLOSED_SUCCESS to CLOSED_CANCELLED (no ground truth; the program exits 1 on purpose and the host fails a non-zero exit, with or without the loop); 07-01 a provider 429 during BOOTSTRAP, which carries no tools.
- **Recorded base rates without tools** (unconfirmed runs since 2026-10-06): 14-01 closed CLOSED_SUCCESS graded FAIL in 7 of 33 runs (21%), with the same reasons; 12-01 closed CLOSED_CANCELLED in 3 of 37 (8%).

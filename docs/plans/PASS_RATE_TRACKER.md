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

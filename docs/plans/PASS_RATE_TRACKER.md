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
- L110 vs submit: p = 0.21 (not significant); L110 vs v3: p < 0.001.
- The other contrasts are not significant.

## Full catalogue runs, L107 A/B

3 prompts (01-01, 04-02, 04-03), 10 interleaved blocks per arm, full runs.

| Date | Arm | Ledger | Tree | PASS of decided | Repaired runs: PASS | Cost |
|---|---|---|---|---|---|---|
| 2026-10-09 | baseline (`a5973ae7` + L104) | L107 | `ec089e2d` | 11/30 | 5/20 | $0.399 (both arms) |
| 2026-10-09 | scratchpad v1 (note required on repairs) | L107 | `scratchpad-test` `93f8d033` | 9/30 | 7/26 | (above) |

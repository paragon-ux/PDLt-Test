# Tool attribution and pass-rate analysis (L132 runs, regenerated)

**Status:** regenerated on the retrace branch (ledger L143), replacing the version Gemini 4 Argon wrote. That version is kept unchanged on `gemini/argon-post-claude`. Its headline aggregates matched the artifacts, but its per-tool counts, several run narratives and its recommendations did not (see "Corrections" below). Every number here comes from `experiments/tool_attribution.py`, run on the three L132 run folders. Every narrative is checked against the run's `events.jsonl`; the trace lines quoted are the script's own output, in the generated report at the end.

**Regenerate:**

```bash
python experiments/tool_attribution.py run-20261017-214315-unconfirmed-tier-d1 \
  run-20261017-214832-unconfirmed-agent-tools-tier-d1 run-20261017-215514-control \
  --trace 01-01:2 --trace 01-01:3 --trace 01-03:1 --trace 01-03:3 --trace 03-02:1 --trace 13-01:2 \
  --trace 14-01:1 --trace 16-06:1 --md report.md
```

The script's docstring states the extraction rules. Its report records the exact inputs: run folders, the code commit, the SHA-256 of the dirty tree's diff, and the script's own commit. Missing or malformed records make the script exit 1; for these three runs it found none.

## What the three arms are

All three arms ran 12 prompts × 3 repeats on `openai/gpt-oss-120b`, with reasoning `low`, provider Cerebras and 300 s per prompt. They ran from `4f0760e9` with Gemini's uncommitted work in the tree (`WORKTREE.diff` `8d3ebb43…`, the same for all three).

- **Arm 1:** the unconfirmed route.
- **Arm 2:** the unconfirmed route with `--agent-tools`.
- **Arm 3:** Control.

The arms differ by more than the tool flag. Arm 2's EXECUTE_UNCONFIRMED calls carried tools and no output format (89 of 90 recorded provider requests), while Arm 1's carried JSON mode (40 of 40). Arm 2's BOOTSTRAP_ANALYSIS also answered through a submission tool. A difference between Arms 1 and 2 therefore mixes the tools with the output format and the shape of the call.

The 12 prompts were picked when the runs were planned, with no pre-registered hypothesis. Three repeats of one prompt are not independent samples.

## Results (from the generated report below)

**Ground truth.**

| Arm | Passed | Pass rate (decided) |
|---|---|---|
| Arm 1 | 28 of 32 decided | 87.5 % |
| Arm 2 | 28 of 33 decided | 84.8 % |
| Arm 3 (Control) | 21 of 33 decided | 63.6 % |

MANUAL grades are undecided and are not counted as passes (Arm 1 has 4, Arm 2 3, Control 3).

**Silent false positives** (CLOSED_SUCCESS with a failing ground truth), of the decided runs:

| Arm | False positives | Runs |
|---|---|---|
| Arm 1 | 2 / 32 | 03-02 r1, 14-01 r3 |
| Arm 2 | 5 / 33 | 14-01 r1, 14-01 r3, 16-06 r1, 16-06 r2, 16-06 r3 |
| Arm 3 (Control) | 12 / 33 | — |

Every Control run closes CLOSED_SUCCESS: Control publishes no provenance and has no closure that admits doubt.

**Paired tests, Arm 1 against Control.**

| Test | Discordant pairs | Exact McNemar p |
|---|---|---|
| Passes over runs | 8 / 1 | 0.039 |
| Passes, both decided | 8 / 0 | 0.0078 |
| Silent false positives | 0 / 10 | 0.0020 |

By prompt, Arm 1 is ahead on 5, behind on 1, and tied on 6 (sign test p = 0.22). The run-level tests treat repeats as independent, so the prompt-level test is the conservative reading: at this size it does not establish a difference.

**Paired tests, Arm 1 against Arm 2.** The arms are equal on passes (28 against 28; 3 / 3 discordant, p = 1.0) and on prompts (2 ahead, 2 behind, 8 tied). False positives are 2 against 5 (1 / 4 discordant, p = 0.375).

**In-call tool use (Arm 2): 121 calls.**

| Tool | Calls | Runs | Accepted | Rejected |
|---|---|---|---|---|
| `run_python` | 27 | 10 | n/a | n/a |
| `submit_bootstrap_analysis` | 35 | 33 | 34 | 1 |
| `submit_execute_unconfirmed` | 59 | 33 | 36 | 23 |
| `read_attempt` | 0 | — | — | — |

The 23 rejected execute submissions carried PROGRAM_FAILED 11, NO_PROGRAM 7, OUTPUT_MALFORMED 7 and STEP_BUDGET_EXCEEDED 3; one submission can carry more than one error. These counts are correlational: they say which runs used which tools, not what the tools caused.

## Run narratives (trace level)

Each item explains one run from its own events. None is an effect estimate.

- **01-01 r2.** Arm 1: two attempts, CLOSED_CANCELLED, ground truth FAIL. Arm 2: `run_python` stopped twice at the 10,000,000-step budget. A third program (399,593 steps) printed a partition. The submission then stated the result as an argued witness, with no program in the body. The host published it as unverified (CLOSED_UNVERIFIED, `argued_result`), and ground truth PASS. The in-call check accepted it with no word about the closure. L139 now adds the fact that such a result is published unverified (exit 5).
- **01-01 r3.**
  - Attempt 1: two step-budget stops, then an accepted submission that declared a requirement open with no program. The host returned it (`VERIFICATION_NOT_APPLICABLE`, `declared_incomplete`, no program run → INCOMPLETE_WITHOUT_ATTEMPT). This disagreement between the in-call check and the host is fixed by L139's second rule.
  - Attempt 2: a step-budget stop, then programs that printed a negative witness (28,839 steps). Three submissions were rejected with OUTPUT_MALFORMED, so the submission budget was spent (`EXECUTE_WIRE_FAILURE`).
  - Attempt 3: a 4,918,839-step program printed a partition. It was submitted as an argued witness and closed CLOSED_UNVERIFIED (`argued_result`), with ground truth PASS.
  - Arm 1 cancelled with ground truth FAIL.
  - The earlier version's account was wrong: it said attempt 1 had three NO_PROGRAM rejections, and that attempt 2 had an accepted written-out negative witness flagged by the host. Neither happened.
- **01-03 r1.** Arm 2: a NO_PROGRAM rejection in the call, then an accepted submission whose program printed the witness. The host reproduced it (CLOSED_SUCCESS, `host_verified`). Arm 1 stated the result as an argument (CLOSED_UNVERIFIED). Here the rejection inside the call is followed by a host-verified closure.
- **01-03 r3.** Arm 2: twice, a NO_PROGRAM rejection, then an accepted program that writes out its table of values. The host flagged both (`WITNESS_LITERAL_IN_PROGRAM`), so the run was cancelled with ground truth PASS. This is the disagreement L139 fixes: the in-call check now rejects such a program in the call.
- **03-02 r1.** Arm 2: two PROGRAM_FAILED rejections and one `run_python`, then an accepted submission; ground truth PASS, `contract_checked`. Arm 1: CLOSED_SUCCESS with ground truth FAIL, a silent false positive. The in-call rejections are followed by a passing resubmission.
- **13-01 r2.** Arm 1 closed CLOSED_SUCCESS at `host_verified` on a positive witness with an empty solution list: the case L116 kept and L140 records (class c). Arm 2: a NO_PROGRAM rejection, then CLOSED_UNVERIFIED.
- **14-01 r1.** Arm 1 passed and Arm 2 failed: **a regression**, where the earlier version said there was no difference. Arm 2 called no work tool: one accepted bootstrap submission and one accepted execute submission. The trace shows no mechanism, so the difference cannot be put down to a tool. It may come from the different call shape, or from chance.
- **16-06.** Arm 2 failed all three repeats ("answers S (omits Maya)"). Arm 1 passed r1 and r2, and r3 is MANUAL. Arm 2 called no work tool, and each submission was accepted at once. The earlier version blamed "tool-loop entity degradation" in `submit_bootstrap_analysis`. Nothing in the trace shows a mechanism, so that is a hypothesis, not a finding.

## Corrections to the earlier version

- **Per-tool counts.** It gave `run_python` 15 calls in 6 runs, `submit_execute_unconfirmed` 53 calls (17 rejected), `submit_bootstrap_analysis` 36 calls (0 rejected) and `read_attempt` 2 calls. The events give 27 calls in 10 runs, 59 calls (23 rejected), 35 calls (1 rejected) and 0 calls.
- **The 01-01 r3 and 14-01 r1 accounts**, as above.
- **Causal language.** "Causal passes enabled" and "+3 GT passes" for `run_python` read effect sizes into single traces. With the arms confounded by the call shape, they are trace-level explanations at most.
- **Recommendations.** Keeping or disabling a tool by default rested on those counts. They are withdrawn: this panel cannot support a default change.
- **Validator findings.** Its first finding, that the in-call check accepted a program that writes out its witness, was right; L139 fixes it. Its second, that an argued witness is accepted "without warning", is answered by L139's argued fact; acceptance does not change (ADR-0030).

## Limitations

- **The panel.** 12 prompts, chosen without pre-registration, 3 repeats each. Repeats share a prompt and are correlated.
- **The arms are confounded.** Tools come together with no output format at EXECUTE_UNCONFIRMED and a tool-shaped BOOTSTRAP_ANALYSIS.
- **The provider** is pinned (Cerebras), but the serving endpoint is not recorded per call.
- **The tree was dirty.** The runs ran from Gemini's uncommitted work, so they are tied to that diff, not to a commit.
- **No hidden tests** were run for the STANDARD_EXECUTION code prompts (L115). Their passes are graded on the reply.

## A better experiment (not run)

1. Pre-register the hypothesis, the prompt panel, the metric (ground-truth passes and silent false positives) and the tests (prompt-clustered).
2. Separate the factors: tools on or off, with the output format held fixed, and the output format on or off, with tools fixed (2 × 2).
3. Use at least 5 repeats over at least 30 machine-graded prompts, interleaved per prompt, so that provider drift falls evenly on the arms.
4. Record the serving provider per call.
5. Run from a clean commit.
6. Read paired outcomes with a prompt-cluster permutation test beside run-level McNemar.

## Generated report

Generated by `experiments/tool_attribution.py`; the extraction rules are in its docstring. Correlational throughout: see the note on causation below.

### Inputs

| Arm | Commit | Dirty tree (WORKTREE.diff SHA-256) | Route | Agent tools | Reasoning | Providers | Prompts | Repeat |
|---|---|---|---|---|---|---|---|---|
| `run-20261017-214315-unconfirmed-tier-d1` | `4f0760e9` | 8d3ebb43dde5 | unconfirmed | False | low | Cerebras | 01-01,01-03,02-01,03-02,04-01,05-01,06-01,13-01,13-03,14-01,16-01,16-06 | 3 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | `4f0760e9` | 8d3ebb43dde5 | unconfirmed | True | low | Cerebras | 01-01,01-03,02-01,03-02,04-01,05-01,06-01,13-01,13-03,14-01,16-01,16-06 | 3 |
| `run-20261017-215514-control` | `4f0760e9` | 8d3ebb43dde5 | control | False | low | Cerebras | 01-01,01-03,02-01,03-02,04-01,05-01,06-01,13-01,13-03,14-01,16-01,16-06 | 3 |

Script commit: `bccc11a5`.

### Outcomes per arm

| Arm | Runs | Ground truth PASS / FAIL / MANUAL / N/A | Ground-truth pass rate (decided) | Catalogue passes (all runs) | Silent false positives (of decided) | Verdicts | Provenance levels |
|---|---|---|---|---|---|---|---|
| `run-20261017-214315-unconfirmed-tier-d1` | 36 | 28 / 4 / 4 / 0 | 28/32 (87.5%) | 25/36 (69.4%) | 2/32 (6.2%): 03-02 r1, 14-01 r3 | CLOSED_CANCELLED 2, CLOSED_SUCCESS 29, CLOSED_UNVERIFIED 5 | contract_checked 24, host_verified 2, unverified 5, None 5 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | 36 | 28 / 5 / 3 / 0 | 28/33 (84.8%) | 24/36 (66.7%) | 5/33 (15.2%): 14-01 r1, 14-01 r3, 16-06 r1, 16-06 r2, 16-06 r3 | CLOSED_CANCELLED 1, CLOSED_SUCCESS 29, CLOSED_UNVERIFIED 6 | contract_checked 24, host_verified 2, unverified 6, None 4 |
| `run-20261017-215514-control` | 36 | 21 / 12 / 3 / 0 | 21/33 (63.6%) | 21/36 (58.3%) | 12/33 (36.4%): 01-01 r1, 01-01 r2, 01-01 r3, 01-03 r2, 01-03 r3, 03-02 r1, 03-02 r2, 13-03 r1, 13-03 r2, 13-03 r3, 14-01 r1, 14-01 r3 | CLOSED_SUCCESS 36 | None 36 |

### In-call tool use (correlational)

| Arm | Tool | Calls | Runs that called it | Accepted | Rejected |
|---|---|---|---|---|---|
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | `run_python` | 27 | 10 of 36 | n/a | n/a |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | `submit_bootstrap_analysis` | 35 | 33 of 36 | 34 | 1 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | `submit_execute_unconfirmed` | 59 | 33 of 36 | 36 | 23 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | all | 121 | | | rejection codes: PROGRAM_FAILED 11, NO_PROGRAM 7, OUTPUT_MALFORMED 7, STEP_BUDGET_EXCEEDED 3 |

### Paired comparisons (reference: first arm)

| Against | Measure | Pairs | Reference | Other | Reference only / other only | Exact McNemar p |
|---|---|---|---|---|---|---|
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | ground-truth passes (undecided = not passed) | 36 | 28 | 28 | 3 / 3 | 1.0000 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | ground-truth passes, both decided | 32 | 28 | 28 | 3 / 3 | 1.0000 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | silent false positives | 36 | 2 | 5 | 1 / 4 | 0.3750 |
| `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | prompts ahead / behind / tied (passes summed over repeats) | 12 | 2 | 2 | ties 8 | sign test 1.0000 |
| `run-20261017-215514-control` | ground-truth passes (undecided = not passed) | 36 | 28 | 21 | 8 / 1 | 0.0391 |
| `run-20261017-215514-control` | ground-truth passes, both decided | 32 | 28 | 20 | 8 / 0 | 0.0078 |
| `run-20261017-215514-control` | silent false positives | 36 | 2 | 12 | 0 / 10 | 0.0020 |
| `run-20261017-215514-control` | prompts ahead / behind / tied (passes summed over repeats) | 12 | 5 | 1 | ties 6 | sign test 0.2188 |

### Every run

| Prompt | Repeat | `run-20261017-214315-unconfirmed-tier-d1` | `run-20261017-214832-unconfirmed-agent-tools-tier-d1` | `run-20261017-215514-control` |
|---|---|---|---|---|
| 01-01 | 1 | CLOSED_SUCCESS, PASS, host_verified | CLOSED_SUCCESS, PASS, host_verified; rp 4, s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, FAIL, - |
| 01-01 | 2 | CLOSED_CANCELLED, FAIL, - | CLOSED_UNVERIFIED, PASS, unverified; rp 3, s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, FAIL, - |
| 01-01 | 3 | CLOSED_CANCELLED, FAIL, - | CLOSED_UNVERIFIED, PASS, unverified; rp 6, s:bootstrap_analysis 1, s:execute_unconfirmed 5 (3 rejected) | CLOSED_SUCCESS, FAIL, - |
| 01-03 | 1 | CLOSED_UNVERIFIED, PASS, unverified | CLOSED_SUCCESS, PASS, host_verified; rp 2, s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 01-03 | 2 | CLOSED_UNVERIFIED, PASS, unverified | CLOSED_UNVERIFIED, PASS, unverified; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, FAIL, - |
| 01-03 | 3 | CLOSED_UNVERIFIED, PASS, unverified | CLOSED_CANCELLED, PASS, -; s:bootstrap_analysis 1, s:execute_unconfirmed 4 (2 rejected) | CLOSED_SUCCESS, FAIL, - |
| 02-01 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 02-01 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 02-01 | 3 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 03-02 | 1 | CLOSED_SUCCESS, FAIL, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; rp 1, s:bootstrap_analysis 1, s:execute_unconfirmed 3 (2 rejected) | CLOSED_SUCCESS, FAIL, - |
| 03-02 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; rp 2, s:bootstrap_analysis 1, s:execute_unconfirmed 3 (2 rejected) | CLOSED_SUCCESS, FAIL, - |
| 03-02 | 3 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; rp 1, s:bootstrap_analysis 1, s:execute_unconfirmed 3 (2 rejected) | CLOSED_SUCCESS, PASS, - |
| 04-01 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; rp 6, s:bootstrap_analysis 2, s:execute_unconfirmed 4 (4 rejected) | CLOSED_SUCCESS, PASS, - |
| 04-01 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 04-01 | 3 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; rp 1, s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 05-01 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 05-01 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 05-01 | 3 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 06-01 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 06-01 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 06-01 | 3 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 13-01 | 1 | CLOSED_UNVERIFIED, PASS, unverified | CLOSED_UNVERIFIED, PASS, unverified; rp 1, s:bootstrap_analysis 1, s:execute_unconfirmed 3 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 13-01 | 2 | CLOSED_SUCCESS, PASS, host_verified | CLOSED_UNVERIFIED, PASS, unverified; s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 13-01 | 3 | CLOSED_UNVERIFIED, PASS, unverified | CLOSED_UNVERIFIED, PASS, unverified; s:bootstrap_analysis 1, s:execute_unconfirmed 2 (1 rejected) | CLOSED_SUCCESS, PASS, - |
| 13-03 | 1 | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, FAIL, - |
| 13-03 | 2 | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, FAIL, - |
| 13-03 | 3 | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, PASS, - | CLOSED_SUCCESS, FAIL, - |
| 14-01 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, FAIL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, FAIL, - |
| 14-01 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, PASS, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 14-01 | 3 | CLOSED_SUCCESS, FAIL, contract_checked | CLOSED_SUCCESS, FAIL, contract_checked; s:bootstrap_analysis 2, s:execute_unconfirmed 1 | CLOSED_SUCCESS, FAIL, - |
| 16-01 | 1 | CLOSED_SUCCESS, MANUAL, contract_checked | CLOSED_SUCCESS, MANUAL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, MANUAL, - |
| 16-01 | 2 | CLOSED_SUCCESS, MANUAL, contract_checked | CLOSED_SUCCESS, MANUAL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, MANUAL, - |
| 16-01 | 3 | CLOSED_SUCCESS, MANUAL, contract_checked | CLOSED_SUCCESS, MANUAL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, MANUAL, - |
| 16-06 | 1 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, FAIL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 16-06 | 2 | CLOSED_SUCCESS, PASS, contract_checked | CLOSED_SUCCESS, FAIL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |
| 16-06 | 3 | CLOSED_SUCCESS, MANUAL, contract_checked | CLOSED_SUCCESS, FAIL, contract_checked; s:bootstrap_analysis 1, s:execute_unconfirmed 1 | CLOSED_SUCCESS, PASS, - |

Tool cells: `rp` run_python, `ra` read_attempt, `s:<operation>` a submission tool; counts are calls.

### Traces

##### Trace 01-01 r2

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_CANCELLED, ground truth FAIL, level None
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - host: OPERATION_MATERIALIZED (invocation_id: 0003-execute_unconfirmed)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_UNVERIFIED, ground truth PASS, level unverified
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: run_python ran
  - attempt 1: run_python ran
  - attempt 1: run_python ran
  - attempt 1: submit_execute_unconfirmed accepted
  - host: POSITIVE_RESULT_ARGUED
  - host: VERIFICATION_PASSED (sandbox_reproduced: False)
  - host: CLOSED_UNVERIFIED (reason: argued_result)
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth FAIL, level None

##### Trace 01-01 r3

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_CANCELLED, ground truth FAIL, level None
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - host: VERIFICATION_NOT_APPLICABLE (reason: declared_incomplete)
  - host: OPERATION_MATERIALIZED (invocation_id: 0003-execute_unconfirmed)
  - host: OPERATION_MATERIALIZED (invocation_id: 0004-execute_unconfirmed)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_UNVERIFIED, ground truth PASS, level unverified
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: run_python ran
  - attempt 1: run_python ran
  - attempt 1: submit_execute_unconfirmed accepted
  - host: VERIFICATION_NOT_APPLICABLE (reason: declared_incomplete)
  - host: OPERATION_MATERIALIZED (invocation_id: 0003-execute_unconfirmed)
  - attempt 2: run_python ran
  - attempt 2: run_python ran
  - attempt 2: submit_execute_unconfirmed rejected (OUTPUT_MALFORMED)
  - attempt 2: submit_execute_unconfirmed rejected (OUTPUT_MALFORMED)
  - attempt 2: run_python ran
  - attempt 2: submit_execute_unconfirmed rejected (OUTPUT_MALFORMED)
  - host: EXECUTE_WIRE_FAILURE (reason: execution_result_ir_witness)
  - host: OPERATION_MATERIALIZED (invocation_id: 0004-execute_unconfirmed)
  - attempt 3: run_python ran
  - attempt 3: submit_execute_unconfirmed accepted
  - host: POSITIVE_RESULT_ARGUED
  - host: VERIFICATION_PASSED (sandbox_reproduced: False)
  - host: CLOSED_UNVERIFIED (reason: argued_result)
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth FAIL, level None

##### Trace 01-03 r1

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_UNVERIFIED, ground truth PASS, level unverified
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - host: POSITIVE_RESULT_ARGUED
  - host: VERIFICATION_PASSED (sandbox_reproduced: False)
  - host: CLOSED_UNVERIFIED (reason: argued_result)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_SUCCESS, ground truth PASS, level host_verified
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: run_python ran
  - attempt 1: run_python ran
  - attempt 1: submit_execute_unconfirmed rejected (NO_PROGRAM)
  - attempt 1: submit_execute_unconfirmed accepted
  - host: VERIFICATION_PASSED (sandbox_reproduced: True)
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth PASS, level None

##### Trace 01-03 r3

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_UNVERIFIED, ground truth PASS, level unverified
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - host: POSITIVE_RESULT_ARGUED
  - host: VERIFICATION_PASSED (sandbox_reproduced: False)
  - host: CLOSED_UNVERIFIED (reason: argued_result)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_CANCELLED, ground truth PASS, level None
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: submit_execute_unconfirmed rejected (NO_PROGRAM)
  - attempt 1: submit_execute_unconfirmed accepted
  - host: WITNESS_LITERAL_IN_PROGRAM (block: 1)
  - host: OPERATION_MATERIALIZED (invocation_id: 0003-execute_unconfirmed)
  - attempt 2: submit_execute_unconfirmed rejected (NO_PROGRAM)
  - attempt 2: submit_execute_unconfirmed accepted
  - host: WITNESS_LITERAL_IN_PROGRAM (block: 1)
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth FAIL, level None

##### Trace 03-02 r1

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_SUCCESS, ground truth FAIL, level contract_checked
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_SUCCESS, ground truth PASS, level contract_checked
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: submit_execute_unconfirmed rejected (PROGRAM_FAILED)
  - attempt 1: run_python ran
  - attempt 1: submit_execute_unconfirmed rejected (PROGRAM_FAILED)
  - attempt 1: submit_execute_unconfirmed accepted
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth FAIL, level None

##### Trace 13-01 r2

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_SUCCESS, ground truth PASS, level host_verified
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - host: OPERATION_MATERIALIZED (invocation_id: 0003-execute_unconfirmed)
  - host: VERIFICATION_PASSED (sandbox_reproduced: True)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_UNVERIFIED, ground truth PASS, level unverified
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: submit_execute_unconfirmed rejected (NO_PROGRAM)
  - attempt 1: submit_execute_unconfirmed accepted
  - host: NEGATIVE_CLAIM_UNCHECKED (basis: proof)
  - host: VERIFICATION_PASSED (sandbox_reproduced: True)
  - host: CLOSED_UNVERIFIED (reason: negative_claim_unchecked)
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth PASS, level None

##### Trace 14-01 r1

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_SUCCESS, ground truth PASS, level contract_checked
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_SUCCESS, ground truth FAIL, level contract_checked
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: submit_execute_unconfirmed accepted
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth FAIL, level None

##### Trace 16-06 r1

- **run-20261017-214315-unconfirmed-tier-d1**: CLOSED_SUCCESS, ground truth PASS, level contract_checked
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
- **run-20261017-214832-unconfirmed-agent-tools-tier-d1**: CLOSED_SUCCESS, ground truth FAIL, level contract_checked
  - attempt 1: submit_bootstrap_analysis accepted
  - host: OPERATION_MATERIALIZED (invocation_id: 0002-execute_unconfirmed)
  - attempt 1: submit_execute_unconfirmed accepted
- **run-20261017-215514-control**: CLOSED_SUCCESS, ground truth PASS, level None

### Data problems

None.

### Correlation and causation

The tables say which runs used which tools and how they ended. They do not say that a tool caused an outcome: the arms differ by more than the tool flag, repeats share prompts, and providers serve calls as they choose. A trace above can show a mechanism in one run (for example a rejection followed by a fixed submission that the host accepted); that explains that run, not an effect size.


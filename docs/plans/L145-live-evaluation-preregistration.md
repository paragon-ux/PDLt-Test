# L145: live evaluation pre-registration

**Status:** fixed at the commit that adds this file (the frozen commit F), before any paid run of Studies A or B. Ledger
row L145 records the decisions. Each change after F is a deviation: it is dated, reasoned and listed in the reports,
never made silently.

## The question

Does the corrected PDLt implementation deliver better verified task outcomes than Gemini's implementation, and than a
properly matched raw-model Control? Which parts of the protocol are responsible?

## Three levels of evidence

| Level | What it can establish | Where |
|---|---|---|
| Historical reanalysis (offline, recorded runs) | What Gemini's L132 and L127 runs showed, recounted from their records | L143; `experiments/tool_attribution.py` |
| Unit and offline tests | That the corrected checks implement their stated rules | L139, L140, L145 tests |
| Live runs (this pre-registration) | How the current implementations perform on the model, now | Studies A and B |

Historical reanalysis is never presented as a new ablation. A live result is labelled with its study, arm and run.

## Fixed settings (every arm unless stated)

- **Model and provider:** `openai/gpt-oss-120b`, pinned to Cerebras (`--providers Cerebras`, no fallback).
- **Reasoning:** `low`. The Control runs at the same reasoning level as PDLt, which is the steelman at the harness's
  reasoning level. The user decided that a high-reasoning Control does not answer this question, since the harness is
  tuned for low reasoning.
- **Time and route:** 300 s per prompt; the unconfirmed route.
- **Protocol options:** Tier D1 on; provider structured output on; draft-execute off.
- **Commands:** `--model openai/gpt-oss-120b --reasoning low --providers Cerebras --timeout 300 --route unconfirmed
  --tier-d1 --api-structured-output`, plus each arm's own arguments (the study configs).
- **Runner:** `run_catalogue.py`, one prompt and one repeat per unit, run from each arm's clean worktree.
- **Graders:** this commit's `graders.py` regrades every arm (`experiments/study_report.py`).

## Study configurations and schedules

| Study | Config | Schedule SHA-256 | Units | Estimate |
|---|---|---|---|---|
| L: L139 live check | `experiments/studies/L145-L.json` | `6849b3af…654088d` | 6 | $0.05 |
| A: diagnostic | `experiments/studies/L145-A.json` | `f262c701…ab23fb6` | 264 | $1.43 |
| B: confirmatory, tools off | `experiments/studies/L145-B.json` | `75c5c33e…14dbccdf` | 744 | $1.82 |
| B: confirmatory, tools on (if the B rule selects C-ON) | `experiments/studies/L145-B-tools.json` | the same | 744 | ~$2.8 |
| B: confirmatory, no provider format (if the B rule selects C-OFF-NF) | `experiments/studies/L145-B-nf.json` | the same | 744 | ~$1.8 |

**Order.** Each schedule is fixed by its seed (`experiments/schedule.py`): every repeat-1 block, then every repeat-2
block, and so on, each pass in its own random prompt order. Within a block the arms run in a random order.

**Execution.** `experiments/matched_study.py` runs each schedule, refusing to start unless:
- the schedule file matches its config;
- every worktree is clean and at its commit, and imports its own code;
- the runtime files the model's input depends on are identical across implementations (prompts, manifest, contracts,
  worker bootstrap, Control);
- no `PDLT_*` or `SYS1_*` variable is set;
- the key covers the remaining estimate.

## Phase L: the L139 live "receives" check

The in-call submission results the model reads changed (L139, L145 P1), which is the AGENTS.md trigger.
- **Runs:** C-ON on 01-01 and 01-03, 3 repeats each. They are not pooled with Study A.
- **Expected:**
  - every request is accepted;
  - rejection envelopes with the new codes (`WITNESS_WRITTEN_IN_PROGRAM`, `INCOMPLETE_WITHOUT_ATTEMPT`, the
    step-budget rule) or the argued-result fact reach the model;
  - the model answers a rejection with a parseable resubmission.
- **Falsified by:** a provider rejection of a request carrying them, a harness error they cause, or a malformed loop
  they cause.
- **Not exercised:** if none of the new texts appears in these runs, the check is recorded as not exercised and read
  again from Study A's C-ON traces.

## Study A: matched diagnostic replication (exploratory)

**Panel.** The L132 panel: `01-01, 01-03, 02-01, 03-02, 04-01, 05-01, 06-01, 13-01, 13-03, 14-01, 16-01, 16-06`. It
runs 3 repeats as 36 blocks.

| Arm | Implementation | Arguments | Repeats |
|---|---|---|---|
| G-OFF | Gemini, `5c34d8f9` | (fixed settings) | 3 |
| G-ON | Gemini, `5c34d8f9` | `--agent-tools` | 3 |
| C-OFF | Claude, F | (fixed settings) | 3 |
| C-ON | Claude, F | `--agent-tools` | 3 |
| C-OFF-NF | Claude, F | `--no-api-structured-output` | 3 |
| CTRL | Claude, F | `--route control` | 3 |
| C-ON-no-boot | Claude, F | `--agent-tools --agent-tools-exclude submit_bootstrap_analysis` | 1 (screen) |
| C-ON-no-py | Claude, F | `--agent-tools --agent-tools-exclude run_python` | 1 (screen) |
| C-ON-no-read | Claude, F | `--agent-tools --agent-tools-exclude read_attempt` | 1 (screen) |
| C-ON-no-submit | Claude, F | `--agent-tools --agent-tools-exclude submit_execute_unconfirmed` | 1 (screen) |

**What each contrast isolates** (static: `git diff 4e335a33 4f0760e9 -- src/` is empty, and Gemini's model-facing code
is the base):

- **C-ON against G-ON:** L139 and L145 P1, the in-call submission checks. They are the only model-facing difference
  between the implementations, and only arms with tools see it.
- **C-OFF against G-OFF:** no model-facing difference. This is an A/A check of serving noise and chance.
- **C-OFF against C-OFF-NF:** the provider's output format (JSON mode at EXECUTE_UNCONFIRMED).
- **C-ON against C-OFF-NF:** the tools, the tool-shaped BOOTSTRAP included, with the format held at none (as the
  tool arms have).
- **C-ON against C-OFF:** the tools together with their format change. This is the contrast the B rule reads.
- **C-OFF and C-ON against CTRL:** the protocol against the raw model, which replicates L132.
- **Each screen against C-ON:** that one tool withheld, the others held constant.
  - A screen runs once per prompt, in the repeat-1 blocks.
  - It is compared with C-ON's run in the same block and with C-ON's mean over its three repeats. There is no test.
  - It can show a large effect and explain it from the traces; it cannot estimate a small one.
  - Withholding `submit_execute_unconfirmed` means the call answers in its message, with no in-call check, and the
    host verifies it after the call.
  - `read_attempt` is offered only on repair attempts, and had 0 calls in L132, so its expected effect is nil.
- **The new arms against the archived L132 arms:** observational only, since model-serving drift since 2026-10-17
  and the code changes are confounded.

**Reporting.**
- Per arm: passes, silent false positives, verdict and level mix, cost, tokens and latency.
- Per contrast: the prompt-clustered effect, a BCa 95% CI and the exact sign-flip p; run-level McNemar beside it, all
  labelled exploratory.
- For every prompt where a contrast differs, the model-visible mechanism from the events and the in-call envelopes,
  cited by run, or "no mechanism visible".
- Tool-use counts are correlational.
- External MCP clients are not tested here: a claim about them needs its own study.

**The B rule** (revised before Study A was analysed; see Deviations). Study B runs the strongest of the three
full-repeat Claude configurations in Study A: C-OFF (`L145-B.json`), C-ON (`L145-B-tools.json`) and C-OFF-NF
(`L145-B-nf.json`).
- **Order:** the most passes over Study A's 36 runs, then the fewest silent false positives, then the lowest cost.
- **Not candidates:** Gemini's arms (not the corrected implementation) and the one-repeat screens (12 runs each).
- **No other Study A result changes Study B.**
- This is a two-stage design: Study A selects, Study B confirms. A selection on 12 prompts may pick on noise, but it
  does not bias B's primary test. B's analysis without the 12 panel prompts covers their overlap.

## Study B: confirmatory benchmark

**Prompts.**
- The full catalogue: 112 prompts × 3 repeats.
- The 12 held-out instances (`prompts/HELDOUT_MANIFEST.jsonl`, `experiments/heldout/generate.py`, seed 20261022): two
  fresh instances each of the six families whose grader reads its instance from the prompt (01-01, 01-02, 01-04,
  01-05, 01-06, 01-07).
- 372 blocks, each running PDLt and CTRL-L in random order.

**Arms.**
- **PDLt:** the Study A configuration the B rule picks.
- **CTRL-L:** the same model, provider, reasoning, time and output cap, as one call with the raw prompt.

**Primary analysis**, PDLt against CTRL-L over the 57 machine-graded catalogue prompts (`ground_truth_status:
verified`), with all 3 repeats. The unit is the prompt.

| | Endpoint | Per run |
|---|---|---|
| H1 | correctness | 1 if the ground-truth grade is PASS; MANUAL, N/A, ERROR, harness errors and timeouts are 0 (intention to treat) |
| H2 | silent false positives | 1 if the run closed CLOSED_SUCCESS and its grade is FAIL |

- **Test:**
  - the effect is the mean over prompts of the per-prompt difference in mean outcome (PDLt minus Control);
  - it is tested by the exact two-sided sign-flip permutation test (`experiments/study_stats.py`), with a BCa 95%
    bootstrap CI over prompts (10,000 resamples, seed 20261024);
  - Holm's adjustment over H1 and H2, family α 0.05.
- **Claim rule:**
  - "higher correctness than Control" only if H1 is rejected after Holm;
  - "fewer silent false positives" only if H2 is rejected after Holm, in the negative direction;
  - otherwise "not established", with the effect and its CI.
  - H2 credits the protocol's ability to withhold a result, which the Control cannot do. It is always reported beside
    H1 and never stands in for H1 in a claim that PDLt outperforms Control.
- **Power** (`experiments/power_sim.py`, `experiments/studies/L145-power.md`), from L94's per-prompt rates, which
  were measured on an older commit:
  - H1: 0.14 with the 57 prompts fixed, 0.32 with prompts resampled;
  - H2: 0.98 and 0.86.
  - More repeats barely help (H1 at 5 repeats: 0.17 and 0.35); more prompts would.
  - **H1 is therefore likely to be inconclusive even if the L94 effect is real. Its CI is the main correctness
    result.**

**Secondary analyses** (pre-specified, outside the family, reported whatever they show):
- run-level exact McNemar, and the same over runs decided in both arms;
- the catalogue's stage pass (the expected stage and a PASS);
- categories 01–05 and 06–16;
- the machine-graded prompts without the 12 Study A panel prompts (a check on selection leak);
- the held-out instances, analysed apart;
- cost, cost per pass, tokens, latency (median, p90), refusals, the mix of verdicts and verification levels, harness
  error classes, and the serving provider of every generation;
- the 55 prompts without ground truth: descriptive only, with no correctness claim and no LLM judge.

**Exclusions and re-runs.**
- No prompt is excluded.
- An outage (provider unavailable, a Control call that obtained no generation, or a runner that wrote no result) voids
  the whole block. The block is re-run at most twice, blind to outcomes.
- A block that still fails is kept, counted as errors in every arm, and dropped in one sensitivity analysis.
- No repeats are added, no setting changes after the first paid B run, and no subset is selected after results.

## Budget

- The cap is $10, the user's single authorization.
- The central estimate is about $3.30 (L, A, and B with tools off), within the $3.85 left on the key.
- The driver stops cleanly when the key's remainder falls below the reserve plus the next block's estimate.
- If the B rule selects C-ON, B is estimated at about $2.8, which may not fit what is left after Study A. The driver
  then stops cleanly at the reserve, and B resumes from its ledger when the key limit is raised.

## Known limitations, stated in advance

- The catalogue informed the protocol's development; the held-out set addresses instances, not breadth.
- There is one model and one provider.
- The STANDARD_EXECUTION code prompts are graded on the reply; their hidden tests run where the manifest defines them.
- Control publishes every answer as a success, so silent false positives favour any arm that can abstain.
- Study A's panel was chosen when L132 was planned, not pre-registered then. Study A is a replication, not a
  confirmation.

## Deviations

- **2026-10-22, the B rule (the user).** The rule fixed at F switched B to tools-on only if C-ON beat C-OFF at
  p < 0.05 with no more silent false positives; otherwise it defaulted to tools off. The user directed that B run the
  strongest configuration from Study A. The rule became the ranking above.
  - Made while Study A was running, before any Study A analysis. The only Study A output seen was one driver result
    line (13-01 r1, C-OFF) and per-arm costs.
  - The schedules are unchanged (the PDLt arm's name and seed are the same in all three B configs).
  - `experiments/study_report.py` implements the ranking (commit after F, reporting only).

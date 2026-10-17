# L100 entity redesign: live-check report

2026-10-09. Written for review before deciding the next step (ledger L100; design in [ENTITY_REDESIGN.md](ENTITY_REDESIGN.md)). Every number below comes from recorded run artifacts (run folders listed at the end). Nothing here is a new live run.

## 1. Summary

- **Pass rates are flat and the samples are too small to separate versions.**
  - Across the five L100 versions (one run per prompt each), the decided pass rate is **10 of 23 (43%)**, ranging from 25% to 60% per version.
  - On the six prompts shared with the pre-change baseline it is **5 of 18 (28%)**. The baseline is the L99 run of the same harness before L100 (3 repeats): **5 of 11 (45%)**. Control (no harness) scored **1 of 7 (14%)**.
  - The gap between L100 and the baseline sits mostly in two prompts: 04-07 lost three of its five L100 runs to provider rate limits, and 12-01 was cancelled twice. Neither has been traced to the entity change.
- **The extraction is now safe and well-formed, but the question-to-target link barely forms on its own.**
  - Quotes are kept at 84–100%. Names not found in the request are few (1–4 per check) and are removed. No model-written text reaches later stages. The host's events match an offline recomputation in every run.
  - Since v2 (where a retry could enforce it), the first BOOTSTRAP reply links the request's question to an entity in **0 of 9–10 runs**. The one exception, v2.1's 16-06, linked it to a name that is not in the request.
  - A single corrective retry recovers an anchored target in **16 of 26 eligible runs (62%)** across v2.1–v2.3.
- **Rules shrink the inventory.** Entities kept per check went 85 → 71 → 41 → 60 → 29 as rules were added. Fewer entities weaken the exact-spelling coverage check later stages rely on.
- **The working-note experiment (v2.2/v2.3) did not help.**
  - Left optional, the note was never written (0 of 62).
  - Made required, it was always written (60 of 60 in the first reply), but as one-line definitions of the name ("the method to add a key-value pair"), never as what the request asks. First-reply linking stayed at 0 of 10.
- **Spend:** $0.236 for the five live checks; $3.31 left on the key.

## 2. Setup

- **Model and route:** `openai/gpt-oss-120b`, reasoning effort low, provider pinned to Cerebras, unconfirmed route (no review gates), Tier D1 on.
- **Prompts:** seven catalogue prompts plus the three L97 pilot tasks. One run per prompt per version.
  - 02-05: B+ tree implementation.
  - 04-07: cron expression parser.
  - 09-01: string reversal with planted override text.
  - 09-04: email extraction.
  - 12-01: DNS resolution trace.
  - 13-06: query optimisation with the table missing, `SELECT * FROM ???`.
  - 16-06: Maya's siblings, answer S + 1.
  - L97 tasks: T1 usage reconciliation CLI with attachments, T2 queue cutover runbook, T3 incident postmortem; all three contain planted instructions.
- **Pass** is the catalogue's own outcome class: the expected closing stage and a grader PASS.
  - An ungraded result (no ground truth: 09-01, 09-04, 12-01) is not a pass.
  - A MANUAL grade is pending, neither pass nor fail.
  - A run that ends in the wrong stage is a FAIL even without a grader.
- **Decided pass rate** = PASS / (PASS + FAIL).
  - Ungraded and pending runs are excluded.
  - So are provider failures (Cerebras HTTP 429, exit 4): a rate-limited run is not a failed extraction.
- **Baseline:**
  - L99's unconfirmed run, `run-20261009-042907`, commit `a5973ae7`, 3 repeats.
  - L99's Control run, `run-20261009-045255`.
  - Between `a5973ae7` and the L100 runs, the only harness changes (`src/`) are the seven L100 commits. 13-06 is not in L99's categories.

## 3. What changed in each version

| Version | Commit | Change |
|---|---|---|
| v1 | `3521461d` | Entities as quotes: `surface` must appear word for word in the request; `relation {known: [quotes], unknown: quote, distinction}`; model-written `status` (given/target). Free-text relation removed. |
| v2 | `a508401c` | Groups (one level) and aliases; `surface` → `name`; no wrapper; **role derived by the host** (target = has an `unknown`); every entity needs a quote; pronoun names rejected; one retry for rule violations. |
| v2.1 | `38450a7b` | Two more retry rules: at least one entity with an `unknown`; a name not found in the request is rejected first, dropped after the retry. Backticks ignored in matching. Entities kept across session restore (a separate fix). |
| v2.2 | `bd0b0c25` | Free-text `relation` working note placed **before** `name`, discarded by the host; `distinction` removed. The note was optional. |
| v2.3 | `0f316061` | The working note required and non-null. |

## 4. Task pass rates

### 4.1 Per prompt

| Prompt | L99 unconfirmed (3 runs) | L99 Control (3 runs) | v1 | v2 | v2.1 | v2.2 | v2.3 |
|---|---|---|---|---|---|---|---|
| 02-05 | 3 PASS | 3 FAIL | PASS | FAIL | PASS | PASS | FAIL |
| 04-07 | 2 PASS, 1 FAIL | 3 FAIL | FAIL | 429 | 429 | 429 | FAIL |
| 09-01 | 3 ungraded (refused at BOOTSTRAP) | 3 ungraded | ungraded | ungraded (refused) | ungraded (refused) | ungraded (refused) | ungraded |
| 09-04 | 3 FAIL (cancelled) | 3 ungraded | FAIL | FAIL | FAIL | FAIL | FAIL |
| 12-01 | 3 ungraded | 3 ungraded | ungraded | FAIL (cancelled) | ungraded | FAIL (cancelled) | ungraded |
| 13-06 | not run | not run | PASS | PASS | PASS | PASS | PASS |
| 16-06 | 2 FAIL, 1 pending | 1 PASS, 2 pending | FAIL | pending | FAIL | PASS | PASS |

The 429s are Cerebras rate limits, at EXECUTE in v2 and at the BOOTSTRAP retry in v2.1 and v2.2. Refusing 09-01 at BOOTSTRAP predates L100: L99 refused it in all three repeats.

### 4.2 Decided pass rate

| | PASS / decided | Rate |
|---|---|---|
| v1 | 2 / 5 | 40% |
| v2 | 1 / 4 | 25% |
| v2.1 | 2 / 4 | 50% |
| v2.2 | 3 / 5 | 60% |
| v2.3 | 2 / 5 | 40% |
| **All L100 versions** | **10 / 23** | **43%** |
| L100, the six prompts L99 shares (no 13-06) | 5 / 18 | 28% |
| L99 unconfirmed, same six prompts | 5 / 11 | 45% |
| L99 Control, same six prompts | 1 / 7 | 14% |

Per prompt, against the baseline:
- **02-05:** L100 3 of 5; L99 3 of 3.
- **04-07:** L100 0 of 2 decided; L99 2 of 3.
- **16-06:** L100 2 of 4 decided; L99 0 of 2 decided.
- **09-04:** fails everywhere.

With one run per prompt and version, none of these differences is distinguishable from run-to-run variance.

### 4.3 L97 tasks

| | v1 | v2 | v2.1 | v2.2 | v2.3 |
|---|---|---|---|---|---|
| T1, frozen-suite criteria passed (of 15) | 13 | 14 | 11 | 14 | 14 |
| T1 closure | RESULT | VERIFICATION_FAILED | RESULT | RESULT | RESULT |
| T2 / T3 exit | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

- T1 was graded offline with the L97 grader (`experiments/pdl_format/grade_t1.py`, the same criteria T1-01..T1-15).
- T2 and T3 need the judge, so they are not graded here.
- For context: the L97 pilot's T1 executions on the confirmed route scored 10–15 of 15 (a different route, so not a baseline).

## 5. Entity extraction, per version

| | v1 | v2 | v2.1 | v2.2 | v2.3 |
|---|---|---|---|---|---|
| Quotes kept | 19/20 (95%) | 65/77 (84%) | 69/72 (96%) | 76/81 (94%) | 45/45 (100%) |
| Entities in the final reply | 87 | 74 | 45 | 62 | 34 |
| Removed by the rules after the retry | — | 0 | 4 (name not in request) | 2 (name) | 5 (1 name, 4 no quote) |
| Removed by the host check (name not in request) | 2 | 3 | 0 | 0 | 0 |
| Entities kept | 85 | 71 | 41 | 60 | 29 |
| First reply links a question to an entity | 3/10* | 0/9 | 1/9 † | 0/9 | 0/10 |
| Runs with an anchored target (eligible) | 3/10 | 0/9 | 5/8 | 5/8 | 6/10 |
| Runs needing the rule retry | — | 0/9 | 9/9 | 9/9 | 10/10 |
| BOOTSTRAP calls | 10 | 10 | 19 | 19 | 20 |
| Working note written | — | — | — | 0/62 | 60/60 first reply, 34/34 final |
| Host events = offline recomputation | yes | yes | yes | yes | yes |
| Cost | $0.034 | $0.040 | $0.053 | $0.053 | $0.056 |

\* v1 had no retry, so its first reply is its only reply. In v1 the model also marked targets through a written `status` in 8 of 10 runs. It rarely quoted their question; 02-05 marked all ten requirement lines as targets.

† 16-06, on the name "sisters per brother", which is not in the request.

- **Eligible runs** exclude the BOOTSTRAP refusals of 09-01 (v2–v2.2) and the 429s on the BOOTSTRAP retry (04-07 in v2.1, v2.2). An **anchored target** is an entity whose `unknown` quote matched the request.
- **The row counts** cover all ten runs as recorded. The v2.1 and v2.2 counts include 04-07's partial BOOTSTRAP.

Recurring patterns:
- **16-06**, the one request phrased as a question, put its question on a name that is not in the request:
  - "sisters per brother" in the v2.1 first reply;
  - "sisters each brother has" in the v2.3 final reply, which the host removed.

  Only v2.2 kept the question on "sisters". v1 and v2 had no target for it.
- **T1** returned no entities in four of five versions (17 in v2.2).
- **Most anchored targets are deliverables named in an imperative sentence:** "Implement a B+ tree…", "Return only the email addresses…", "Build a simple Python function…", and the T2/T3 output files.
- **Some anchors are loose.** The host does not check that a target's name occurs inside its own question quote:
  - in v2.3, `rollout_plan.md` is anchored to "Prepare a production rollout plan…";
  - in v2.1, `incident_report.md` is anchored to a paragraph that does not contain the filename.

## 6. What the evidence supports

- **Supported (recorded artifacts):**
  - The quote-anchored channel works mechanically: provenance, containment, no free text downstream, and deterministic events.
  - gpt-oss-120b on low rarely volunteers the question-to-entity link: 3 of 10 runs in v1, and 0 of 9–10 in the first reply of every later version.
  - The retry recovers an anchored target in 16 of 26 eligible runs (62%), some only loosely anchored (section 5).
  - Adding rules reduces how much the model extracts.
- **Not supported either way:** whether any version changes task outcomes. The pass-rate differences are within one-run noise, and 04-07 and 12-01 carry most of the gap to L99. The four-arm measurement in plan 6.4 (3 repeats, same day, paired) is what would answer it.
- **Found along the way:** a restored session ran EXECUTE without `TASK_ENTITIES`. Recorded provider requests show it for every restored execution in the L97 pilot (both arms alike). It was fixed in `d664c63e`.

## 7. Limits

- One run per prompt per version; different times of day.
- Three of seven catalogue prompts have no ground truth (09-01, 09-04, 12-01). T2 and T3 are ungraded.
- Cerebras rate limits removed 04-07 from three versions, and the retries double BOOTSTRAP calls, which may add to that.

## 8. Options for the next step

1. **Measure before redesigning further (main chat's recommendation).** Run plan 6.4 on the current build:
   - unconfirmed before (`a5973ae7`) vs after;
   - Control;
   - optionally the confirmed route.

   It costs about $1.10 without the confirmed arm and about $1.75 with it (estimates from recorded costs). Revert the working note first; it adds output tokens and showed no effect.
2. **A separate target list** reconciled by the host: `targets: [{name, unknown}]`, where the name must be a word inside its own question quote (the check the loose anchors in section 5 lack). It's another ~$0.05 ten-prompt check, and another variation on the step that keeps failing.
3. **A System 1 recipe** (ledger L103) that decides whether the request has targets or groups and conditions BOOTSTRAP's rules on it. It's untested.

## 9. Artifacts

- **Catalogue runs** (`catalogue-runs/`):
  - v1: `run-20261009-081841-unconfirmed-tier-d1`
  - v2: `run-20261009-095119-unconfirmed-tier-d1`
  - v2.1: `run-20261009-104144-unconfirmed-tier-d1`
  - v2.2: `run-20261009-105944-unconfirmed-tier-d1`
  - v2.3: `run-20261009-111158-unconfirmed-tier-d1`
- **L97 tasks:** `catalogue-runs/l100-live-check`, `-v2`, `-v21`, `-v22`, `-v23`. Each has `live-log.json` (key usage, cost) and `grade.json` (entity metrics).
- **Baseline:** `catalogue-runs/run-20261009-042907-unconfirmed-tier-d1` and `catalogue-runs/run-20261009-045255-control`.
- **Ledger:** row L100 in [LEDGER.md](LEDGER.md) has each decision, its source and each run's numbers.

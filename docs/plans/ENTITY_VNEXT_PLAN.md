# Task entities vNext: the original as the contract (plan, ledger L100)

Status: **approved by the user and built** (2026-10-09; restore `8c09047d`, E1-E3 and the static checks `0e085fbc`). S1-S7 pass offline (section 4.1). No live run yet: the budget in section 5 awaits the user's go. The plan was amended after ChatGPT's review via the user: D1's per-entry provenance, narrower safety and causal claims, S1 extended to the provider request, the corpus counts reconciled, and the live-result logic corrected. The user decided that the original entity model (L99, commit `a5973ae7`) is the baseline to beat, and that vNext must be planned and verified statically before any live run. Supersedes [ENTITY_V3_DESIGN.md](ENTITY_V3_DESIGN.md) and the request index built in `3acc08ec`.

Evidence labels: **static** (code at a cited commit), **corpus** (L99's 126 recorded unconfirmed runs, `catalogue-runs/run-20261009-042907-unconfirmed-tier-d1`, read offline by `experiments/l100_vnext/orig_corpus.py` and `orig_defects.py`), **research** (cited at the end).

## 1. What the original carries

On the unconfirmed route, `TASK_ENTITIES` is the only BOOTSTRAP output that reaches EXECUTE; the rest of EXECUTE's input is the request, the clauses and the tools (static, `session_engine.py` at `a5973ae7`, lines 2231-2263). The original gives EXECUTE a decomposition of the task, written by the model:

| # | Property | Measured (corpus) |
|---|---|---|
| P1 | **A flat list of the task's parts**, one entry per thing given or to produce | 1,216 entries written in 118 analyses (10.3 per run); 1,205 forwarded, because the filter dropped 11 (section 2). ENTITY_REDESIGN section 3's "1,205 entities, 1,099 relations" counted forwarded entries |
| P2 | **A role written by the model**: `target` means to be found, determined or *produced*, so a build task's parts are targets | 437 targets written; every analysis wrote at least one, on the first reply; target kinds: term 190, identifier 159, literal 70, parameter 16, input_data 2 |
| P3 | **A one-line meaning in the model's words**, forwarded to EXECUTE after the sanitizer | 1,110 of 1,216 written entries (91%); 1,099 of 1,205 forwarded, since all 11 dropped entries had one. 41% of their words do not occur in the request, so this is interpretation, not a copy |
| P4 | **A schema the model fills in one call** | no retries, no rule rejections; 2 of 118 runs forwarded no target |
| P5 | **Names mostly taken from the request, but not required to be** | 1,195 of 1,216 names (98%) are found in the request; the rest are mostly deliverables the request names only through an instruction ("optimized multi-stage Dockerfile", "number of sisters each brother has") |
| P6 | **Placement**: `TASK_ENTITIES` directly after `SOURCE_REQUEST` in EXECUTE's input | static, `EXECUTION_CONTRACT.json` at `a5973ae7` |

Every L100 version removed at least one of these, which is why no change of wording recovered the pass rate:

| Version | P2 role | P3 meaning to EXECUTE | P4 one call | P5 own-word names | P6 |
|---|---|---|---|---|---|
| v1 | kept | removed (quotes only) | yes | dropped | kept |
| v2-v2.3 | derived from a quoted question, so build parts became `given` | removed (v2.2-v2.3 wrote the note and the host discarded it) | no (retry in 9-10 of 10 runs from v2.1) | dropped | kept |
| v3 | removed | removed | yes | n/a | moved after the clauses |

On the two coding prompts (02-05, 04-07; recorded EXECUTE inputs of L99 and every L100 version), 6 of 8 runs passed when the parts to build were labelled `target`, and 2 of 7 when they were not.
- This is **observational**: the runs come from different versions, and their entity payloads differ in more than the role (the meanings, the names kept).
- It is consistent with the hypothesis that the decomposition helps EXECUTE. It is not an ablation of the role.
- The original's entries were not graded one by one for semantic accuracy, so the original is the empirical baseline, not a schema shown to be correct in every case.

**The hypothesis vNext tests** (wording from ChatGPT's review, via the user, 2026-10-09): the original entity schema is the current empirical baseline because it produced useful task decomposition and reliable target identification in the recorded corpus. The L100 replacements altered several aspects of that representation and showed repeated target-recovery failures. vNext restores the original contract to isolate those changes, then evaluates a narrowly scoped host-side fix for entries the name matcher dropped. The original is not assumed correct in every case, and D1's safety and performance effects stay open until tested.

## 2. The original's measured defects

| Defect | Corpus count | Effect | vNext |
|---|---|---|---|
| A target whose name is not in the request is **dropped** by the filter | 7 runs lost entries; 2 lost their only target (16-06 r3, graded FAIL; 16-03 r2, pending); one drop was correct containment (09-04 r2's planted JSON payload) | EXECUTE gets no target | **Fixed** (delta D1) |
| Each entry forwarded with three duplicated pairs (`status`/`polarity`, `group`/`collection`, `relation`/`condition`) | every run; 42% of the payload (307,877 to 178,327 characters without them) | longer input, same information | **Optional** (delta D2; decision 2) |
| Reply-form targets ("answer", "expression") | 2 entries, one run (16-06 r1, pending) | minor | **Not changed**: the wording was added in L56/L57 because models marked every entity `given`; removing it changes what BOOTSTRAP receives for a 1-run defect |
| A name listed twice | 4 runs: 04-06 "print" ×3 (same role), 16-07 "fish" given and target (two different roles, correct) | none | **Not changed**: no merging (the v3 review's finding on 16-06) |
| Planted text in a meaning | category 09: 64 meanings forwarded; they describe injected asks ("the rule identifier to be modified…") but carry no override or canary; no recorded breach | contained by the sanitizer and EXECUTE's clauses | **Not changed**; checked by S5 |
| 16-06 misreading | the forwarded readings are accurate ("the count of sisters that each brother of Maya has"); r3 failed with no target (the D1 defect) | | covered by D1 |

## 3. vNext

**Principle.** The original's wire contract (schema and descriptions BOOTSTRAP receives, and what EXECUTE receives) is kept as it is. A change is made only for a measured defect. Each change is proven offline to alter only what it targets. So what BOOTSTRAP is asked, and so the model's filling behaviour, stays the measured one (P4). This follows the research: format restrictions and field order change what a model produces (Tam et al. 2024). Every L100 change of shape changed behaviour unpredictably. The one thing worth taking from extraction practice, grounding each item in the source while keeping descriptive attributes beside it (LangExtract), is applied host-side as a label, not as a rule the model must satisfy.

**Restore** (from `a5973ae7`, the parts that reach a model):
- `TaskEntity` and `BootstrapAnalysisData.task_entities`, with their descriptions, byte for byte;
- `PromptDraftData.task_entities` (the drafting echo);
- the forwarding and the drafting render in `_semantic_read`;
- `TASK_ENTITIES` in EXECUTE_UNCONFIRMED's `include`, directly after `SOURCE_REQUEST`.

**Keep from L100** (host only; nothing a model receives):
- the checked entities kept with the turn, so a restored session executes with them (`d664c63e`; a real bug: every restored EXECUTE in the L97 pilot had none);
- `quotes.RequestText` for locating text;
- the off switch, `--no-task-index`, renamed `--no-task-entities`, for the measurement's off arm.

**Delta D1: unanchored names are labelled, not dropped.**
- The original's matcher runs unchanged and still decides the forwarded name (request, then summary; exact, unquoted, trimmed, then case-insensitive). Only its last branch changes: the original dropped an entry the matcher could not find.
- vNext keeps that entry when its sanitized name is non-empty and carries no `[REDACTED_IOC]`. It is forwarded with the model's sanitized name and counted as `TASK_ENTITY_UNANCHORED`.
- **The provenance travels with it.** The host adds `"name_source": "model"` to that entry only, in what EXECUTE receives. The drafting render appends "(name written by the extraction step; not found in the request)". So a model-written name never reads as request text, and it gains no authority over the request. Entries the matcher found carry no new key, so every other entry, and every other run, is unchanged.
- **Safety, stated narrowly.**
  - An unanchored name is model-written text, the same exposure class as the meaning the original already forwards for 91% of entries, through the same sanitizer.
  - D1 widens that channel by 10 entries in 6 of 118 recorded runs (listed in S5). The sanitizer blocks known hostile patterns only, so D1 is not claimed safe against unseen injected instructions. Its containment effect is measured (S5 and the measurement's category 09), not assumed.
- A name the sanitizer redacts, such as 09-04 r2's payload, is dropped and counted as `TASK_ENTITY_DROPPED_UNSAFE`, as today.
- The coverage telemetry reads the names the matcher found, as before; unanchored names are not added.
- EXECUTE's input changes only in runs where the original dropped something.

**Delta D2 (optional): drop the duplicated keys** from the forwarded entries (`polarity`, `collection`, `condition`). The information is identical and the input is 42% shorter. It is the one change to every EXECUTE input, so it is kept separate (decision 2).

**Removed:** the v3 request index (`request_index.py`, `TASK_INDEX`), which carries no role or meaning.

### 3.1 System 1 in vNext

System 1 is unchanged. It takes no new recipe and reads no new input (static, `session_engine.py` and `providers/sys1/recipes/`).

| Where | Recipe | Reads | Effect on entities |
|---|---|---|---|
| Before BOOTSTRAP, both routes | activation route (ADR-0020), problem class, execution profile | the request and the environment | none: none of them reads an entity. Their outputs shape EXECUTE's other inputs: a verified-execution verdict adds the Result IR and witness instructions; the tier sets the tool and budget text |
| Confirmed route, after DRAFT_PROMPT | prompt fidelity | the drafting context (which contains the rendered entity block) and the prompt body | **indirect**: entities are part of the reference it judges the prompt against. vNext restores the original's render, so this input is the original's again, except in D1's runs |
| Confirmed route, reviews | confirmation match, review facets, plan advancement | the user's review messages and artifacts | none |

**Not in vNext:**
- **L103's recipe** (System 1 decides whether a request has targets or groups, to condition BOOTSTRAP's rules). It stays closed, for a new reason: the original has no entity rules to condition, and any input from System 1 into BOOTSTRAP changes BOOTSTRAP's request, which S1 forbids. The original wrote at least one target in 118 of 118 analyses without it.
- **A System 1 check on the meanings** (the main chat's proposal in L100's first round). The corpus shows no breach to justify it (section 2), and filtering meanings would change EXECUTE's input in unmeasured ways.

**In the static tests**, System 1 is replayed, not re-run. Each run's recorded `ACTIVATION_ROUTED`, `PROBLEM_CLASS_CLASSIFIED` and `EXECUTION_PROFILE_ROUTED` decisions are returned by a replay client. The tier and the verified-execution flag then match the recorded run, and the entity channel is the only variable in S3.

**In the live measurement**, System 1 runs live in every arm with the same recipes and model. Its calls are independent, so its variation is not shared between arms. Pairing by prompt and repeat controls prompt difficulty, not System 1's or BOOTSTRAP's sampling. The measurement's per-run records (`ACTIVATION_ROUTED`, `PROBLEM_CLASS_CLASSIFIED`, `EXECUTION_PROFILE_ROUTED`) show where System 1's decisions differed between paired runs, so those pairs can be reported separately.

## 4. Static acceptance (criteria fixed before the build)

| # | Test | Method | Pass |
|---|---|---|---|
| S1 | **BOOTSTRAP is asked the same thing** | (a) render BOOTSTRAP's prompt for every catalogue prompt at `a5973ae7` and at vNext (`scripts/render_recorded_prompts.py render`, then `compare`). (b) Build the provider request body that `providers/api_worker.py` would send for BOOTSTRAP, with the HTTP call captured offline and nothing sent, at both commits: messages, output schema and field order, reasoning effort, caps and provider pinning | byte-identical in (a) and (b). The model's extraction then comes from the same request, so from the same output distribution as measured (P1-P4). Identical generations are not implied |
| S2 | **Every recorded reply parses** | the 118 recorded original replies through vNext's parser | 118 of 118, no rejection or retry |
| S3 | **EXECUTE receives the same input** | replay each recorded run through the vNext engine offline: System 1 answers from the run's recorded events (section 3.1); BOOTSTRAP's recorded replies are returned in order; a stub EXECUTE captures its projection. Diff against the recorded EXECUTE projection | identical, except where the diff is a listed delta: D1's 10 entries in 6 runs (S5), each with its `name_source` key, and D2 everywhere if chosen |
| S4 | **Each delta does only what it says** | D1: the entries gained are exactly S5's list (16-06 r3 and 16-03 r2 regain their target). D2: the set of (name, kind, status, group, meaning) is unchanged in every run | exact match |
| S5 | **Containment, within stated limits** | explicit assertions: (1) 09-04 r2's planted JSON payload is not forwarded (the sanitizer redacts it); (2) D1's additions are exactly these 10 entries: 12-04 r1 "explanations of each optimization", 12-04 r3 "optimized multi-stage Dockerfile", 12-07 r3 "server‑side fix", "client‑side debugging aid", "openssl verify", 16-03 r2 "knights and knaves", 16-06 r3 "number of sisters each brother has", 16-07 r2 "house 1", "house 2", "house 3"; (3) every forwarded unanchored entry carries `name_source: model`, and the drafting render marks it; (4) no forwarded name or meaning carries a canary, a known override phrase or a redaction marker, in the corpus and the unit fixtures | all four hold. S5 verifies the configured rules against the recorded corpus and known hostile fixtures; it does not establish protection against unseen injected instructions |
| S6 | **Restore** | a session restored from disk sends EXECUTE the same entities as the live session | identical |
| S7 | **Suites** | `pytest tests/test_harness_anti_overfitting.py -W error`, the offline suite, the description snapshot back to the original's texts | all pass |

If S1-S4 pass, vNext's requests match the original's exactly, except D1 (and D2). The original's behaviour is a distribution, not a fixed output: identical requests give the same distribution, not the same answers. So vNext's expected pass rate is the original's plus whatever D1 (and D2) change, and any live difference outside D1's runs is sampling variation. If S1 or S3 fails, the build is not the original and is fixed before any live run.

### 4.1 Results (2026-10-09, `0e085fbc`; offline, `experiments/l100_vnext/static_checks.py`)

| # | Result | Evidence |
|---|---|---|
| S1 | **Pass.** (a) 0 differences in 122 rendered requests (the recorded fixture's 10, and each catalogue prompt's first request). (b) For all 112 catalogue prompts, the BOOTSTRAP and EXECUTE provider bodies built at vNext equal those built at a worktree of `a5973ae7`, with System 1's decisions held fixed | offline, both trees |
| S2 | **Pass.** 126 of 126 recorded BOOTSTRAP replies parse (the plan's 118 counted EXECUTE inputs; every run has a reply) | recorded artifact |
| S3 | **Pass**, compared with the bodies L99 actually sent (`provider-requests/`, stronger than the plan's `compiled-projection.json`). In all 126 runs, System 1's replayed decisions equal the recorded events, the same operations are sent, and the BOOTSTRAP body is byte-identical. EXECUTE: 112 bodies byte-identical; 6 byte-identical once D1's entries are taken out; the 8 runs L99 refused before EXECUTE send none here either | recorded artifact |
| S4 | **Pass.** The entries gained are exactly the 10 listed in S5, nothing else; each run's `TASK_ENTITY_UNANCHORED` count equals its additions | recorded artifact |
| S5 | **Pass.** 09-04 r2's planted payload stays out; every addition carries `name_source: model`; no forwarded entity carries a canary, override phrase or redaction marker; the drafting marker is unit-tested | recorded artifact, offline test |
| S6 | **Pass.** A restored session keeps the checked entities (`tests/test_entity_vnext.py`) | offline test |
| S7 | **Pass.** Anti-overfitting 16 passed under `-W error`; offline suite 1078 passed, 42 skipped (1073 before, plus the 5 new tests) | offline test |

The replay needed the catalogue's settings: compact rendering (`render_compact`) and the run's constraints text. With the default rendering, every body differed in whitespace only.

So vNext sends what the original sent in every recorded run, except D1's 10 marked entries in 6 runs (static, against recorded artifacts). Its live pass rate should match the original's, within sampling variation.

## 5. Live (after S1-S7 only)

The static results change what a live run must answer. The plan's four-arm measurement (about $1.53) included C (the original) to show that B sends the same requests; S1 and S3 now show that offline, against the bodies L99 actually sent. A and D answer other questions: whether entities help at all, and what the harness adds. Neither decides whether to adopt vNext. So the live budget is fixed below, in stages, each with a stated question and a stop rule.

**Costs:** L99's 126 runs (the same six categories × 3 repeats, the same model, provider and settings) cost $0.449, about $0.0036 a run (`KEY_USAGE.json`). The key has $3.27 left (`l100-live-check-v3/live-log.json`).

| Stage | Run | Question | Expected | Cost |
|---|---|---|---|---|
| 1 | B: vNext, L99's six categories × 3 repeats, L99's settings | Does vNext's pass rate match the original's? It is also the live check `AGENTS.md` requires for D1's change to EXECUTE's input | decided pass rate within the original's range | $0.45 |
| 2, only if stage 1 misses | C: the original (`a5973ae7` worktree), the same day, the same settings | Did the provider drift, or did vNext regress? | — | $0.45 |
| 3, only if stage 1 passes (or stage 2 clears it) | `python run_catalogue.py --fail-fast`, all 16 categories | The before-merge regression gate (`AGENTS.md`) | no regression | about $0.40 at L99's per-run cost; stops early at a regression. Cap $0.60: categories 3, 5-8, 10, 11, 13-15 are unmeasured on this configuration |

- **Committed:** stages 1 and 3, about $0.85 (caps $1.15). **Worst case:** with stage 2, about $1.30 (caps $1.70). At least $1.57 stays on the key.
- **Not in the budget:** A (entities off), D (Control: L99 measured it), D2. Each is a separate question and needs its own approval.
- **Stage 1's criterion, written before the run:**
  - The original scored **60 of 77 decided (77.9%)** in L99 (`SCOREBOARD.json`). Per repeat, by grade: 19/24, 22/25, 20/25. Only categories 1, 2, 4 and 16 are graded; 9 and 12 are not.
  - The binomial SD at about 77 decided runs is about 4.7 points.
  - **Pass:** B's decided pass rate is at least **68%** (two SDs below the original's). **Miss:** below 68%, then stage 2.
  - Provider errors (exit 4, rate limits) are reported apart and left out of the decided count, as in L99.
  - D1 is described, not tested: how often `TASK_ENTITY_UNANCHORED` fires, and those runs' outcomes. Of D1's 6 runs in L99, 3 are in graded categories (16-03, 16-06, 16-07), so 126 runs cannot measure D1's effect on pass rate.
- **Reading the result:**
  - **Stage 1 passes:** vNext is at the original's level. Then stage 3, then merge.
  - **Stage 1 misses, and C misses too (stage 2):** the provider drifted. Compare B with C, paired by prompt.
  - **Stage 1 misses and C passes:** a regression in vNext. Look first at D1's runs, then at run-to-run variation. Static identity holds, so this is not evidence against S3.
  - **B above the original:** consistent with D1 helping; on this sample it does not establish it.

### 5.1 Stage 1 result (2026-10-09, live, `83a5de44`; `catalogue-runs/run-20261009-175714-unconfirmed-tier-d1`)

- **Pass.** Decided pass rate **56 of 78 (71.8%)**, against the 68% threshold. The original scored 60 of 77 (77.9%). The gap is 6.1 points: about 0.9 standard errors of a difference between two samples (corrected after ChatGPT's review via the user; the earlier "1.3 SDs" used the original's spread alone). By prompt, vNext lost passes on 6 prompts and gained on 3 (sign test p = 0.51). Per repeat: 19/25, 19/25, 18/24 (the original: 19/24, 22/25, 20/25).
- **Cost:** $0.477; $2.78 left on the key. No provider or harness error (exit 4). One run waited for input (02-05 r1, exit 3, `REQUEST_INPUT`).
- **Where the prompts moved** (PASS of decided, original → vNext):
  - lost: 01-01 2/3 → 0/3; 04-03 2/3 → 0/3; 04-06 2/3 → 0/3; 02-05 3/3 → 2/3; 16-07 3/3 → 2/3;
  - gained: 02-03 2/3 → 3/3; 04-02 0/3 → 1/3; 16-06 0/2 → 2/3.
- **None of the lost runs involved D1.** `TASK_ENTITY_UNANCHORED` fired in 10 runs (01-03 r1, r2; 02-01 r3; 02-03 r1; 04-05 r2; 12-03 r1, r2; 12-04 r2; 16-03 r3; 16-07 r1). Of the 6 graded, 5 passed. 04-05 r2 failed, but 04-05 scored the same as in the original. So in every lost run, EXECUTE got its entities exactly as the original would have built them from that BOOTSTRAP reply (static, S3). The losses are not caused by vNext's change: those runs are draws from the original's own process (recorded artifact, static). That process's variation includes BOOTSTRAP's entity draw (audit below), so this does not show that entities are irrelevant to the losses.
- **Audit of the sent requests** (recorded artifact, `provider-requests/` of both sweeps, after ChatGPT's review via the user):
  - BOOTSTRAP's body is byte-identical in every run of all 42 prompts, in both sweeps.
  - Between any two runs of one prompt, in either sweep, EXECUTE's body differs **only in `TASK_ENTITIES`**: every other input, the instructions, effort, caps and pinning are identical. In the original as in vNext, the entity payload is the only part of EXECUTE's input that varies from run to run. It differed in every comparison.
  - System 1's problem class varied only on 04-04 and 16-01, in both sweeps; neither lost or gained.
  - 01-01, all 6 runs: every payload's meanings restate the request's constraint correctly. A passing payload (original r3: `a_i`, `b_i`, `c_i` as targets, the sum as given) has the same structure as a failing one (vNext r3). Every failure is computational: no exact partition found (0 or 3 valid triples), the original's r1 included. At n = 6 there is no visible link between the payload and the outcome, and no way to rule one out.
  - Category 1 under the original, with the full entity block: 20 of 21. Under vNext: 18 of 21, all losses on 01-01.
- **04-06 failed all 3 runs the same way** ("Expected SEMI, got EOF" on the prompt's own example). The original failed it once, cancelled. This consistent failure is worth watching in stage 3, but it is not D1's: no entity was unanchored in those runs.
- **Next:** stage 3 (`run_catalogue.py --fail-fast`, about $0.40, cap $0.60), on the user's go. Stage 2 is not needed.

### 5.2 Fixed-entity experiment (proposed by ChatGPT via the user; design fixed before any result)

- **Question:** does the entity block's content change EXECUTE's pass rate, with the extraction held fixed? This is a question about the original's design. It does not decide vNext's merge.
- **Prompts:** 01-01 and 04-06 (both lost in stage 1, computational) and 16-06 (gained, logical). Each is reported separately, never pooled.
- **Frozen extraction, by a rule fixed in advance:** for each prompt, the original's (L99) first repeat, its first BOOTSTRAP reply. It is the same reply in all arms. BOOTSTRAP makes no model call; System 1, EXECUTE, its retries and the host's verification run as usual.
- **Arms** (only EXECUTE's `TASK_ENTITIES` differs):
  - **A:** `--no-task-entities`, so `TASK_ENTITIES` is present and empty;
  - **B:** the full block, as the original sent it;
  - **C:** the block without the model-written meanings. Each entity's `relation` is removed from the frozen reply, so `condition` and `relation` go out as null; names, kinds, statuses and groups are kept.
- **Runs:** 20 blocks. Each block is the 9 (arm, prompt) pairs in a seeded random order (seed 20261009). The catalogue's own runner and graders are used (`run_catalogue.run_single_prompt`), through `experiments/l100_vnext/frozen_cli.py`. The experiment stops between blocks once it has spent its cap.
- **Checks:**
  - Offline dry run, before anything is spent (`fixed_entity.py dryrun`): **pass**. For all 3 prompts, B's EXECUTE body is byte-identical to the one L99 sent in that run. A's and C's differ from it only in `TASK_ENTITIES`, as their arm says. No network was used (offline, via the catalogue's runner and child process).
  - Live: `report` checks each run's recorded EXECUTE body the same way.
- **Reading, per prompt** (two-sided Fisher exact test on PASS of decided, p < 0.05 counts as a difference):
  - B below A and C close to A: the model-written meanings are a candidate for harm.
  - B and C both below A: something broader in the block interferes.
  - B above A on 16-06 but below on 01-01: a task-dependent trade-off.
  - No difference: inconclusive at this size (about 40-point effects detectable). This does not show that the content is irrelevant.
- **Cost:** from L99's recorded tokens, about $0.0053 a run for 01-01, $0.0033 for 04-06 and $0.0009 for 16-06. That is about $0.03 a block, about $0.60 for 20 blocks. **Cap: $0.80.**
- **Stage 3 caveat:** `--fail-fast` stops at the first failed prompt (`run_catalogue.py:709`), and the catalogue starts with 01-01. 01-01 failed 4 of its last 6 runs, and PR #1's gate stopped there (waived by the user, `protocol-fixes-plan.md`). So the literal gate will almost surely stop at 01-01 for about a cent, which says nothing about vNext. The alternative is one full pass of all 16 categories without `--fail-fast` (about $0.40, cap $0.60), compared per category with the last full unconfirmed run (`run-20261008-061233`, `7a882f10`: 41 of 53 decided, 77.4%; provider not pinned then). The user decides.

## 6. Decisions for the user

1. Adopt this plan: restore the original contract, D1, and the L100 host-only fixes; remove v3's index.
2. D2 (drop the duplicated keys from EXECUTE's input): include it now, or keep EXECUTE's input identical and test D2 later as its own delta. Recommendation: later, so S3 proves identity in its strongest form.
3. Close v3 in the ledger as superseded (its live check stands as recorded).

## 7. Implementation

Between `a5973ae7` and HEAD, 27 files changed, all of them L100 (static, `git diff --stat a5973ae7 HEAD -- src tests contracts scripts`). So the restore is a file checkout from `a5973ae7`. The host-only fixes are then re-applied on top as small, separate edits.

### 7.1 Files

| Action | Files |
|---|---|
| **Restore from `a5973ae7`, byte for byte** | `runtime/wire_payloads.py`, `runtime/operation_bridge.py`, `runtime/session_engine.py` (then E1-E3 below), `providers/live_stub.py`, both `EXECUTION_CONTRACT.json` and `CONTRACT_MANIFEST.json`; tests `test_task_entities.py`, `test_targeted_probe_16_06_09_01.py`, `test_pydantic_wire.py`, `test_output_contracts.py`, `test_unconfirmed_route.py`, `test_execution_brief.py`, `test_computation_recipe.py`, `test_reasoning_wire.py`; fixtures `prompt_schema_descriptions.json`, `recorded-cases.json` |
| **Delete** (L100 only, no consumer after the restore) | `runtime/request_index.py`, `runtime/quotes.py` (D1 does not need it; the corpus scripts keep a copy in `experiments/l100_vnext/`), `tests/test_request_index.py`, `tests/test_entity_quotes.py`, `tests/entity_stub.py` |
| **Re-apply** (host only) | `runtime/workspace.py` (`write_turn_entities`, `turn_entities`, from `d664c63e`); `host/repl.py`, `host/app.py`, `providers/api_worker.py`, `run_catalogue.py` (the off switch, renamed) |
| **New** | `tests/test_entity_vnext.py` (E1-E3); `experiments/l100_vnext/static_checks.py` (S1-S5) |

### 7.2 The three edits to the restored `session_engine.py`

- **E1, D1** (in `_semantic_read`'s matcher loop):
  - The original's `else: matched = None` becomes: sanitize the model's name (`compile_bootstrap_output(raw_text, surface)`).
  - If it is non-empty and has no `[REDACTED_IOC]`, keep the entry under that name, add `"name_source": "model"` to its forwarded dict, mark it in the drafting render, and count it in a `TASK_ENTITY_UNANCHORED {count}` event. Otherwise drop it, counted in the existing `TASK_ENTITY_DROPPED_UNSAFE`.
  - The coverage tuple excludes the unanchored names.
  - Nothing else in the loop, the forwarding (`typed_entities`) or the drafting render changes.
- **E2, entities kept with the turn** (from `d664c63e`):
  - After each of the two activation points (confirmed and unconfirmed), `workspace.write_turn_entities(names, forwarded)`.
  - In `restore()`, `workspace.turn_entities()` refills `_active_task_entities` and `_active_typed_task_entities`.
  - No model input changes, except that a restored session's EXECUTE now gets its entities, which is the fix.
- **E3, the off switch** (`self.task_entities_enabled`, default `True`; set by the host from `--no-task-entities`). When it is off:
  - EXECUTE_UNCONFIRMED gets `TASK_ENTITIES: []`. The symbol stays in `include`, so with the switch on the contract is the original's.
  - Confirmed EXECUTE and DRAFT_EXECUTE get no `TASK_ENTITIES`.
  - The drafting context has no entity block.
  - BOOTSTRAP and the host check run as usual, so the arms differ only in what later stages receive.

D2 is not in this build (recommended in decision 2). If you choose it, it is one more edit, E4: the `typed_entities` dict loses three keys, and S3 then expects that diff in every run.

### 7.3 Order of work, each step gated offline

1. **Restore and delete** (7.1).
   - Gate: the offline suite passes.
   - Gate: `recorded-cases.json` replays with its `a5973ae7` keys and no `ReplayMissError`. That is already proof that what the models receive in that corpus is the original's.
2. **E2 and E3**, switch on by default.
   - Gate: the offline suite.
   - Gate: S1 against a worktree of `a5973ae7`, zero differences.
3. **E1 and its tests.**
   - Gate: the offline suite.
   - Gate: S1 still shows zero differences. D1 acts after BOOTSTRAP replies, so its request cannot change.
4. **S2-S6** on the corpus. Gate: section 4's criteria, unchanged.
5. **S7:** the anti-overfitting suite under `-W error` and the offline suite. Then commit and update the ledger, and stop: the measurement runs only on your approval.

**Live-check trigger** (`AGENTS.md`):
- The restore changes nothing a model receives relative to `a5973ae7`: S1, and the replay keys of step 1.
- E1 changes EXECUTE's input in the runs where the original dropped an entry. That is a change to what the model receives, so one live run is due before merge. The outcome measurement (section 5) is that run.
- `run_catalogue.py --fail-fast` is due before merge, as for any behaviour change.

### 7.4 What S3 needs to replay a run

- **System 1:** a client that answers from the run's recorded events (3.1).
- **BOOTSTRAP:** a model worker that returns the recorded `model-response.txt` files in order, including a degenerate-read retry when one was recorded.
- **EXECUTE:** a stub that records the projection and stops the session.
- **Comparison:** the captured `document` against the run's recorded `compiled-projection.json`, field by field.
  - A difference outside `TASK_ENTITIES` fails S3, whatever it is. For example, a different `AVAILABLE_EXECUTION_TOOLS` text means the environment differs and must be reconciled before any conclusion.
  - Inside `TASK_ENTITIES`, the only allowed difference is D1's added entries, in the runs of section 2.

## 8. Research

- Google, LangExtract: each extraction is grounded to exact character offsets in the source; extractions that cannot be located get no interval and are filtered by the caller, and descriptive attributes sit beside the grounded text. [Developers blog](https://developers.googleblog.com/en/introducing-langextract-a-gemini-powered-information-extraction-library/), [GitHub](https://github.com/google/langextract).
- Tam et al., *Let Me Speak Freely?* (EMNLP 2024 Industry): stricter format constraints degrade reasoning, and key order matters. [arXiv 2408.02442](https://arxiv.org/abs/2408.02442).
- Wang et al., *Plan-and-Solve Prompting* (ACL 2023): having the model first divide the task into subtasks, then carry them out, improves zero-shot reasoning, the role the original's decomposition plays for EXECUTE. [arXiv 2305.04091](https://arxiv.org/abs/2305.04091).

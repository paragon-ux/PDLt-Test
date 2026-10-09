# Task entities vNext: the original as the contract (plan, ledger L100)

Status: **plan for the user's review** (2026-10-09). Nothing built. The user decided that the original entity model (L99, commit `a5973ae7`) is the baseline to beat, and that vNext must be planned and verified statically before any live run. Supersedes [ENTITY_V3_DESIGN.md](ENTITY_V3_DESIGN.md) and the request index built in `3acc08ec`.

Evidence labels: **static** (code at a cited commit), **corpus** (L99's 126 recorded unconfirmed runs, `catalogue-runs/run-20261009-042907-unconfirmed-tier-d1`, read offline by `experiments/l100_vnext/orig_corpus.py` and `orig_defects.py`), **research** (cited at the end).

## 1. What the original carries

On the unconfirmed route, `TASK_ENTITIES` is the only BOOTSTRAP output that reaches EXECUTE; the rest of EXECUTE's input is the request, the clauses and the tools (static, `session_engine.py` at `a5973ae7`, lines 2231-2263). The original gives EXECUTE a decomposition of the task, written by the model:

| # | Property | Measured (corpus) |
|---|---|---|
| P1 | **A flat list of the task's parts**, one entry per thing given or to produce | 1,216 entries in 118 analyses (10.3 per run) |
| P2 | **A role written by the model**: `target` means to be found, determined or *produced*, so a build task's parts are targets | 437 targets; every analysis wrote at least one, on the first reply; target kinds: term 190, identifier 159, literal 70 |
| P3 | **A one-line meaning in the model's words**, forwarded to EXECUTE after the sanitizer | 1,110 of 1,216 entries (91%); 41% of their words do not occur in the request, so this is interpretation, not a copy |
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

**In the live measurement**, System 1 runs live and identically in every arm (same recipes, same model), so its run-to-run variation is shared across the paired arms.

## 4. Static acceptance (criteria fixed before the build)

| # | Test | Method | Pass |
|---|---|---|---|
| S1 | **BOOTSTRAP is asked the same thing** | render BOOTSTRAP's request for every catalogue prompt at `a5973ae7` and at vNext (`scripts/render_recorded_prompts.py render`, then `compare`) | byte-identical. The model's extraction is then the measured one (P1-P4) |
| S2 | **Every recorded reply parses** | the 118 recorded original replies through vNext's parser | 118 of 118, no rejection or retry |
| S3 | **EXECUTE receives the same input** | replay each recorded run through the vNext engine offline: System 1 answers from the run's recorded events (section 3.1); BOOTSTRAP's recorded replies are returned in order; a stub EXECUTE captures its projection. Diff against the recorded EXECUTE projection | identical, except where the diff is a listed delta: D1 in the 7 runs of section 2, and D2 everywhere if chosen |
| S4 | **Each delta does only what it says** | D1: the entries gained are exactly the dropped non-hostile ones (16-06 r3 and 16-03 r2 regain their target; 09-04 r2's payload stays out). D2: the set of (name, kind, status, group, meaning) is unchanged in every run | exact match |
| S5 | **Containment** | across the corpus and the unit fixtures: no forwarded name or meaning carries a canary, an override phrase or a redaction marker; 09-* forwarded payloads are a subset of the original's plus D1's | zero |
| S6 | **Restore** | a session restored from disk sends EXECUTE the same entities as the live session | identical |
| S7 | **Suites** | `pytest tests/test_harness_anti_overfitting.py -W error`, the offline suite, the description snapshot back to the original's texts | all pass |

If S1-S4 pass, vNext's EXECUTE input matches the original's exactly, except D1 (and D2). Its expected pass rate is then the original's plus whatever D1 and D2 change, known before any live run. If S1 or S3 fails, the build is not the original and is fixed before anything else.

## 5. Live (after S1-S7 only)

- **The outcome measurement:** six L99 categories, 3 repeats, the same day, paired, about $1.53. Arms:
  - A: vNext with entities off;
  - B: vNext;
  - C: the original (`a5973ae7`);
  - D: Control.
- **Prediction, written now:**
  - B ≥ C;
  - B and C differ only in D1's runs, and in D2's if chosen;
  - A < C on the coding prompts.
- **Falsified by:** B losing more paired runs to C than it gains. That would mean S3's identity did not hold in the live request, so the cause would be looked for in what the provider received, not in the schema.

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
  - If it is non-empty and has no `[REDACTED_IOC]`, keep the entry under that name and count it in a `TASK_ENTITY_UNANCHORED {count}` event. Otherwise drop it, counted in the existing `TASK_ENTITY_DROPPED_UNSAFE`.
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

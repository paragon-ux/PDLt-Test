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
- The host keeps an entry whose sanitized name is non-empty and carries no redaction marker. It records host-side whether the name is found in the request (`anchored`, telemetry only, never forwarded).
- A name the sanitizer redacted, such as 09-04 r2's payload, is dropped as today.
- The coverage telemetry reads only anchored names of exact kinds.
- This replaces the request-or-summary match. EXECUTE's input changes only in runs where the original dropped something.

**Delta D2 (optional): drop the duplicated keys** from the forwarded entries (`polarity`, `collection`, `condition`). The information is identical and the input is 42% shorter. It is the one change to every EXECUTE input, so it is kept separate (decision 2).

**Removed:** the v3 request index (`request_index.py`, `TASK_INDEX`), which carries no role or meaning.

## 4. Static acceptance (criteria fixed before the build)

| # | Test | Method | Pass |
|---|---|---|---|
| S1 | **BOOTSTRAP is asked the same thing** | render BOOTSTRAP's request for every catalogue prompt at `a5973ae7` and at vNext (`scripts/render_recorded_prompts.py render`, then `compare`) | byte-identical. The model's extraction is then the measured one (P1-P4) |
| S2 | **Every recorded reply parses** | the 118 recorded original replies through vNext's parser | 118 of 118, no rejection or retry |
| S3 | **EXECUTE receives the same input** | replay each recorded reply through the vNext engine offline (stub EXECUTE captures its projection); diff against the recorded EXECUTE projection | identical, except where the diff is a listed delta: D1 in the 7 runs of section 2, and D2 everywhere if chosen |
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

## 7. Files

- `runtime/wire_payloads.py`;
- `runtime/session_engine.py` (`_semantic_read`, the forwarding, the EXECUTE contexts);
- `runtime/operation_bridge.py`;
- `runtime/request_index.py` (removed);
- `runtime/workspace.py`;
- both `EXECUTION_CONTRACT.json` and their manifests;
- `host/repl.py`, `host/app.py`, `providers/api_worker.py`, `run_catalogue.py` (switch name);
- tests;
- `tests/fixtures/prompt_schema_descriptions.json` and `recorded-cases.json` (back to the original keys).

## 8. Research

- Google, LangExtract: each extraction is grounded to exact character offsets in the source; extractions that cannot be located get no interval and are filtered by the caller, and descriptive attributes sit beside the grounded text. [Developers blog](https://developers.googleblog.com/en/introducing-langextract-a-gemini-powered-information-extraction-library/), [GitHub](https://github.com/google/langextract).
- Tam et al., *Let Me Speak Freely?* (EMNLP 2024 Industry): stricter format constraints degrade reasoning, and key order matters. [arXiv 2408.02442](https://arxiv.org/abs/2408.02442).
- Wang et al., *Plan-and-Solve Prompting* (ACL 2023): having the model first divide the task into subtasks, then carry them out, improves zero-shot reasoning, the role the original's decomposition plays for EXECUTE. [arXiv 2305.04091](https://arxiv.org/abs/2305.04091).

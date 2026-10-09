# Task-entity redesign (ledger L100)

Status: **approved by the user (2026-10-09), section 8 answered**; nothing built or run yet. Branch `claude/final-five-arm-benchmark`.

## 1. Provenance

| Source | What it contributed |
|---|---|
| The user, side chat 1 (Antigravity/Gemini, 2026-10-09; exported as `PDL Benchmark and Release Evaluation.md`) | Found the defect from 16-06's recorded entities: "answer" and "expression" accepted as targets; "sisters" given and "How many sisters" target in the same run; `relation` used as a gloss of the entity instead of what is known and unknown about it. The user also decided to drop `polarity`: one polarity is confusing when an entity mixes known and unknown. |
| Side chat 1 | Traced the wording to `wire_payloads.py` (added in L56/L57) and the duplicated fields to `session_engine.py`. Proposed a free-text `relation` of the form "known: ...; unknown: ...". |
| Main chat (2026-10-09) | Verified both in the code (section 2), measured the baseline (section 3), proposed a System 1 (Jev) check on `relation` against injected content. |
| Side chat 2 (2026-10-09, pasted into main) | Replaced free text with verbatim quotes checked by the host, which closes the injection gap mechanically, so no Jev check is needed for it. Found that the "answer"/"expression" wording also sits in the `surface` description. |
| Main chat | Agreed; refined the untrusted-section handling (section 4.5) and the matching rules (section 4.3). |
| The user with ChatGPT (2026-10-09, 07:04-07:17; exported as `ChatGPT-Design Relation Evidence-20261009-0720.md`) | The user requires a rule for telling an implicit unknown from the knowns, so that implicit relations are neither written out nor lost. Several rejected versions led to the final one: a registry of rules, which was problem-specific; general invariants, which were too much for gpt-oss-120b on low; and count comparisons such as `n(known) < n(unknown)`, which don't show whether the knowns settle the question. The final version: `relation` becomes `{known, unknown, distinction}`, where `distinction` is one operator from a closed list (`direct`, `implicit`, `undetermined`, `conflict`). |
| Main chat | Agreed, with one recommendation: drop `direct` (open question 3, section 4.2.1). |
| The user with ChatGPT (2026-10-09, 07:28; exported as `ChatGPT-Design Relation Evidence-20261009-0731.md`) | Open question 1. The user worried that requiring the name to appear in the request would make misspellings literal and tie the model to the user's accuracy, while misspellings can also be injection attempts. ChatGPT: require a mention traceable to the request, keep its spelling, never treat the spelling as correct or as authority, never validate a name against the model's summary, and add no canonical-name field. Main chat agrees, with three refinements (section 4.3). The user then answered all three open questions (section 8). |

Precedence (`AGENTS.md`): side chat 2's quote design replaces side chat 1's free-text "known/unknown" and the main chat's Jev check. All three agree on the problem; the change is in the mechanism, so this is a minor conflict. The user's `distinction` puts back one closed-vocabulary judgment at this stage, where side chat 2 had said this stage should only extract. That is the user's decision, and recorded as such.

## 2. The defect (static, verified)

- `wire_payloads.py:116-121` (`surface`): "copy the exact word or short phrase ... (for example the word naming what is asked about, or "answer", "expression")", and "When the request uses the same text for two different things ... list one entity per thing: each repeats the surface".
- `wire_payloads.py:138-142` (`status`): a target is "the exact word or phrase the request uses for what it asks about (e.g. following "how many" ... or naming the requested deliverable, such as "answer" or "expression"), even when it uses an ordinary word that also appeared as given (list that word again with status "target")".
- `wire_payloads.py:158-167` (`relation`): free text written by the model: "what it is or stands for, its value, its constraints ...". It is the only entity field the host cannot verify: `surface` must appear word for word in the request or summary (`session_engine.py:853-899`), and `kind` and `status` are fixed lists of values.
- Where `relation` goes: into the task summary that drafting reads (`session_engine.py:933-960`) and into `TASK_ENTITIES` for EXECUTE (`session_engine.py:1848-1859`, `2231-2263`). The only check on it is `compile_bootstrap_output` (`quarantine.py:59`), which redacts known hostile tokens (canaries, override phrases), not new wording.
- `session_engine.py:911-920` sends every entity with three pairs that duplicate each other: `status` and `polarity`, `group` and `collection`, `relation` and `condition`.
- Unrelated and unchanged: the witness `polarity` (positive, negative) in `result_ir.py`, `verification/checkers/fallback.py` and `wire_payloads.py:670-721`.

## 3. Baseline (recorded artifacts, offline)

From L99's unconfirmed run (`catalogue-runs/run-20261009-042907-unconfirmed-tier-d1`, 126 runs, six categories):

| Measure | Value |
|---|---|
| Runs whose EXECUTE received `TASK_ENTITIES` | 118 of 126 |
| Entities per run | 10.2 on average (1,205 in total) |
| Runs with no target | 2 |
| Targets per run | median 3 |
| Runs with a duplicated surface | 4 |
| Surfaces that begin with a question word | 4 |
| Reply-form words as targets | 2 entities, both in 16-06 r1 |
| Entities with a model-written `relation` | 1,099 of 1,205 (mean 50 characters) |

So in these categories the reply-form targets and duplicates are rare. The broad exposure is `relation`: almost every entity carries the model's own reading of the request into later stages. That 16-06 failed *because* of it ("answers S") is a hypothesis this plan tests (section 6), not a finding.

## 4. Design

### 4.1 What an entity is

An entity is a thing, quantity, role, setting or piece of data the task is about. Words that only name the reply or its format are not entities. Each thing is listed once. The rule is stated in the schema descriptions; there is no list of banned words and no regex (ADR-0018, GUARD-01).

### 4.2 The wire model (`TaskEntity`)

| Field | Type | Meaning |
|---|---|---|
| `surface` | str | The request's own mention of the thing, copied exactly with its spelling (typos included), without question words: a name, symbol, role or short description, the most specific one the request uses (not a bare pronoun). It records where the entity came from; it does not claim the spelling is correct. |
| `kind` | identifier, input_data, literal, parameter, term | Unchanged. |
| `status` | given, target | The only role field. `target` when the request asks for anything about the entity to be found, determined, computed, chosen or produced; `given` otherwise. An entity the request both describes and asks about is a target. |
| `group` | str or null | Unchanged. |
| `relation` | object or null | How the request's statements about the entity stand to what it asks about. Three fields, below. Null when the request only names the entity. |
| `relation.known` | list of str | Exact quotes from the request that state facts, values, rules or constraints about the entity. May be empty. |
| `relation.unknown` | str or null | For a target: the exact quote that asks about it (the question, or the instruction to produce it). Null for a given entity. |
| `relation.distinction` | one closed operator, or null | How `unknown` stands to `known` (section 4.2.1). Null when `unknown` is null. |

Removed: the free-text `relation` (now the object above) and the derived properties `polarity`, `collection` and `condition`.

Inbound aliases (ADR-0018 coercion, for recorded payloads and models that use old names): `polarity` still maps to `status` and `collection` to `group`; `known` and `unknown` given beside `relation` instead of inside it are moved in; a string `relation`, `condition` or `definition` is dropped and counted, since free text cannot become a quote.

16-06's entity would be:

```json
{"surface": "sisters", "kind": "term", "status": "target", "group": null,
 "relation": {
   "known": ["Maya has B brothers and S sisters", "Every brother and sister shares both parents with Maya"],
   "unknown": "How many sisters does each of Maya's brothers have?",
   "distinction": "implicit"}}
```

#### 4.2.1 `distinction`: telling an implicit unknown from the knowns

`known` and `unknown` show what the request says. They don't show whether the answer is already among the stated facts, and that is where 16-06 went wrong: "Maya has S sisters" was treated as the answer to "how many sisters does each brother have?". `distinction` records that judgment as a single operator. The model never writes the implicit fact, which would launder an inference into the contract; it only marks that the unknown has to be worked out.

| Operator | Meaning (the host's fixed wording, rendered downstream) |
|---|---|
| `implicit` | The request does not state the answer; it has to be worked out or produced from what the request states. |
| `undetermined` | What the request states is not enough to settle it. |
| `conflict` | The request's statements about it contradict each other. |

Rules:
- One operator per target, chosen from the closed list. No prose, no counts, no rule registry: the user's limit for gpt-oss-120b on low, and the reason the other versions were rejected (section 1).
- Null for a given entity (no `unknown`). If the host drops the `unknown` quote, it drops `distinction` with it, so a judgment never outlives its evidence. `conflict` needs at least two kept `known` quotes, since a contradiction takes two statements; otherwise it is dropped. These checks are deterministic.
- Whether the right operator was chosen can't be checked mechanically. The field can't carry injected text (it is a closed value), but it can be wrong. Downstream it is labeled as the extraction step's classification, never as a fact. `undetermined` does not by itself pause a run or ask for input; that stays with the existing input-request logic.
- **No `direct` (decided, section 8).** ChatGPT proposed a fourth value, `direct` ("the answer is stated in the known quotes"). It is the one value that would turn an unknown into a known: 16-06's misreading would be recorded exactly as `direct`, and EXECUTE would receive it as structure. Without it, every target is marked as needing work, input or a resolution, never as already answered. A target whose answer really is stated loses nothing: `implicit` then means "trivially worked out". A model that returns `direct` anyway has it dropped and counted.

### 4.3 The host check (deterministic, free, offline-testable)

In `_semantic_read`, after BOOTSTRAP replies:

1. **Surfaces** keep today's word-for-word test, against the request only (decided, section 8). The match against the model-written summary is removed, so the summary cannot vouch for a surface the request doesn't contain. The test establishes where a mention came from, never that it is spelled right or safe to follow. Three refinements:
   - Whether spelling binds depends on `kind`. For `identifier`, `literal`, `input_data` and `parameter` the request's spelling is the value (a misspelled function name is the function's name), and the existing coverage check already requires it exactly. For a person or a `term`, the surface only points to the thing; what it refers to, typo or not, is worked out downstream.
   - The surface is the most specific mention the request uses, not a bare pronoun, because the host merges entries that share a surface (item 4).
   - A model that silently corrects the user's spelling loses the entity, because its version is not in the request. The live check counts dropped surfaces. If drops are frequent, the fallback is a host-side near-match that maps to the request's own text (the request's spelling is kept, never the model's), decided then, not now.
2. **Quotes** (`relation.known` items and `relation.unknown`) are kept only if each one appears in the sanitized request as one continuous span. The match folds only typography: Unicode normalization, dash variants to "-", curly quotes to straight ones, and whitespace runs (including non-breaking and narrow spaces) to one space. gpt-oss writes U+2011 and U+202F often (seen in the L97 outputs). The host then replaces the model's copy with the request's own text for that span, as it does for surfaces today.
3. A quote that doesn't match is dropped, never repaired. Each drop is counted in an event (`TASK_ENTITY_QUOTE_DROPPED`). A target that loses its `unknown`, or never had one, stays a target and is counted (`TASK_ENTITY_TARGET_UNANCHORED`).
4. Entities whose surfaces are the same after the same folding are merged: quotes are combined and deduplicated, and the result is a target if any copy was a target. This makes "one per thing" a host guarantee rather than a request to the model.
5. Every kept quote still passes `compile_bootstrap_output`, as `relation` does today.
6. **`distinction`** goes through the checks in section 4.2.1: a value from the closed list, null without an `unknown`, dropped with its `unknown`, and `conflict` only with two or more `known` quotes. When merged entities disagree, `undetermined` and `conflict` take precedence over `implicit`, so a merge never hides a gap. Each drop is counted (`TASK_ENTITY_DISTINCTION_DROPPED`).

### 4.4 What later stages receive

- `TASK_ENTITIES` items have exactly `surface`, `kind`, `status`, `group` and `relation` (`known`, `unknown`, `distinction`). No duplicated pairs.
- The task summary renders each entity as its surface, kind and role, then its quotes, marked as quotes, and the meaning of its `distinction` in the host's own fixed wording:

  ```
  - sisters (term) [TARGET]
      stated: "Maya has B brothers and S sisters"; "Every brother and sister shares both parents with Maya"
      asked: "How many sisters does each of Maya's brothers have?"
      extraction step's reading: not stated; to be worked out from what is stated
  ```

- No stage receives a model-written description of an entity any more. Interpretation moves to where it is checked or visible: the prompt artifact on the confirmed route (System 1 fidelity check), and EXECUTE's own working notes on the unconfirmed route. The only judgment carried forward is `distinction`, which is a closed value and labeled as a judgment.

### 4.5 Untrusted text inside a request

A quote is only as trustworthy as the request text it copies. If a request carries untrusted material, such as the planted instructions in the L97 tasks and category 09, an entity's `known` list could quote it, and in `TASK_ENTITIES` it could read like part of the host's contract. Surfaces have the same exposure today.

The host has no map of which parts of a request are untrusted: `isolate_untrusted_input` (`quarantine.py:48`) wraps the whole request, and requests mark untrusted material in prose. So the fix is framing rather than labels per quote. Quotes are passed down as quoted request text, inside the same untrusted wrapper the request gets, and never restated as requirements. A label the model declares itself (for example "this quote comes from supplied material") can't be checked, so it isn't used. Category 09 and the L97 planted instructions test this (section 6).

### 4.6 Schema descriptions (what BOOTSTRAP receives)

Rewritten for `surface`, `status`, `relation` and its three fields, the `term` kind (which now refers to `relation.known` quotes, not a rule sentence), and the `task_entities` list itself (`wire_payloads.py:255-265`, which says "put descriptions in relation"). They drop both "answer"/"expression" examples and both "list it again" instructions, and state sections 4.1-4.2.1. `distinction` is described with one plain sentence per operator, kept short for gpt-oss-120b on low. No example is taken from a catalogue prompt. Draft wording is reviewed with the code change, and `tests/fixtures/prompt_schema_descriptions.json` is updated with it.

### 4.7 Not in this change

- A System 1 check on entities. Injection no longer needs one. A meaning check on whether an entity's `status` is right is a possible later recipe, decided after the measurement.
- Typed relations (for example `count_of(sisters, brother)`) and a registry of inference rules: checkable, but too rigid for the catalogue's range of tasks and too much for a small model (section 1).
- A rule that prompt artifacts list the assumptions they make where the request is open. It would help review and fidelity judging, but it changes the prompt stage and is a separate decision.

### 4.8 Implicit entities and implicit knowns

- **Implicit entities** (things the request never names) have no verbatim surface, so they are not entities. With surfaces matched against the request only (open question 1), none get in.
- **Implicit knowns** (facts the request implies but doesn't state, such as 16-06's crux) are never written at this stage. Writing them would do the reasoning early, and the executor would inherit it, right or wrong. In this project, DRAFT_EXECUTE's pre-written brief lowered pass rates (L93/L95). `distinction: implicit` marks that such reasoning is needed, without doing it.
- **Missing information** keeps its own channel, the input request (graded by 13-06). `undetermined` labels it but does not trigger it.
- **Known limitation:** `task_summary` stays model-written free text. It is sanitized and wrapped as untrusted, as today, so it keeps the exposure that `relation` had. This change does not touch it.

## 5. Risks

- **Fewer targets (L56/L57):** the "answer" wording was added because models marked every entity given. Measured by runs with no target (baseline 2 of 118) and by `TASK_ENTITY_TARGET_UNANCHORED`.
- **Quotes that fail to match:** a model that tidies punctuation or spacing loses its quotes. Measured by the drop rate in the live check; the folding rules are the fix, never a looser match.
- **Longer inputs:** quotes are longer than 50-character glosses. Measured as input tokens per run; a cap on quotes per entity only if the measurement calls for it.
- **Lost readings:** later stages no longer receive the model's paraphrase of each entity. This is intended (section 4.4); it is measured, not assumed, by the comparison in section 6.
- **A wrong `distinction`:** the value is closed but chosen by the model. A wrong `undetermined` could push EXECUTE to ask for input it doesn't need (measured by input-request exits). If `direct` is kept, a wrong `direct` encodes the lookup error that 16-06 made. Measured in the live check against expected values (section 6.2).
- **Replay misses:** BOOTSTRAP's request changes, so recorded replays that include BOOTSTRAP miss. They are re-recorded after the live check.

## 6. Verification (`AGENTS.md`: static first, offline before live)

1. **Offline.** Unit tests:
   - quotes matched, folded and replaced by the request's text;
   - quotes not in the request dropped and counted;
   - quotes containing a canary redacted;
   - surfaces merged;
   - `distinction` dropped with its `unknown`, `conflict` dropped with fewer than two `known` quotes, and the merge precedence applied;
   - inbound aliases accepted and old fields dropped;
   - `TASK_ENTITIES` has only the five keys, with `relation` holding `known`, `unknown` and `distinction`;
   - the summary renders quotes as quotes;
   - the witness `polarity` untouched.

   Then the anti-overfitting suite under `-W error` and the offline suite.
2. **Live check, one run per prompt,** because what BOOTSTRAP receives changes. Question: does gpt-oss on Cerebras produce quotes that survive the check, with every question anchored to a target?
   - Prompts: 16-06, 09-01, 09-04, the three L97 tasks (long, with attachments and planted instructions), 02-05, 04-07 and one category 12 prompt.
   - Add a missing-information prompt (13-06).
   - Expected:
     - at least 90% of quotes kept;
     - at most 10% of surfaces dropped;
     - every run has a target with a kept `unknown`;
     - no duplicated surfaces;
     - no planted text in an `unknown`;
     - `distinction` is `implicit` for 16-06's target and `undetermined` for what 13-06 leaves out;
     - no `undetermined` or `conflict` on the prompts that state everything they need.
   - Falsified by any of:
     - fewer than 80% of quotes kept;
     - more than one run without an anchored target;
     - a wrong `distinction` on 16-06 or 13-06.

     The fix is then to the descriptions or the folding, never a looser match.
3. **Catalogue gate:** `python run_catalogue.py --fail-fast` before merge.
4. **Measurement** (priced and approved before any call; open question 2). Six categories (L99's: 01, 02, 04, 09, 12, 16) with 3 repeats, on the same day:
   - unconfirmed at the pre-change commit;
   - unconfirmed at the post-change commit;
   - Control (Control has no entities, so it checks the day's drift);
   - and the confirmed route at the post-change commit ("confirmed never got a fair shake").

   Paired by prompt and repeat; exact McNemar per run and a sign test per prompt, as in L99.
   - **Written before the run:** post-change unconfirmed passes at least as many runs as pre-change, with 16-06 improving, category 09 containment unchanged and no more input-request exits.
   - **Falsified if:** it loses more paired runs than it gains, 09 containment worsens, or input-request exits rise.

## 7. Files

`runtime/wire_payloads.py` (`TaskEntity`, descriptions, aliases); `runtime/session_engine.py` (`_semantic_read` filter, merge, emission, summary rendering); a small matching helper beside `runtime/quarantine.py`; any contract or clause text that names entity fields (none found by search; checked again during the build); tests (`test_task_entities.py`, `test_pydantic_wire.py`, `test_targeted_probe_16_06_09_01.py`, the schema-description and recorded fixtures); `docs/plans/LEDGER.md`.

## 8. Open questions for the user

All answered by the user on 2026-10-09:

1. **Surface matching:** against the request only, keeping the user's spelling; never against the model's summary (with ChatGPT's reasoning and the refinements in section 4.3). **Yes.**
2. **Measurement scope:** the same-day four-arm run in section 6.4, priced before any call. **Yes.**
3. **`distinction` values:** `implicit`, `undetermined`, `conflict`, without `direct`. **Yes.**

## 9. Steps

1. ~~The user reviews this plan and answers section 8.~~ Done, 2026-10-09.
2. Build sections 4.2-4.6 with the offline tests (6.1).
3. Live check (6.2); re-record the replays it invalidates.
4. Catalogue gate (6.3).
5. Measurement (6.4), then the ledger row's outcome.

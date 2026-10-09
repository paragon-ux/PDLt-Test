# Task-entity redesign (ledger L100)

Status: **plan for the user's review**; nothing built or run. Branch `claude/final-five-arm-benchmark`.

## 1. Provenance

| Source | What it contributed |
|---|---|
| The user, side chat 1 (Antigravity/Gemini, 2026-10-09; exported as `PDL Benchmark and Release Evaluation.md`) | Found the defect from 16-06's recorded entities: "answer" and "expression" accepted as targets; "sisters" given and "How many sisters" target in the same run; `relation` used as a gloss of the entity instead of what is known and unknown about it. The user also decided to drop `polarity`: one polarity is confusing when an entity mixes known and unknown. |
| Side chat 1 | Traced the wording to `wire_payloads.py` (added in L56/L57) and the duplicated fields to `session_engine.py`. Proposed a free-text `relation` of the form "known: ...; unknown: ...". |
| Main chat (2026-10-09) | Verified both in the code (section 2), measured the baseline (section 3), proposed a System 1 (Jev) check on `relation` against injected content. |
| Side chat 2 (2026-10-09, pasted into main) | Replaced free text with verbatim quotes checked by the host, which closes the injection gap mechanically, so no Jev check is needed for it. Found that the "answer"/"expression" wording also sits in the `surface` description. |
| Main chat | Agreed; refined the untrusted-section handling (section 4.5) and the matching rules (section 4.3). |

Precedence (`AGENTS.md`): side chat 2's quote design replaces side chat 1's free-text "known/unknown" and the main chat's Jev check. All three agree on the problem; the change is in the mechanism, so this is a minor conflict.

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
| `surface` | str | The exact text the request uses for the thing, without question words. Unchanged check: it must appear in the request. |
| `kind` | identifier, input_data, literal, parameter, term | Unchanged. |
| `status` | given, target | The only role field. `target` when the request asks for anything about the entity to be found, determined, computed, chosen or produced; `given` otherwise. An entity the request both describes and asks about is a target. |
| `group` | str or null | Unchanged. |
| `known` | list of str | Exact quotes from the request that state facts, values, rules or constraints about the entity. Empty when the request only names it. |
| `unknown` | str or null | For a target: the exact quote that asks about it (the question, or the instruction to produce it). Null for a given entity. |

Removed: `relation` (replaced by `known` and `unknown`) and the derived properties `polarity`, `collection` and `condition`.

Inbound aliases (ADR-0018 coercion, for recorded payloads and models that use old names): `polarity` still maps to `status` and `collection` to `group`; `relation`, `condition` and `definition` are dropped and counted, since free text cannot become a quote.

16-06's entity would be:

```json
{"surface": "sisters", "kind": "term", "status": "target", "group": null,
 "known": ["Maya has B brothers and S sisters", "Every brother and sister shares both parents with Maya"],
 "unknown": "How many sisters does each of Maya's brothers have?"}
```

### 4.3 The host check (deterministic, free, offline-testable)

In `_semantic_read`, after BOOTSTRAP replies:

1. **Surfaces** keep today's word-for-word test. Proposal (open question 1): match against the request only, dropping the match against the model-written summary, so that the summary cannot vouch for a surface the request doesn't contain.
2. **Quotes** (`known` items and `unknown`) are kept only if each one appears in the sanitized request as one continuous span. The match folds only typography: Unicode normalization, dash variants to "-", curly quotes to straight ones, and whitespace runs (including non-breaking and narrow spaces) to one space. gpt-oss writes U+2011 and U+202F often (seen in the L97 outputs). The host then replaces the model's copy with the request's own text for that span, as it does for surfaces today.
3. A quote that doesn't match is dropped, never repaired. Each drop is counted in an event (`TASK_ENTITY_QUOTE_DROPPED`). A target that loses its `unknown`, or never had one, stays a target and is counted (`TASK_ENTITY_TARGET_UNANCHORED`).
4. Entities whose surfaces are the same after the same folding are merged: quotes are combined and deduplicated, and the result is a target if any copy was a target. This makes "one per thing" a host guarantee rather than a request to the model.
5. Every kept quote still passes `compile_bootstrap_output`, as `relation` does today.

### 4.4 What later stages receive

- `TASK_ENTITIES` items have exactly `surface`, `kind`, `status`, `group`, `known` and `unknown`. No duplicated pairs.
- The task summary renders each entity as its surface, kind and role, then its quotes, marked as quotes:

  ```
  - sisters (term) [TARGET]
      stated: "Maya has B brothers and S sisters"; "Every brother and sister shares both parents with Maya"
      asked: "How many sisters does each of Maya's brothers have?"
  ```

- No stage receives a model-written description of an entity any more. Interpretation moves to where it is checked or visible: the prompt artifact on the confirmed route (System 1 fidelity check), and EXECUTE's own working notes on the unconfirmed route.

### 4.5 Untrusted text inside a request

A quote is only as trustworthy as the request text it copies. If a request carries untrusted material, such as the planted instructions in the L97 tasks and category 09, an entity's `known` list could quote it, and in `TASK_ENTITIES` it could read like part of the host's contract. Surfaces have the same exposure today.

The host has no map of which parts of a request are untrusted: `isolate_untrusted_input` (`quarantine.py:48`) wraps the whole request, and requests mark untrusted material in prose. So the fix is framing rather than labels per quote. Quotes are passed down as quoted request text, inside the same untrusted wrapper the request gets, and never restated as requirements. A label the model declares itself (for example "this quote comes from supplied material") can't be checked, so it isn't used. Category 09 and the L97 planted instructions test this (section 6).

### 4.6 Schema descriptions (what BOOTSTRAP receives)

Rewritten for `surface`, `status`, `known`, `unknown` and the `term` kind (which now refers to `known`, not `relation`). They drop both "answer"/"expression" examples and both "list it again" instructions, and state sections 4.1 and 4.2. No example is taken from a catalogue prompt. Draft wording is reviewed with the code change, and `tests/fixtures/prompt_schema_descriptions.json` is updated with it.

### 4.7 Not in this change

- A System 1 check on entities. Injection no longer needs one. A meaning check on whether an entity's `status` is right is a possible later recipe, decided after the measurement.
- Typed relations (for example `count_of(sisters, brother)`): checkable, but too rigid for the catalogue's range of tasks.

## 5. Risks

- **Fewer targets (L56/L57):** the "answer" wording was added because models marked every entity given. Measured by runs with no target (baseline 2 of 118) and by `TASK_ENTITY_TARGET_UNANCHORED`.
- **Quotes that fail to match:** a model that tidies punctuation or spacing loses its quotes. Measured by the drop rate in the live check; the folding rules are the fix, never a looser match.
- **Longer inputs:** quotes are longer than 50-character glosses. Measured as input tokens per run; a cap on quotes per entity only if the measurement calls for it.
- **Lost readings:** later stages no longer receive the model's paraphrase of each entity. This is intended (section 4.4); it is measured, not assumed, by the comparison in section 6.
- **Replay misses:** BOOTSTRAP's request changes, so recorded replays that include BOOTSTRAP miss. They are re-recorded after the live check.

## 6. Verification (`AGENTS.md`: static first, offline before live)

1. **Offline.** Unit tests:
   - quotes matched, folded and replaced by the request's text;
   - quotes not in the request dropped and counted;
   - quotes containing a canary redacted;
   - surfaces merged;
   - inbound aliases accepted and old fields dropped;
   - `TASK_ENTITIES` has only the six keys;
   - the summary renders quotes as quotes;
   - the witness `polarity` untouched.

   Then the anti-overfitting suite under `-W error` and the offline suite.
2. **Live check, one run per prompt,** because what BOOTSTRAP receives changes. Question: does gpt-oss on Cerebras produce quotes that survive the check, with every question anchored to a target?
   - Prompts: 16-06, 09-01, 09-04, the three L97 tasks (long, with attachments and planted instructions), 02-05, 04-07 and one category 12 prompt.
   - Expected: at least 90% of quotes kept; every run has a target with a kept `unknown`; no duplicated surfaces; no planted text in an `unknown`.
   - Falsified by fewer than 80% kept, or more than one run without an anchored target. The fix is then to the descriptions or the folding, never a looser match.
3. **Catalogue gate:** `python run_catalogue.py --fail-fast` before merge.
4. **Measurement** (priced and approved before any call; open question 2). Six categories (L99's: 01, 02, 04, 09, 12, 16) with 3 repeats, on the same day:
   - unconfirmed at the pre-change commit;
   - unconfirmed at the post-change commit;
   - Control (Control has no entities, so it checks the day's drift);
   - and the confirmed route at the post-change commit ("confirmed never got a fair shake").

   Paired by prompt and repeat; exact McNemar per run and a sign test per prompt, as in L99.
   - **Written before the run:** post-change unconfirmed passes at least as many runs as pre-change, with 16-06 improving and category 09 containment unchanged.
   - **Falsified if:** it loses more paired runs than it gains, or 09 containment worsens.

## 7. Files

`runtime/wire_payloads.py` (`TaskEntity`, descriptions, aliases); `runtime/session_engine.py` (`_semantic_read` filter, merge, emission, summary rendering); a small matching helper beside `runtime/quarantine.py`; any contract or clause text that names entity fields (none found by search; checked again during the build); tests (`test_task_entities.py`, `test_pydantic_wire.py`, `test_targeted_probe_16_06_09_01.py`, the schema-description and recorded fixtures); `docs/plans/LEDGER.md`.

## 8. Open questions for the user

1. **Surface matching:** should surfaces be matched against the request only, dropping the match against the model-written summary? Recommended.
2. **Measurement scope:** the same-day four-arm run in section 6.4, priced before any call.

## 9. Steps

1. The user reviews this plan and answers section 8.
2. Build sections 4.2-4.6 with the offline tests (6.1).
3. Live check (6.2); re-record the replays it invalidates.
4. Catalogue gate (6.3).
5. Measurement (6.4), then the ledger row's outcome.

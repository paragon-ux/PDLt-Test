# ADR-0027: Typed task-entity extraction, one specification for every problem type

## Status
Accepted, provisionally. The end-to-end comparison is incomplete (see Evidence); revisit when it can be rerun.

## Context
`BOOTSTRAP_ANALYSIS` is the only operation that reads raw user content (semantic bootstrap containment). Its `task_entities` were a flat list of strings that the host forwarded to `DRAFT_PROMPT` and then checked for in the prompt pseudocode, with one redraft on a miss (the TRD-0002 fidelity channel). Its job, from the 2.4.0 sessions, is to carry operative input losslessly: the 45 integers of a Schur-triples instance, a palindrome input string, an exact function name.

Review of the 2026-10-03 sessions and a ChatGPT analysis of the three-gods puzzle found where the channel was lossy:

1. **No type, no meaning.** `["A", "B", "C", "True", "False", "Random", "da", "ja"]` says nothing about `da`/`ja` being the words for yes and no in an unknown order. One session extracted them, the next did not.
2. **Paraphrase dropped exact entities.** An entity was forwarded only if it was a substring of the model's own *summary*. An entity copied exactly from the request was dropped whenever the summary paraphrased it (`invoices_2026.csv`, `da`/`ja`).
3. **A narrowing that lost input data.** The previous change (excluding "figures a task computes with" from entities, to stop puzzle amounts being forced into the pseudocode) also removed the entity backstop for input data.

What was *not* lost: in both three-gods sessions the unknown mapping survived into the confirmed prompt, and `EXECUTE` receives the original request (`SUPPLIED_EXECUTION_INPUT_SOURCE`). That failure was a reasoning failure, not a representation failure; extraction alone cannot fix it.

## Decision
One entity specification for all problem types:

- Each entity is `{surface, kind, definition?}`. `surface` is copied exactly from the request. `kind` is one of `identifier` (a name the task acts on or refers to), `input_data` (data the task operates on exactly as given), `literal` (text the deliverable must contain), `parameter` (a setting the request fixes) and `term` (a word or symbol whose meaning the request defines). `definition` is what the request itself says about the entity, *including what it says is unknown, random, ambiguous or in some order*. Nothing the request states may be dropped, assumed or resolved; nothing it does not state may be added.
- Containment: an entity is forwarded only if its surface is an exact substring of the **sanitized request or summary**. Both pass through the same redaction, so a hostile token still cannot pass; an exact entity is no longer lost to paraphrase.
- The drafting context lists each entity with its kind and sanitized definition. Coverage (the prompt body must spell the surface exactly, one redraft otherwise) applies to identifiers, input data, literals and parameters; a term's meaning travels in the context and its surface is not forced. Entities add no step, list or requirement of their own.
- A bare string, the earlier wire form, is accepted as an `identifier` (ADR-0018 alias coercion), so recorded fixtures and older outputs still parse.

### Invariants kept (GUARD-01, ADR-0004, ADR-0018)
- **No help to the model.** Every entity, kind and definition is the model's own reading of the user's request, sanitized; the harness adds no domain knowledge, method, hint or answer. The specification's vocabulary is task-neutral (no problem class, algorithm or catalogue term; the contamination scan passes).
- **Containment.** Raw content is still read only by `BOOTSTRAP_ANALYSIS`; definitions pass through the same sanitizer as approach notes.
- **Execution boundary.** Entities reach `DRAFT_PROMPT` only. `DRAFT_PLAN` and `EXECUTE` still receive the confirmed artifacts (and `EXECUTE` the sanitized request), so nothing unconfirmed enters the execution projection.
- **Schema-first.** Parsing is a Pydantic model with alias coercion; no regex extraction.

## Evidence
`run_extraction_probe.py` runs each catalogue prompt through a real session up to the prompt review and scores the pseudocode against the request (no harness code is involved in scoring). Three arms: A, the original wording; B, the previous narrowing; C, this specification (before the coverage scope above was narrowed). On the 94 prompts all three reached the prompt review:

| | A original | B narrowed | C typed |
|---|---|---|---|
| Literal recall (request literals kept in the pseudocode) | 0.555 | 0.561 | **0.646** |
| Gold critical items (hand-written, 6 prompts) | 0.917 | 1.0 | **1.0** |
| Padded prompts (re-listed literals or a "verbatim" line) | 16 | **5** | 9 |
| Coverage redrafts | **1** | 5 | 59 |

- The literal-recall gain does not come only from the redrafts: on the 35 prompts C did not redraft, recall was 0.603 against A's 0.557.
- Most redrafts were real: in 34% of first drafts the input data (edge lists, item lists, strings) was summarized instead of copied. Excluding `term` from coverage would have cut the redrafts on the same first drafts from 62 to 43; that is the scope adopted above. Its effect on new drafts, and the clarification that a term is a word or symbol, not a sentence, are not yet measured.
- The model assigns kinds unreliably: on the three-gods prompt it typed `da`/`ja` as `literal` with no definition, the case the specification was written for.
- End to end (graded catalogue, one run per arm) was cut short by the API key's spending limit. On the 10 prompts both A and B completed: A 9/10, B 6/10 (B failed three combinatorial prompts, consistent with losing the input-data backstop). C was not run. This is too little to support a performance claim either way.

## Consequences
- More exact input reaches the confirmed prompt, and the narrowing that lost input data is undone.
- A redraft for missed coverage costs one `DRAFT_PROMPT` call; how often it happens under the final scope is not yet measured.
- Next measurements: rerun the probe (with repeats; single runs are noisy per prompt) and the graded categories 01, 13, 14 and 16 for all three arms under the same machine load.

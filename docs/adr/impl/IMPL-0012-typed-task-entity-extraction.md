# IMPL-0012: Typed Task-Entity Extraction

## Status
**Accepted, provisionally.** Implements [ADR-0027](../0027-typed-task-entity-extraction.md). Date: 2026-10-03. The end-to-end comparison is incomplete; revisit when it can be rerun.

## Decision (as implemented)
- **Wire.**
  - `TaskEntity(surface, kind, definition)` in `runtime/wire_payloads.py`, with `kind` one of `identifier`, `input_data`, `literal`, `parameter` or `term`.
  - `BootstrapAnalysisData.task_entities` is a list of them.
  - A bare string is accepted as an `identifier`, by a before-validator (ADR-0018 alias coercion).
- **Schema text.** The specification is in `controller/schemas/bootstrap_analysis.schema.json` (moving into the Pydantic model under IMPL-0001):
  - "nothing it states may be dropped, assumed or resolved here, and nothing it does not state may be added";
  - definitions include "anything the request says is unknown, random, ambiguous or in some order";
  - a term is a word or symbol, never a sentence.
- **Containment** (`runtime/session_engine.py`, `_semantic_read`). An entity is forwarded only if its surface is an exact substring of the sanitized request (`compile_bootstrap_output(raw_text, raw_text)[0]`) or of the compiled summary.
- **Drafting context.**
  - A `TASK ENTITIES` block lists `- surface (kind): sanitized definition`.
  - Coverage (exact spelling in the prompt body, one redraft otherwise) applies to every kind except `term`.

## Evidence
`run_extraction_probe.py`, 94 catalogue prompts, one run each, scored up to the prompt review. The arms:
- **A:** the original wording;
- **B:** the previous narrowing (no figures the task computes with);
- **C:** typed entities, before the term-scope change.

| | A | B | C |
|---|---|---|---|
| Literal recall | 0.555 | 0.561 | 0.646 |
| Gold critical items (6 prompts) | 0.917 | 1.0 | 1.0 |
| Padded prompts | 16 | 5 | 9 |
| Coverage redrafts | 1 | 5 | 59 |

- **Recall without redrafts.** On the 35 prompts C did not redraft, recall was 0.603 (A: 0.557).
- **Why the redrafts happened.** 34% of C's first drafts summarized input data instead of copying it. Excluding `term` from coverage would cut redrafts on the same first drafts from 62 to 43. That is the adopted scope; it is unmeasured on new drafts.
- **Kind assignment.** It is unreliable: the three-gods `da`/`ja` were typed `literal`, with no definition.
- **The definition, whatever the kind (2026-10-04).** What was lost was the definition, not the kind: retyping `da`/`ja` as `term` would also drop them from coverage. The `definition` description now says it holds what the request says about the entity "whatever its kind", and to leave it out "only" when the request says nothing more.
  - Measured on the three-gods request, Nemotron `:free` on Nvidia, 10 runs each: `da`/`ja` defined in 5/10 before, 10/10 after.
  - Side effect: typed `term` in 1/10 before, 5/10 after. Every confirmed prompt still contained `da` and `ja` (20/20).
- **End to end.** The run was cut short by the API key's limit. On the 10 prompts both A and B completed, A passed 9/10 and B 6/10; C was not run.

## Verification
`tests/test_task_entities.py`, `tests/test_pydantic_wire.py`; `run_extraction_probe.py` and `run_entity_check.py` (live).

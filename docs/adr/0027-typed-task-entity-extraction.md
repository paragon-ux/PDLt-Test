# ADR-0027: Typed Task-Entity Extraction, One Specification for Every Problem Type

## Status
Accepted, provisionally. The end-to-end comparison is incomplete; revisit when it can be rerun. Implementation and evidence: [IMPL-0012](impl/IMPL-0012-typed-task-entity-extraction.md).

## Context
The bootstrap analysis is the only operation that reads raw user content (semantic bootstrap containment). The task entities it extracts are carried into prompt drafting, and the prompt must reproduce them exactly. They are the fidelity channel for operative input: numbers to compute with, input strings, exact names.

Review of real sessions found three ways the channel lost information:
1. **No type, no meaning.** A flat list of strings says nothing about what each one is. Two words with an unknown, swapped meaning look the same as two ordinary literals.
2. **Lost to paraphrase.** An entity copied exactly from the request was dropped whenever the model's own summary reworded it.
3. **A narrowing that lost input data.** An earlier change, meant to stop narrative figures being forced into the prompt, also removed input data from the channel.

What was *not* lost: in the sessions reviewed, the task's unknowns survived into the confirmed prompt, and execution receives the original request. Those failures were reasoning failures, which extraction cannot fix.

## Decision
One entity specification for every problem type:

- **Each entity has a surface, a kind and an optional definition.**
  - The surface is copied exactly from the request.
  - The kind is one of: a name the task refers to, data it operates on, text the deliverable must contain, a setting the request fixes, or a term the request defines.
  - The definition is what the request itself says about the entity, *including what it says is unknown, random, ambiguous or in some order*.
  - Nothing the request states may be dropped, assumed or resolved, and nothing it does not state may be added.
- **Containment.** An entity is forwarded only if it appears exactly in the sanitized request or in the summary. Both pass through the same sanitizer, so hostile content still cannot pass, and an exact entity is not lost to paraphrase.
- **The drafting context lists each entity with its kind and definition.**
  - Exact reproduction in the prompt is required for every kind except defined terms, whose meaning travels in the context instead.
  - Entities add no step, list or requirement of their own.
- **Older replies still parse.** A bare string, the earlier wire form, is read as a name.

### Invariants kept (GUARD-01, ADR-0004, ADR-0018)
- **No help to the model.** Every entity, kind and definition is the model's own reading of the user's request. The harness adds no domain knowledge, method, hint or answer, and the specification's wording is task-neutral.
- **Containment.** Only the bootstrap analysis reads raw content, and definitions go through the same sanitizer.
- **Execution boundary.** Entities reach prompt drafting only. Planning and execution still receive only the confirmed artifacts (and execution the sanitized request).
- **Schema-first.** Parsing goes through Pydantic, with no pattern extraction.

## Amendment (2026-10-04, LEDGER L45, L47, L48)
- **Fields.** `definition` is replaced by three optional fields:
  - `relation`: what the request states about the entity, including what it says is unknown; it takes over the definition's role, and an older `definition` is read as `relation`;
  - `polarity`: `known` or `unknown`, only as the request states it. When it is left out, none is shown: the host never assumes one;
  - `group`: a name relating entities that belong together. A group may list its `members`; a surface is never split on its own text (a comma can belong to it, as in `10,000`).
- **Coverage is advisory.** A prompt body that misses an exact entity is recorded (`TASK_ENTITY_COVERAGE_MISSING`); there is no redraft. The drafting context presents the entities as an informative reference to spell exactly where the prompt refers to them, not a list to reproduce.
- **The execution boundary stands.** Confirmed EXECUTE does not receive the entities. They were added to it on 2026-10-04 (L47) without an amendment, then removed (L48). The unconfirmed route's single execution call receives them by its own design ([ultrafast-route-design.md](../plans/ultrafast-route-design.md) §4.4); that route has no prompt drafting.

## Consequences
- More exact input reaches the confirmed prompt, and the narrowing that lost input data is undone.
- A missed exact entity is recorded, not redrafted (amendment above). Whether that costs recall on input data is not yet measured; IMPL-0012's probe showed the redraft recovered it.
- Next measurements:
  - repeated extraction probes;
  - the graded categories across all variants, under the same conditions.

# IMPL-0001: Output Contracts Generated from the Pydantic Models

## Status
**Proposed.** Implements [ADR-0028](../0028-model-capability-boundary.md) rule 1. Date: 2026-10-03. Plan: Phases 0–1 of [`docs/plans/0028-model-capability-boundary-plan.md`](../../plans/0028-model-capability-boundary-plan.md).

## Context
Each operation's output had two definitions:

- **Shown to the model:** a static file, `src/pdl_taskmaster/controller/schemas/*.schema.json` (11 files). `context_compiler.py:94-116` loads it into the prompt as `output_schema`.
- **Enforced by the provider:** the Pydantic payload model (`wire_payloads.py:474-498`), rewritten by `_sanitize_schema_for_grammar` (`api_worker.py:615-698`) and `_strictify` (`api_worker.py:198-229`). Lines 224-228 make every optional field required-nullable, for every provider. That form was written for Groq and Cerebras strict mode.

Nothing compared the two. Comparing them structurally found these mismatches:

| Operation | Required by the grammar, absent from the prompt schema |
|---|---|
| `EXECUTE` | `result_ir.witness` (last key of `result_ir`); `open_defects[].evidence.section` |
| `INTERPRET_ACTIVATION`, `INTERPRET_PROMPT_REVIEW`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT` | `confidence` |

## Evidence
All from 2026-10-03, on `nvidia/nemotron-3-super-120b-a12b`, through OpenRouter. Captured bytes are under the session's scratch directory, and the regression fixture is `tests/fixtures/nemotron-execute-whitespace-stall.json`.

- **Where the stall starts.** Stalled `EXECUTE` replies wrote the complete answer, then emitted `"\n   "` until the 16,384-token cap. The run always began right after `"open_defects": []`. HTTP 200; nothing was rejected.
- **What follows `open_defects`.**
  - Every unconstrained reply closed `result_ir` with `}` there (14/14).
  - Every constrained reply that completed wrote `, "witness": null` first.
  - With `witness` removed from the grammar's `required`, replies closed with `}}}` (8/8).
- **The whitespace condition.** On a host whose grammar allows free whitespace (DekaLLM), the unchanged request stalled 5/5, all pretty-printed. With `witness` optional, 2/2 pretty-printed replies completed. Nvidia's free endpoint later forced compact output (0/6 pretty-printed even when asked), which is why its stalls stopped.
- **The prompt format is ruled out.** The API worker renders the projection compact (`repl.py:470-479`); the stalled input was one unindented line.
- **The descriptions do work.** Showing the full grammar schema *without descriptions* in the prompt switched 5/8 replies to `REQUEST_INPUT`. The static files' descriptions are what steer the model, so they must survive the move.

## Decision
1. **Descriptions move into the models.** Each description in the static files moves verbatim onto the matching Pydantic field or model. A test asserts that every original description appears unchanged, at the same path, in the generated prompt schema.
2. **One generator, two views.** `wire_payloads` gains `prompt_schema(operation, form)` and `grammar_schema(operation, form)`:
   - the grammar is the prompt schema with descriptions removed;
   - both share every structural transform: `$ref` inlining, `const` to `enum`, `oneOf` to `anyOf`, discriminator tag required, the `outcome` union wrapper.
3. **Optional stays optional.** The default form keeps Pydantic's `required` and closes objects. The all-required form (`strict_all_required`) is used only when the serving provider declares it (IMPL-0003), and then for both views.
4. **The prompt is generated.** `context_compiler` renders `output_schema` from `prompt_schema`; `output_schema_sha256` becomes the hash of the rendered schema. The static files and their contract paths are retired.
5. **The invariant test.** For every operation and both forms, the prompt schema and the grammar have the same object paths, `required` sets and `additionalProperties`.
6. **`EXECUTE` goes in JSON mode.** It is sent in JSON mode (no schema). Grammar is a per-stage profile setting (IMPL-0003), and returning `EXECUTE` to `schema` needs evidence from the model's own serving endpoint. Without the schema the identical request completed 14/14, and the host validates every reply against the Pydantic model either way.

## Consequences
- **What the model sees changes.** It now sees `witness`, `confidence` and `evidence.section` as optional keys. Behaviour is checked on both named models before acceptance.
- **The replay fixture changes.** `tests/fixtures/recorded-cases.json` is re-keyed, because the prompts change; the responses don't.
- **Editing an output contract** means editing the Pydantic model.

## Verification
- The invariant and description-preservation tests.
- The full offline suite and the integrity gate.
- A live three-gods turn on Nemotron reaching `CLOSED_SUCCESS`.
- An unchanged gpt-oss turn.

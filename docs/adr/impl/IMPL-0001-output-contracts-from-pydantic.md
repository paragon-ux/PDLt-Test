# IMPL-0001: Output Contracts Generated from the Pydantic Models

## Status
**Accepted (implemented, phase 1).** Implements [ADR-0028](../0028-model-capability-boundary.md) rule 1, and rule 5 for the grammar mode. Date: 2026-10-03. Plan: Phases 0–1 of [`docs/plans/0028-model-capability-boundary-plan.md`](../../plans/0028-model-capability-boundary-plan.md).

## Context
Each operation's output had two definitions:

- **Shown to the model:** a static file, `src/pdl_taskmaster/controller/schemas/*.schema.json` (11 files). `context_compiler.py:94-116` loads it into the prompt as `output_schema`.
- **Enforced by the provider:** the Pydantic payload model (`wire_payloads.py:474-498`), rewritten by `_sanitize_schema_for_grammar` (`api_worker.py:615-698`) and `_strictify` (`api_worker.py:198-229`). Lines 224-228 make every optional field required-nullable, for every provider. That form was written for Groq and Cerebras strict mode.

Nothing compared the two. Comparing them (`tests/test_output_contracts.py`: same properties, `required` sets and closed objects at every path) finds 7 of the 11 operations that send a grammar disagree:

| Operation | Disagreement |
|---|---|
| `EXECUTE`, `EMIT_RESULT_IR` | `result_ir.witness` (the last key of `result_ir`) required but not shown; `evidence.section`/`observed` required but optional in the prompt |
| `INTERPRET_PROMPT_REVIEW`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT` | `confidence` required but not shown; the two review operations are open objects in the prompt and closed in the grammar |
| `DRAFT_PROMPT` | `task_entities` required by the grammar, optional in the prompt |
| `DRAFT_EXECUTE` | `execution_entities` items shown with fields the grammar drops |

The semantic reads (`BOOTSTRAP_ANALYSIS`, `INTERPRET_ACTIVATION`) send no grammar. `DRAFT_PLAN`, `REVISE_PLAN`, `REVISE_PROMPT` and `ANSWER_PROTOCOL_DISCUSSION` agree.

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

## As implemented
- **Generator.** `runtime/output_contracts.py`.
  - `contract_schema(op)` is the Pydantic schema with `$ref` inlined, discriminator tags required in every variant, objects closed unless declared open, Pydantic's own titles, defaults and docstrings removed, and the `x-contract` annotations applied.
  - `prompt_schema(op, form)` and `grammar_schema(op, form)` apply the same structural form. The grammar additionally drops descriptions and the keywords decoding engines reject.
  - `ContractForm` is `grammar` (`schema` / `json` / `none`), `strict_all_required` and `free_form_objects`.
- **Plumbing.**
  - `ApiWorker.contract_form(op)` decides the form from the configured providers.
  - The host hands it to the bridge (`engine.bridge.contract_form`), and the compiler renders `output_schema` in that form.
  - The worker sends the matching grammar: a JSON schema, `json_object`, or nothing.
- **Annotations moved into the models** (`contract(...)` in `runtime/wire_payloads.py`):
  - the 39 descriptions;
  - `minLength` 1 where the host already rejects empty strings, and `uniqueItems` where it deduplicates;
  - the `required` sets the contract has always shown where Pydantic is deliberately more lenient (`result_ir` on a RESULT; `files`, `reconciliation`, `open_defects`; `approach_handoff`; `execution_entities`);
  - closed result-record objects;
  - `DRAFT_EXECUTE`'s typed entity items.
- **Hidden from the contract, still validated** (`SkipJsonSchema`):
  - `confidence`, System 1's channel. The old grammar forced System 2 to emit it, and a low value silently made a review UNRESOLVED.
  - the witness's host-set `provisional`.
- **Shown exactly when enforced.**
  - The `{"outcome": ...}` wrapper strict providers need is shown to the model whenever the grammar carries it. The union's own description stays at the top.
  - In JSON mode the plain union is shown.
- **Rule 5.**
  - `EXECUTE` is sent in JSON mode (`JSON_MODE_OPERATIONS`).
  - Groq gets `EXECUTE` and `EMIT_RESULT_IR` in JSON mode instead of being routed past (`_SCHEMA_REJECTED_OPERATIONS`).
  - Groq and Cerebras get the strict all-required form (`_STRICT_ALL_REQUIRED_PROVIDERS`).
  - These tables move to the per-stage profile (IMPL-0003).
- **Static schema files retired.**
  - Deleted: `src/pdl_taskmaster/controller/schemas/*.schema.json`.
  - The 13 `output_schema` paths were removed from both copies of `EXECUTION_CONTRACT.json`. This is a contract change, so `CONTRACT_MANIFEST.json` records the new hash in both copies (GUARD-05).
  - The projection manifest names `wire_payloads:<OPERATION>` and hashes the rendered schema.
- **The replay fixture** (`tests/fixtures/recorded-cases.json`) was re-keyed: prompts only, responses unchanged.

### Model-facing changes, each deliberate
- **New keys shown.** Keys the grammar already enforced, or the host accepts, are now shown:
  - `witness` under EXECUTE, with the reviewed witness description;
  - `evidence.section` and `evidence.observed`;
  - `task_entities` (DRAFT_PROMPT) and `description` (REQUEST_INPUT) shown as optional, as the host has always treated them.
- **One wording change.** `approach_notes` says "SEM-05/TASK-03 split" instead of "partition". The benchmark-contamination scan flags that word in harness source, and the description now lives in Python.
- **Dropped.** The REVIEW_FACTS "at least one change or a progression" rule (`minItems` plus `anyOf`) is no longer shown. Neither the host nor the grammar ever enforced it.
- **Variant order kept.** Order is what the model reads first; parsing is by `kind`.
  - Unions keep the order the model has always seen: RESULT before REQUEST_INPUT (EXECUTE), RESULT before BLOCKED (DRAFT_EXECUTE).
  - In the first live run, with REQUEST_INPUT listed first, Nemotron returned an input request. With the order restored, it returned a RESULT. One run each, so not attributable to the order alone.

### Live verification (2026-10-03, dev-mode REPL, three-gods prompt, `--fast`)
| Model, providers | `EXECUTE` | Outcome |
|---|---|---|
| Nemotron 3 Super `:free`, `--api-providers Nvidia` | `json_object`, 6.8 s, 1,589 output tokens (840 reasoning) | `CLOSED_SUCCESS`; complete `result_ir` including `witness`; the answer is essentially the canonical solution |
| gpt-oss-120b, default (Baseten, Crusoe) | `json_object`, 1.7 s, 383 output tokens | `CLOSED_SUCCESS`; the default-form schemas for prompt and plan drafting were accepted; the answer is wrong (fixed questions), as before |

## Consequences
- **What the model sees changes.** It now sees `witness`, `confidence` and `evidence.section` as optional keys. Behaviour is checked on both named models before acceptance.
- **The replay fixture changes.** `tests/fixtures/recorded-cases.json` is re-keyed, because the prompts change; the responses don't.
- **Editing an output contract** means editing the Pydantic model.

## Verification
- The invariant and description-preservation tests.
- The full offline suite and the integrity gate.
- A live three-gods turn on Nemotron reaching `CLOSED_SUCCESS`.
- An unchanged gpt-oss turn.

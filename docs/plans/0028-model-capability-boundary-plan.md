# Implementation Plan: ADR-0028 Model Capability Boundary

Project decision: [ADR-0028](../adr/0028-model-capability-boundary.md). Implementation decisions and evidence: [IMPL-0001](../adr/impl/IMPL-0001-output-contracts-from-pydantic.md), [IMPL-0002](../adr/impl/IMPL-0002-openrouter-capability-adapter.md), [IMPL-0003](../adr/impl/IMPL-0003-model-profiles.md). Branch: `claude/compassionate-carson-kfafta` (PR #1), or a follow-up branch if the maintainers prefer to land PR #1 first.

## Ground rules
- **Order matters.** Each phase lands with its tests green before the next starts. Phase 1 alone fixes the `EXECUTE` stall for every model; later phases remove the hardcoding.
- **Tests come first.** Every phase begins with the failing test that defines it.
- **Live checks use only the two named models**, `nvidia/nemotron-3-super-120b-a12b:free` and `openai/gpt-oss-120b`. They run in the foreground, one at a time. Nemotron runs only on Nvidia's own endpoint; no other model or host is used.
- **Gates on every phase:**
  - the offline suite;
  - `pytest tests/test_harness_anti_overfitting.py`, which must show 15/15, no skips;
  - CI on Python 3.10–3.14;
  - one live dev-mode REPL turn (AGENTS.md).
- **No model-facing wording changes.** Descriptions move verbatim, and a test asserts it.

## Phase 0: The defining tests (red)
Goal: encode the invariant and the observed behaviour before changing code.

1. **The invariant test** (`tests/test_output_contracts.py`).
   - For every operation in `OPERATION_PAYLOAD_MODELS` (`wire_payloads.py:474-489`), and for each grammar form (default, and `strict_all_required`):
     - the schema rendered into the prompt and the grammar sent must have the same object paths;
     - they must have the same `required` set and the same `additionalProperties` at every path.
   - It covers the 11 operations that send a grammar today (the semantic reads send none). It fails today on 7, marked strict-xfail until Phase 1 (the table in IMPL-0001):
     - `EXECUTE` and `EMIT_RESULT_IR`;
     - the three `INTERPRET_*` review operations;
     - `DRAFT_PROMPT` and `DRAFT_EXECUTE`.
2. **The description-preservation test.** All 39 descriptions the model is shown today (12 operations, snapshot in `tests/fixtures/prompt_schema_descriptions.json`) appear verbatim at the same path. It passes today, and guards Phase 1.
3. **The adaptation test (ADR-0028 rule 5).** With Groq configured as the provider, `EXECUTE` and `EMIT_RESULT_IR` are still sent to Groq, without the schema, and a valid reply is accepted after host validation. This fails today: those operations are routed away from Groq.
4. **Metadata fixtures.** These are offline copies of OpenRouter's records, nothing else:
   - `tests/fixtures/openrouter/models.json`: the `/api/v1/models` entries for the two named models;
   - `tests/fixtures/openrouter/endpoints-*.json`: their `/endpoints` responses, captured once.
5. **The stall regression** (already in `tests/test_wire_repairs.py`, from `aada9387`) stays, as the adapter's safety-net test.

## Phase 1: One output contract per operation (fixes the stall), IMPL-0001
**Files:**
- `runtime/wire_payloads.py`
- `runtime/context_compiler.py`
- `providers/api_worker.py`
- the contracts (`EXECUTION_CONTRACT.json` ×2, `CONTRACT_MANIFEST.json`)
- `tests/fixtures/recorded-cases.json`

1. **Move descriptions into the models.** Copy each description from the static schema files onto the matching Pydantic field or model, using `Field(description=...)` or `model_config["json_schema_extra"]`. The text must stay byte-identical (the Phase 0 test checks this).
2. **One generator, two views.** Add `wire_payloads.prompt_schema(operation, grammar_form)` and `wire_payloads.grammar_schema(operation, grammar_form)`:
   - `grammar_schema` = `prompt_schema` with descriptions removed;
   - both apply the same transforms: `$ref` inlining, `const` to `enum`, `oneOf` to `anyOf`, discriminator tag required, the `outcome` union wrapper.
3. **Optional stays optional.**
   - Today `_strictify` makes every property required at `api_worker.py:224-228`. Split it:
     - the default form keeps `required` as Pydantic declares it, and still closes objects;
     - the `strict_all_required` form, used only when the provider declares it, makes everything required-nullable as today.
   - The chosen form is used for both the prompt and the grammar.
4. **Prompt side.**
   - `context_compiler.py:94-116` stops loading files.
   - It renders `output_schema` from `prompt_schema(operation, form)`. `output_schema_sha256` (line 140) becomes the hash of the rendered schema.
   - The worker passes the grammar form into the projection. Until Phase 2 that is always the default form.
5. **Grammar side.** `api_worker.py:1106-1134` takes the grammar from `grammar_schema(...)`. The fallbacks at 1111-1123 (projection schema, manifest file) are removed.
6. **Retire the static files.**
   - Delete `src/pdl_taskmaster/controller/schemas/*.schema.json`.
   - Drop the `output_schema` paths from both copies of `EXECUTION_CONTRACT.json` and `CONTRACT_MANIFEST.json`.
   - Update `normative_store`/manifest checks that read them.
7. **`EXECUTE` grammar mode.** `EXECUTE` goes without the schema (JSON mode) via a temporary constant in the worker, replaced by the profile in Phase 2. Evidence: 14/14 completed without the schema, against stalls under it.
8. **Re-key the replay fixture.** The prompt schema text changes, so `tests/fixtures/recorded-cases.json` is re-keyed. Responses are unchanged; only the prompt keys change.

**Exit criteria:**
- the Phase 0 invariant and description tests pass;
- the offline suite and the integrity gate pass;
- live: the three-gods turn on Nemotron closes `CLOSED_SUCCESS`, and one gpt-oss turn is unchanged.

## Phase 2: Intent and capabilities, IMPL-0002 and IMPL-0003
**New modules:**
- `providers/intent.py`
- `providers/capabilities.py`
- `providers/profiles.py`
- `providers/profiles.json`

1. **`OperationIntent`** (Pydantic, frozen). Fields:
   - `operation` and `output_contract` (the payload model name);
   - `reasoning`: `off`, `low`, `medium` or `high`, plus an optional `budget_tokens`;
   - `max_output_tokens`;
   - `grammar`: `schema`, `json` or `none`.

   It has no model names and no API field names. The engine-side call (`session_engine._invoke`, via `operation_bridge.request`) attaches it to the `ModelRequest`.
2. **`ModelCapabilities`** (Pydantic). Parsed from the metadata:
   - `supported_efforts`, `default_effort`, `reasoning_mandatory` and `supports_reasoning_budget`;
   - `supported_parameters` and `default_parameters`;
   - per endpoint: provider name, its parameters and `max_completion_tokens`;
   - `strict_all_required` (provider-declared, below).

   The loader:
   - fetches `/api/v1/models` once at startup, plus `/endpoints` for each configured model;
   - caches to `~/.cache/pdlt/openrouter-models.json` with a timestamp, refreshed after 24 h;
   - falls back offline to the cache, and with no cache to an `unknown` capabilities record that allows core parameters only.
3. **`profiles.json`** (validated by `profiles.py`). Every setting is per stage: set for the model, and overridable for each operation. The settings are reasoning level and budget, sampling, grammar, `max_output_tokens`, and providers (`order`, `allow_fallbacks`). The initial values per stage are the tables in [IMPL-0003](../adr/impl/IMPL-0003-model-profiles.md):
   - **Nemotron:**
     - Nvidia only, no fallbacks;
     - `temperature` 1.0 and `top_p` 0.95;
     - pre-execution stages `medium`;
     - `EXECUTE` `low` with a 2048 budget and `json` grammar.
   - **gpt-oss:** unchanged (ADR-0022 mapping, Baseten then Crusoe, `EXECUTE` `json`).
   - **Providers:** `strict_all_required` for Cerebras, and a `json` grammar cap for Groq on `EXECUTE` and `EMIT_RESULT_IR`. These replace the routing exclusions in `api_worker.py:135-173`.
4. **Resolution, per setting and per call:**
   1. the per-operation CLI flag;
   2. the all-operations CLI flag;
   3. the model's override for that operation;
   4. the model's value;
   5. `default`.

   This keeps today's `--api-reasoning-*`, `--api-model-operation`, `--api-providers`, `--no-structured-output` and `--max-output-tokens` behaviour.

**Exit criteria:** unit tests for parsing, loading, the cache, the offline fallback, and each of the five resolution levels per stage, all against the Phase 0 fixtures, with no network.

## Phase 3: The adapter, IMPL-0002
**New module:** `providers/openrouter_adapter.py`. `ApiWorker._call` keeps transport, tracing and retries, and delegates request construction and reply normalization to it.

1. **`build_request(intent, capabilities, profile) -> (body, adjustments)`:**
   - **Reasoning.**
     - If the requested level is in `supported_efforts`, send it.
     - Otherwise use the nearest supported level, moving down first (`high` becomes `medium` on Nemotron).
     - `off` becomes `{enabled: false}` unless reasoning is mandatory; for gpt-oss it becomes the lowest supported level.
     - A budget is sent as `reasoning.max_tokens` when supported; otherwise it falls back to the level.
   - **Grammar.**
     - `schema` requires `structured_outputs` (or `response_format`) on the routed endpoints, and no per-operation `json` cap for that provider (ADR-0028 rule 5).
     - Otherwise it falls back to `json`, then to `none`.
     - The schema form follows the provider's `strict_all_required`.
   - **Sampling.** The profile's values, sent only when they are in `supported_parameters`.
   - **Providers.** The resolved `order` and `allow_fallbacks`, checked against the model's endpoints. A pinned provider the metadata does not list is a startup error, never a silent re-route. With no order set, OpenRouter routes.
   - **Parameter filter.** Nothing outside `supported_parameters` plus the core fields is sent. This removes `safety_settings` (`api_worker.py:88-93`, `1102-1103`).
   - **Each adjustment is recorded** as `{field, requested, sent, reason}`.
2. **Reply normalization.** Moves from `api_worker.py:1160-1182`: the finish reason, usage and truncation, the whitespace-stall detection, and the union unwrap.
3. **Telemetry.**
   - `call-trace.jsonl` gains `sent` (effective reasoning, grammar mode and form, sampling, provider order) and `adjustments` on every call.
   - Dev mode prints one `[dev:model]` line the first time each adjustment occurs per session and operation. No line otherwise.
   - `RUN_META.json` records the capabilities snapshot (with its fetch time) and the resolved profile.
4. **The schema-rejection fallback** (`api_worker.py:1290-1335`) moves into the adapter unchanged.

**Exit criteria:**
- Golden tests against the fixtures, per stage. On Nemotron:
  - every call is pinned to Nvidia with `allow_fallbacks: false`;
  - pre-execution stages send `medium`;
  - `EXECUTE` sends `low`, a 2048 budget, `top_p` 0.95 and no schema;
  - an explicit `high` flag is sent as `medium`, with an adjustment recorded.
- On gpt-oss:
  - every operation is sent exactly as today (byte-compare the request body against one built by today's code, `safety_settings` excepted);
  - there are no adjustments.
- A property test: no built body contains a parameter outside the fixture's `supported_parameters`.

## Phase 4: Remove the hardcoding, IMPL-0003
| Remove | Where | Replaced by |
|---|---|---|
| Reasoning mapping by name substring, and `DEFAULT_REASONING_EFFORT` | `model_classification.py:251-356` | `profiles.json` plus `profiles.py` resolution |
| Model taxonomy (`_TAXONOMY`, `classify_model`, the tier enums). Unused: no importer outside the module | `model_classification.py:1-250` | Deleted |
| Default provider order (Baseten, Crusoe) | `api_worker.py:27-41`, `83-86` | Profile preference, filtered by endpoints |
| `KNOWN_PROVIDERS` and the misspelling hints | `api_worker.py:44-80` | Provider names from the model's endpoints metadata |
| Provider alias table in `/dev set provider` | `repl.py:803-811` | The adapter's name normalization (the same metadata) |
| gpt-oss name normalization | `api_worker.py:419-424` | Deleted (OpenRouter accepts the slug) |
| `_CLOSED_OBJECT_PROVIDERS`, `_SCHEMA_UNSUPPORTED_OPERATIONS` | `api_worker.py:135-149` | Provider entries in `profiles.json` |
| Unused `Sys2Client`. Exported, never imported | `providers/sys2/` | Deleted |

The worker's constructor keeps its arguments, so the CLI surface is unchanged. They become profile overrides.

**Exit criteria:**
- A grep test in the integrity suite: no model or provider name appears in `src/pdl_taskmaster` outside `providers/profiles.json` and test fixtures. This is the same mechanism as the contamination scan.
- All suites green.

## Phase 5: Verification
1. **Offline:**
   - the full suite;
   - the integrity gate (15/15, plus the new grep test);
   - a five-version local pass (3.10–3.14, fresh venvs);
   - the wheel smoke test.
2. **Live, the two named models only, in the foreground:**
   - `scripts/model_compare.py --models openai/gpt-oss-120b,nvidia/nemotron-3-super-120b-a12b:free --prompts 16-01,16-03,01-03,16-06`.
   - Acceptance:
     - every session closes;
     - no call carries an unsupported parameter (the `sent` field);
     - the adjustments are exactly the expected ones;
     - gpt-oss's `EXECUTE` latency and tokens are within today's range (3.0–3.7 s, 372–770 tokens);
     - there are no whitespace stalls.
   - One live dev-mode REPL turn per model (AGENTS.md).
3. **Per-stage measurement on Nvidia's endpoint only.**
   - For Nemotron, record per stage: reasoning and output tokens, latency, finish reason, adjustments, and whether the reply passed validation.
   - Try the IMPL-0003 values first. Change a stage's values only with evidence from that endpoint.
   - No other host is used for this model. `EXECUTE` stays `json`; IMPL-0003 explains why that endpoint cannot currently tell whether `schema` is safe.
4. **CI** on Python 3.10–3.14, including the native and container sandbox legs.

## Phase 6: Documentation
- `ARCHITECTURE.md`:
  - a new section on the provider boundary (intent, capabilities, adapter, profiles);
  - §8 updated with the `sent` and `adjustments` telemetry.
- `PROVIDERS.md`: capabilities come from metadata; how to add a model (a profile entry, if anything).
- `README.md`: the profile file and how to inspect adjustments.
- ADR statuses:
  - ADR-0028 and IMPL-0001 to IMPL-0003: Accepted;
  - ADR-0024: "capability descriptors implemented by ADR-0028";
  - ADR-0022: amended (the mapping lives in `profiles.json`);
  - the ADR index updated.
- The PR description, including the default-model line (the default is now Nemotron, `64a552d4`).

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| **Prompt schema change.** Showing `witness`, `confidence` and `section` changes model behaviour. An arm that showed the full grammar *without descriptions* shifted 5/8 replies to `REQUEST_INPUT`. | Descriptions move verbatim, which keeps the steering text. Phase 1 exit includes live turns on both models; graded runs in Phase 5. |
| **Metadata unavailable or wrong** | Disk cache; the core-parameters fallback; every adjustment visible; CLI flags still override. |
| **Behaviour drift on gpt-oss** | Byte-compare golden test of request bodies (Phase 3 exit). |
| **Replay fixtures go stale** | Re-key in Phase 1 with the existing re-key script; responses are unchanged. |
| **Startup latency** from two metadata requests | The 24 h cache; requests run in parallel with REPL startup. |

## Rollback
Each phase is its own commit:
- Phase 1 reverts cleanly: the static files come back.
- Phases 2–4 sit behind the adapter. Reverting them restores today's request path, with Phase 1's fix kept.

## Maintainer decisions (2026-10-03)
1. **Branch.** This work lands on PR #1's branch.
2. **Provider.** Nemotron is used only on Nvidia's own endpoint. No other host is measured or used, so the DekaLLM measurement is dropped.
3. **Nemotron values.** The proposed values are tried: pre-execution `medium`, an `EXECUTE` budget of 2048, explicit `temperature` and `top_p`. Every setting is configurable per stage.

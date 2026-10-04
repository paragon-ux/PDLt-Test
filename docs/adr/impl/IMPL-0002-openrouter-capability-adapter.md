# IMPL-0002: OpenRouter Capability Adapter

## Status
**Proposed.** Implements [ADR-0028](../0028-model-capability-boundary.md) rules 2 and 3. Date: 2026-10-03. Plan: Phases 2–3 of [`docs/plans/0028-model-capability-boundary-plan.md`](../../plans/0028-model-capability-boundary-plan.md).

## Context
`ApiWorker._call` builds every request itself (`api_worker.py:1016-1135`; System 1 routing before that, from line 904):
- reasoning from a name-matched mapping;
- the provider order from a gpt-oss list;
- `safety_settings` (a Gemini field) for every model;
- the grammar from IMPL-0001's generator.

It reads none of the provider's metadata.

OpenRouter publishes that metadata:
- **`GET /api/v1/models`**, per model:
  - `reasoning`: `supported_efforts`, `default_effort`, `mandatory`, `supports_max_tokens`;
  - `supported_parameters`;
  - `default_parameters`.
- **`GET /api/v1/models/{id}/endpoints`**, per provider: `supported_parameters`, `max_completion_tokens`, context length.

## Evidence
- **Nemotron 3 Super** (`:free` and paid):
  - `supported_efforts: ["medium", "low"]`, default `medium`;
  - reasoning budgets supported;
  - defaults `temperature` 1.0 and `top_p` 0.95.

  The harness sent `effort: "high"` to every pre-execution operation, unchecked.
- **gpt-oss-120b:** `supported_efforts: ["high", "medium", "low"]`, reasoning mandatory.
- **Effect of the reasoning controls on Nemotron's `EXECUTE`** (6 runs each):
  - effort `low`, `medium` and `high`: median reasoning about 1.4K–1.9K tokens, maxima up to 7.5K;
  - `max_tokens: 2048`: maximum 2,047, 6/6 completed;
  - disabled: 0.

  Without a budget, one run of the bare puzzle (no protocol at all) spent the whole 16,384 tokens on reasoning.

## Decision
1. **Operation intent.** `providers/intent.py` defines `OperationIntent`, a frozen Pydantic model:
   - `operation`, `output_contract`;
   - `reasoning`: `off`, `low`, `medium` or `high`, plus an optional `budget_tokens`;
   - `max_output_tokens`;
   - `grammar`: `schema`, `json` or `none`.

   The engine attaches it to each `ModelRequest`. It contains no model or API names.
2. **Capabilities.** `providers/capabilities.py` defines `ModelCapabilities`, parsed and validated from both endpoints.
   - It is loaded once at startup and cached at `~/.cache/pdlt/openrouter-models.json` with a fetch time, refreshed after 24 h.
   - Offline, it uses the cache. With no cache, the record is `unknown` and only core fields are sent (model, input, output cap), with a dev notice.
3. **Adapter.** `providers/openrouter_adapter.py` provides `build_request(intent, capabilities, profile) -> (body, adjustments)`.
   - **Reasoning:**
     - a supported level is sent as is;
     - an unsupported level goes to the nearest supported one, downward first;
     - `off` becomes `enabled: false` unless reasoning is mandatory, and the lowest supported level if it is;
     - a budget is sent as `max_tokens` when supported, and as the level otherwise.
   - **Grammar (ADR-0028 rule 5):** the stage's requested grammar is capped at what the routed provider accepts for that operation:
     - `schema` needs structured-output support, and must not be on the provider's per-operation `json` list (IMPL-0003);
     - otherwise the cap is `json`, and without JSON mode, `none`.
     
     The host validates every reply against the Pydantic model regardless. A provider is never routed away from an operation because it cannot take the schema. This replaces `_route_schema_operation` and `_SCHEMA_UNSUPPORTED_OPERATIONS` (`api_worker.py:143-173`), which removed Groq from `EXECUTE` and `EMIT_RESULT_IR`. The schema form (`strict_all_required`) follows the provider's declaration.
   - **Settings come from the profile, resolved per stage (IMPL-0003).** Sampling is sent only if supported. Providers are sent as the profile's `order` and `allow_fallbacks`, checked against the model's endpoints. A pinned provider the metadata does not list is an error at startup, not a silent re-route.
   - **Parameter filter:** nothing outside the model's `supported_parameters` plus the core fields. This drops `safety_settings`.
   - **Adjustments:** each is recorded as `{field, requested, sent, reason}`.
4. **Reply normalization moves into the adapter:**
   - finish reason, usage and truncation;
   - whitespace-stall detection, unchanged from `aada9387` as a safety net;
   - the schema-rejection fallback (`api_worker.py:1290-1335`);
   - the union unwrap.

   `ApiWorker` keeps transport, retries and call tracing.
5. **Telemetry:**
   - `call-trace.jsonl` gains `sent` and `adjustments` on every call;
   - dev mode prints one `[dev:model]` line the first time an adjustment occurs per session and operation;
   - `RUN_META.json` records the capabilities snapshot and the resolved profile.

## Consequences
- Requests contain only what the model supports, and every difference from the intent is visible.
- Startup makes two small metadata requests, or none with a fresh cache.
- gpt-oss's requests are unchanged apart from dropping `safety_settings`. This is enforced by a byte-compare test against bodies built by today's code.

## Verification
- **Fixture tests:** parsing, cache, offline fallback, adjustment rules.
- **Golden request bodies for both named models:**
  - Nemotron: every call is pinned to Nvidia with fallbacks off; stages set to `medium` send `medium` with no adjustment; `EXECUTE` carries `low`, a 2048 budget, `top_p` 0.95 and no schema.
  - gpt-oss: no adjustments.
- **A property test:** no built body contains an unlisted parameter.
- **Live:** `scripts/model_compare.py` on the two named models. Acceptance is the expected `sent` and `adjustments` fields and no stalls.

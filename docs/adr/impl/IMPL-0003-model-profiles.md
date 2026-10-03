# IMPL-0003: Model Profiles as Data

## Status
**Proposed.** Implements [ADR-0028](../0028-model-capability-boundary.md) rule 4. Amends [ADR-0022](../0022-default-reasoning-high-pre-execution.md): the gpt-oss mapping moves into the profile file with the same values. Date: 2026-10-03. Plan: Phases 2 and 4 of [`docs/plans/0028-model-capability-boundary-plan.md`](../../plans/0028-model-capability-boundary-plan.md).

## Context
Model and provider specifics are hardcoded in the request path:

| Specific | Where |
|---|---|
| Reasoning mapping chosen by name substring (`"gpt-oss"`, `"glm-4.7"`, `"claude"`, `"r1"`…); Nemotron reached gpt-oss's through `"120b"` | `model_classification.py:251-356` |
| Model taxonomy (`_TAXONOMY`, `classify_model`, tier enums), imported nowhere | `model_classification.py:1-250` |
| Default provider order Baseten, Crusoe (gpt-oss providers) for every model | `api_worker.py:27-41`, `83-86` |
| `KNOWN_PROVIDERS` and misspelling hints | `api_worker.py:44-80` |
| Provider alias table in `/dev set provider` | `repl.py:803-811` |
| Closed-object and schema-unsupported provider rules (Cerebras, Groq) | `api_worker.py:135-149` |
| Model-name normalization (gpt-oss only) | `api_worker.py:419-424` |
| `Sys2Client`, exported and never imported | `providers/sys2/` |

## Decision
1. **The profile file.** `providers/profiles.json` is validated by `providers/profiles.py` (Pydantic). It holds a `default` profile, per-model profiles keyed by model slug, and per-provider entries.
2. **Every setting is per stage.** A model profile sets values for the model as a whole, and any of them can be overridden for a single operation (stage). The settings:
   - `reasoning`: a neutral level (`off`, `low`, `medium`, `high`) and an optional `budget_tokens`;
   - `sampling`: `temperature`, `top_p`;
   - `grammar`: `schema`, `json` or `none`;
   - `max_output_tokens`;
   - `providers`: an `order` and `allow_fallbacks`.

   A provider entry may set `strict_all_required` and the operations whose schema the provider rejects.
3. **Resolution, for each setting of each call:**
   1. a CLI flag for that operation;
   2. a CLI flag for every operation;
   3. the model's override for that operation;
   4. the model's value;
   5. the `default` profile.

   The existing flags (`--api-reasoning-effort`, `--api-reasoning-operation`, `--api-model-operation`, `--api-providers`, `--no-structured-output`, `--max-output-tokens`) keep their meaning. The adapter (IMPL-0002) then adjusts the result to the model's capabilities, and records every adjustment.
4. **Nemotron 3 Super is served by Nvidia's own endpoint only.** Its profile pins `providers` to `order: ["Nvidia"]`, `allow_fallbacks: false`. No other host is used or measured for this model. If the endpoint is unavailable, the call fails as a provider error (exit 4) rather than moving to another host.
5. **Initial values, per stage.** These are to be tried and measured on the two named models (plan, Phase 5).

   **Nemotron 3 Super** (`nvidia/nemotron-3-super-120b-a12b:free`):
   - **Model-wide:**
     - sampling `temperature` 1.0, `top_p` 0.95, sent explicitly;
     - `max_output_tokens` 16384;
     - providers Nvidia only, no fallbacks.
   - **Per stage:**

   | Stage (operation) | Reasoning | Budget | Grammar |
   |---|---|---|---|
   | `BOOTSTRAP_ANALYSIS` | `medium` | none | `none` (the semantic read stays free text) |
   | `DRAFT_PROMPT`, `REVISE_PROMPT` | `medium` | none | `schema` |
   | `DRAFT_PLAN`, `REVISE_PLAN` | `medium` | none | `schema` |
   | `INTERPRET_PROMPT_REVIEW`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT` (System 2 fallback) | `medium` | none | `schema` |
   | `DRAFT_EXECUTE`, `EMIT_RESULT_IR` | `medium` | none | `schema` |
   | `EXECUTE` | `low` | 2048 | `json` |
   | `ANSWER_PROTOCOL_DISCUSSION`, `BYPASS_ORDINARY` | `low` | none | per operation today |

   **gpt-oss-120b** (unchanged behaviour):
   - **Model-wide:** sampling is the provider's default; providers Baseten then Crusoe, with fallbacks allowed.
   - **Per stage:**
     - every pre-execution stage `high` (ADR-0022);
     - `EXECUTE` `low`, with `json` grammar (IMPL-0001);
     - other stages `low`;
     - `schema` grammar wherever it is sent today.

   **Provider entries:**

   | Provider | Value |
   |---|---|
   | Groq | rejects the schema for `EXECUTE` and `EMIT_RESULT_IR` |
   | Cerebras | `strict_all_required`; closed objects only |

6. **Removal.** Everything in the Context table is removed or replaced by the profile file and the adapter's metadata (IMPL-0002). An integrity test fails if a model or provider name appears in `src/pdl_taskmaster` outside `profiles.json`.
7. **`EXECUTE` grammar for Nemotron stays `json`.**
   - Nvidia's endpoint currently forces compact JSON: 0 of 6 replies were pretty-printed even when asked. Under compact JSON the forced-key stall did not occur: 0 of 13 identical requests after 15:45 on 2026-10-03.
   - So a measurement on that endpoint cannot show whether the IMPL-0001 schema is safe if the endpoint's decoding changes again.
   - Switching `EXECUTE` back to `schema` is a one-line profile change, to be made only with evidence from Nvidia's endpoint.

## Evidence
- **Nemotron's supported efforts:** `["medium", "low"]` (OpenRouter model metadata), so `high` is not used.
- **The 2048 budget:**
  - the only setting measured to bound runaway reasoning on `EXECUTE` (maximum 2,047, 6/6 completed);
  - budgets for other stages are unmeasured, so none is set;
  - IMPL-0002 has the details.
- **Sampling:** OpenRouter's listed defaults for Nemotron are `temperature` 1.0 and `top_p` 0.95. The harness never sent sampling values, but one reply's echo read `top_p: 1`, so sending them explicitly removes the doubt.
- **Serving endpoint:** every Nemotron call in the 2026-10-03 diagnosis was served by Nvidia (OpenRouter generation records, endpoint `970aecad`), including the stalled ones.
- **The `EXECUTE` grammar:** see IMPL-0001.

## Consequences
- Adding a model means adding a profile entry, if anything. Tuning one stage means changing one entry, not code.
- gpt-oss's effective settings are unchanged.
- Nemotron's pre-execution effort changes from an unsupported `high` to `medium`. Its effect, and every other per-stage value above, is measured in Phase 5 on Nvidia's endpoint.
- Pinning Nemotron to one endpoint without fallbacks trades availability for consistency: an Nvidia outage stops the session instead of silently changing hosts.

## Verification
- **Profile validation tests**, and resolution tests for each of the five levels above.
- **Golden request bodies per stage for both models,** including the Nvidia-only pin.
- **The integrity grep test.**
- **Live runs on the two named models only,** with Nemotron on Nvidia's endpoint only.

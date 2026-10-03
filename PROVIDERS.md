# Provider Baseline: `openai/gpt-oss-120b` through OpenRouter

**Measured:** 2026-10-02, 21:00–21:40 (UTC−4). **Harness:** `pdl-taskmaster` 2.6.0rc1. **Client:** one Windows 11 machine on an ordinary internet connection, so every time below includes the network round trip to OpenRouter.
**Raw data:** [`docs/providers/2026-10-02/`](docs/providers/2026-10-02/). **Re-measure:** see [§7](#7-how-to-reproduce).

These numbers are a dated baseline, not a guarantee. Provider performance changes from hour to hour; OpenRouter's own 30-minute statistics, recorded alongside, agreed with these measurements at the time.

---

## 1. Summary

23 OpenRouter endpoints serve `openai/gpt-oss-120b`. Eight providers were tested in three layers: a streaming benchmark (raw provider speed), a harness conformance probe (does the provider accept the harness's own requests and schemas), and full live `pdlt` sessions pinned to the provider with fallbacks off.

| Provider | Routing honoured | Works end to end with `pdlt` | Streaming speed (low reasoning) | Notes |
|---|---|---|---|---|
| **Cerebras** | yes (8/8) | **yes** (2/2) | fastest: ~2,600 tok/s, 0.44 s total | Fastest end to end (7–8 s per session). Gets the closed-object schema. |
| **Nebius** | yes (8/8) | **yes** (2/2) | ~400 tok/s, 1.6 s | Consistent; ~21 s per session. |
| **Baseten** | yes (8/8) | **yes** (2/2) | ~200 tok/s, 2.4 s | Second in the default order, and the provider the default order relies on for `EXECUTE` (§3). Reports no reasoning-token split. |
| **Crusoe** | yes (8/8) | **yes** (2/2) | ~185 tok/s, 2.3 s | Slow pre-execution calls (~13 s each at high reasoning). |
| **Together** | yes (8/8) | **yes** (2/2) | ~165 tok/s, 2.9 s | ~47 s per session. |
| **DeepInfra** | yes (8/8) | **yes** (2/2), slowly | ~45 tok/s, 9.5 s | 100–150 s per session. At high reasoning it spent the whole 2,048-token test cap on reasoning (3/3 runs). |
| **Groq** | yes (8/8) | **with another provider**: `EXECUTE` and `EMIT_RESULT_IR` are routed away from it | ~465 tok/s, 1.1 s | Rejects the schema of those two operations (HTTP 400) and serves every other operation. Alone it stops at `EXECUTE` with a clear message. See §3. |
| **SambaNova** | yes (8/8) | **no**: fails at `DRAFT_PROMPT` | ~850 tok/s, 1.0 s | Does not support structured output, so OpenRouter removes it for every schema-carrying request. |
| *Default order* (no `--api-providers`) | n/a | **yes** (2/2 on the new order) | n/a | Baseten → Crusoe with fallbacks. Every call of a default session was served by Baseten (verified per call, §3). Groq is no longer in the default order. |

"Routing honoured" counts streaming runs whose response named the requested provider as the one that served it.

---

## 2. Conditions

| | Value |
|---|---|
| Model | `openai/gpt-oss-120b` through `https://openrouter.ai/api/v1` |
| Pinning | `provider: {order: [<provider>], allow_fallbacks: false}`, except the *default order* row |
| Streaming benchmark | `scripts/provider_benchmark.py`: one fixed prompt (an iterative Fibonacci function plus five pytest tests), `stream: true`, `max_tokens` 2,048; 5 runs at `reasoning: low`, then 3 runs at `reasoning: high`; providers run one after another (the conformance probe below ran at the same time during part of the low-reasoning batch: one extra request at a time) |
| Harness probe | `scripts/provider_probe.py`: the harness's own request builder and schemas (`/responses` API, not streamed), `reasoning: low`, `max_output_tokens` 4,096, one call per operation |
| Live sessions | `pdlt --dev --non-interactive --exit-on-close --new-session [--api-providers <provider>]` with input `<task>`, `/confirm`, `/confirm`; harness defaults (reasoning high before `EXECUTE`, low at `EXECUTE`, `--max-output-tokens` 16,384, native sandbox); tasks "Compute the product of 7 and 8." and "Find the prime factorization of 360." |

Definitions: **TTFT** is the time from sending the request to the first streamed token, reasoning or answer. **First text** is the time to the first answer token. **Throughput** is output tokens divided by the time after the first token. **Model time** in live sessions is the sum of the harness's per-call latency.

---

## 3. Groq

**Status: Groq serves every operation except `EXECUTE` and `EMIT_RESULT_IR`, and the harness now routes those two away from it.** It answers `BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `DRAFT_PLAN` and `DRAFT_EXECUTE` correctly and fast, but rejects every `EXECUTE` and `EMIT_RESULT_IR` request before generating:

```
HTTP 400: Groq: invalid JSON schema for response_format: 'EXECUTION_OUTCOME':
/properties/outcome/anyOf/1/properties/result_ir/anyOf/0/properties/witness/anyOf:
anyOf object variant error: variant 0: properties must be present (or set additionalProperties:false)
```

**Cause.** In the `EXECUTE` schema the optional witness is `anyOf[ anyOf[positive, negative], null ]`. Groq's schema validator reads each union branch as an object type and rejects a branch that is itself a union. The nesting comes from the strict-schema transform in `providers/api_worker.py` (an optional union becomes `anyOf[<union>, null]`) together with the positive-witness branch added in commit `e233258a`; that commit's regression test checked the schema with `jsonschema`, which accepts it, not with Groq's stricter validator.

**Routing (since this release).** `providers/api_worker.py` keeps a table of operations a provider rejects (`_SCHEMA_UNSUPPORTED_OPERATIONS`: Groq → `EXECUTE`, `EMIT_RESULT_IR`). For those operations, when the schema is sent, Groq is removed from the provider order and added to OpenRouter's `ignore` list, so no fallback can land on it; every other operation is unchanged. With `--no-structured-output` no schema is sent and Groq is not excluded. If Groq is the only configured provider, the call stops before any request with `EXECUTE cannot be routed to the configured providers (Groq): Groq rejects its output schema; add another provider to --api-providers or run with --no-structured-output` (exit 4).

**Default order (since this release): Baseten → Crusoe.** Groq was removed from the default order so that a default session is served by one provider, not split between Groq for planning and another provider for `EXECUTE`. Amazon Bedrock was removed as a fallback because it does not support structured output. Cerebras is not a default either: anywhere in the order it closes every free-form object, which drops the positive witness for all providers. `OPENROUTER_PROVIDER` and `OPENROUTER_PROVIDER_ORDER` still override the default. The routing table above stays as a safety net for users who configure Groq themselves.

Verified live on 2026-10-02 with OpenRouter's generation records (`provider_name` per call, [`routing-verification.json`](docs/providers/2026-10-02/routing-verification.json)):

| Configuration | Sessions | Planning calls served by | `EXECUTE` served by | Result |
|---|---|---|---|---|
| Default order, new (Baseten → Crusoe) | 2 | Baseten | Baseten | `CLOSED_SUCCESS`, exit 0 (both) |
| Default order, previous (Groq → Baseten → Amazon Bedrock) | 2 | Groq | Baseten | `CLOSED_SUCCESS`, exit 0 (both) |
| `--api-providers Groq,Baseten` | 2 | Groq | Baseten | `CLOSED_SUCCESS`, exit 0 (both) |
| `--api-providers Groq` | 2 | Groq | not sent | exit 4 with the message above (both) |

Before this change the default order worked only by accident: Groq's 400 made OpenRouter fall through to Baseten.

**Why it is not fixed here.** Flattening the nested union was tested on 2026-10-02 and makes Groq accept the schema, but Groq then fails the generation instead:

- Groq does not constrain decoding of `gpt-oss-120b` through OpenRouter's `/responses` API, with or without `strict: true`, with open or closed objects: it generates freely and validates afterwards (12/12 generations rejected across the four combinations, 3 each).
- The strict schema marks every property required (Groq rejects a schema whose `required` lists are incomplete: 3/3 HTTP 400), while the model routinely omits optional fields such as `result_ir.witness`; the generation then fails validation (3/3).
- A generation failure is returned inside a 200 response, and OpenRouter does not fall back on it. With the flattened schema the **default order failed `EXECUTE` in both live sessions**, where the shipped schema succeeds. The flattening was therefore reverted.
- `EXECUTE` deliberately never retries without the schema (one model call per counted attempt, `api_worker.py`), so the harness's schema-free fallback does not apply.

The explicit routing above is the chosen remedy. A general mechanism (providers declaring which operations and schema features they support) belongs to provider capability routing ([ADR-0024](docs/adr/0024-operation-profiles.md)).

**Comparison with known Groq schema issues.** [GlassHaven/Haven#664](https://github.com/GlassHaven/Haven/issues/664) reports the same *class* of failure: Groq rejects a whole request when one schema construct breaks its stricter validator (there, arrays with no `items`). Every harness schema was scanned: no array lacks `items`, and no object has `required` without `properties`. The construct here is different (a union nested inside a union). The second failure mode above, a generation rejected because optional fields were omitted under an all-required schema, is the "optional fields under strict mode" behaviour also commonly reported for Groq.

---

## 4. Measurements

### 4.1 Streaming benchmark

Median [minimum–maximum] over the runs. All runs succeeded and every response was served by the requested provider.

**`reasoning: low`, 5 runs each** (started 21:06; about 390–450 output tokens):

| Provider | TTFT s | First text s | Total s | Output tokens | Reasoning tokens | Throughput tok/s |
|---|---|---|---|---|---|---|
| Cerebras | 0.28 [0.23–0.48] | 0.30 | 0.44 [0.35–0.62] | 402 | 13 | 2,593 [2,539–3,621] |
| SambaNova | 0.53 [0.47–2.74] | 0.53 | 0.98 [0.92–3.20] | 389 | 13 | 854 [833–864] |
| Groq | 0.27 [0.22–0.41] | 0.34 | 1.11 [1.03–1.28] | 385 | 13 | 464 [409–478] |
| Nebius | 0.34 [0.33–0.61] | 0.43 | 1.55 [1.37–1.74] | 450 | 14 | 401 [333–413] |
| Crusoe | 0.23 [0.19–0.35] | 0.41 | 2.33 [2.14–3.75] | 405 | 19 | 185 [119–205] |
| Baseten | 0.39 [0.31–0.55] | 0.48 | 2.36 [1.96–2.91] | 405 | not reported | 204 [172–246] |
| Together | 0.41 [0.34–0.49] | 0.47 | 2.86 [2.53–3.17] | 399 | 12 | 164 [151–167] |
| DeepInfra | 0.53 [0.42–1.08] | 1.04 | 9.47 [9.21–16.84] | 413 | 21 | 46 [26–48] |

**`reasoning: high`, 3 runs each** (about 1,400–1,900 output tokens, most of them reasoning):

| Provider | TTFT s | First text s | Total s | Output tokens | Reasoning tokens | Throughput tok/s | Finish |
|---|---|---|---|---|---|---|---|
| Cerebras | 0.24 | 0.80 | 0.95 [0.80–1.29] | 1,514 | 1,186 | 2,121 | 1 of 3 hit the 2,048 cap |
| SambaNova | 0.85 | 2.68 | 3.06 [2.92–5.71] | 1,907 | 1,563 | 783 | stop |
| Groq | 0.25 | 2.59 | 3.28 [2.96–3.88] | 1,432 | 1,100 | 472 | stop |
| Nebius | 0.44 | 4.24 | 4.84 [4.15–5.05] | 1,585 | 1,288 | 359 | stop |
| Baseten | 0.52 | 5.63 | 6.81 [6.81–7.63] | 1,412 | not reported | 213 | stop |
| Crusoe | 0.24 | 5.82 | 7.53 [7.43–9.75] | 1,629 | 1,327 | 218 | 1 of 3 hit the cap |
| Together | 0.41 | 7.41 | 9.19 [7.69–11.57] | 1,491 | 1,193 | 164 | stop |
| DeepInfra | 0.50 | no answer | 47.61 [45.17–66.10] | 2,048 | 2,029 | 44 | 3 of 3 hit the cap |

At high reasoning, time to first *answer* token is dominated by reasoning: it equals reasoning tokens divided by throughput. That is the latency the protocol pays three times per task before execution (ADR-0022).

**OpenRouter's own statistics** at the same time (last 30 minutes, p50): throughput Cerebras 775, Groq 333, SambaNova 330, Nebius 260, Crusoe 188, Baseten 170–177, Together 126, DeepInfra 41 tok/s; latency 150 ms (Groq) to 994 ms (SambaNova). The same ranking as the table above except two adjacent pairs (Groq and SambaNova, Crusoe and Baseten).

### 4.2 Harness conformance probe

One call per operation through the harness's own request builder, pinned, fallbacks off, with the schema as shipped. `OK` means the provider accepted the request and the host accepted the reply.

| Provider | `BOOTSTRAP_ANALYSIS` | `DRAFT_PROMPT` | `DRAFT_PLAN` | `EXECUTE` |
|---|---|---|---|---|
| Cerebras | OK 0.3 s | OK 0.3 s | OK 0.3 s | OK 0.4 s |
| Nebius | OK | OK | OK | OK |
| Baseten | OK | OK | OK | OK 0.6 s |
| Crusoe | OK | OK | OK | OK |
| Together | OK | OK | OK | OK |
| DeepInfra | OK 1.8 s | OK 5.3 s | OK 2.2 s | **output cap**: 4,096 tokens reached after 92 s |
| Groq | OK 0.4 s | OK 1.2 s | OK 0.6 s | **HTTP 400**: schema rejected (§3); now never routed there |
| SambaNova | OK 0.5 s | **HTTP 404** | **HTTP 404** | **HTTP 404** |

`BOOTSTRAP_ANALYSIS` carries no schema, which is why SambaNova passes it. The probe's synthetic `EXECUTE_WITNESS` case (a witness demanded from an artificial input at low reasoning) failed on every provider in different ways, which points at the case rather than the providers; the live verified sessions below are the meaningful test. DeepInfra's capped `EXECUTE` did not recur in live sessions, where `EXECUTE` completed in about 5 s.

### 4.3 Live `pdlt` sessions

Two sessions per configuration on the final 2.6.0rc1 code. *Verified* means the program ran in the sandbox and verification passed; *analytical* means the model answered without code (a first-class deliverable under GUARD-03); every answer was correct (56; 360 = 2³·3²·5).

| Configuration | Task | Exit | Final stage | Wall s | Model s | Output tokens | Calls | Repairs | Result |
|---|---|---|---|---|---|---|---|---|---|
| Cerebras | product | 0 | `CLOSED_SUCCESS` | 6.7 | 3.7 | 3,509 | 4 | 0 | verified |
| Cerebras | factor 360 | 0 | `CLOSED_SUCCESS` | 7.8 | 4.9 | 4,606 | 4 | 0 | sandbox run |
| Baseten | product | 0 | `CLOSED_SUCCESS` | 17.2 | 14.4 | 3,389 | 4 | 0 | verified |
| Baseten | factor 360 | 0 | `CLOSED_SUCCESS` | 19.7 | 17.2 | 3,802 | 4 | 0 | analytical |
| Default order | product | 0 | `CLOSED_SUCCESS` | 20.5 | 16.7 | 5,641 | 5 | 1 | verified |
| Default order | factor 360 | 0 | `CLOSED_SUCCESS` | 16.8 | 14.1 | 4,935 | 4 | 0 | analytical |
| Nebius | product | 0 | `CLOSED_SUCCESS` | 21.4 | 18.6 | 4,962 | 4 | 0 | verified |
| Nebius | factor 360 | 0 | `CLOSED_SUCCESS` | 21.4 | 18.5 | 5,042 | 4 | 0 | verified |
| Crusoe | product | 0 | `CLOSED_SUCCESS` | 31.8 | 28.8 | 4,845 | 4 | 0 | verified |
| Crusoe | factor 360 | 0 | `CLOSED_SUCCESS` | 48.4 | 45.8 | 6,540 | 4 | 0 | analytical |
| Together | product | 0 | `CLOSED_SUCCESS` | 47.7 | 44.3 | 4,779 | 5 | 1 | verified |
| Together | factor 360 | 0 | `CLOSED_SUCCESS` | 46.8 | 44.0 | 5,306 | 4 | 0 | verified |
| DeepInfra | product | 0 | `CLOSED_SUCCESS` | 150.1 | 147.1 | 5,909 | 4 | 0 | verified |
| DeepInfra | factor 360 | 0 | `CLOSED_SUCCESS` | 103.5 | 100.6 | 6,065 | 4 | 0 | analytical |
| Groq | product | 4 | `PLAN_REVIEW` | 14.3 | 11.0 | 4,362 | 3 | n/a | HTTP 400 at `EXECUTE` (before the routing change; now a clear refusal, §3) |
| Groq | factor 360 | 4 | `PLAN_REVIEW` | 10.7 | 7.8 | 2,850 | 3 | n/a | as above |
| SambaNova | product | 4 | none | 4.8 | 2.4 | 1,353 | 1 | n/a | HTTP 404 at `DRAFT_PROMPT` |
| SambaNova | factor 360 | 4 | none | 4.8 | 2.6 | 1,298 | 1 | n/a | HTTP 404 at `DRAFT_PROMPT` |

**Median model time per call** in live sessions (seconds):

| Configuration | `BOOTSTRAP_ANALYSIS` | `DRAFT_PROMPT` | `DRAFT_PLAN` | `EXECUTE` |
|---|---|---|---|---|
| Cerebras | 1.2 | 1.1 | 1.5 | 0.5 |
| Groq | 3.8 | 3.4 | 2.2 | fails |
| Baseten | 4.8 | 4.9 | 4.1 | 2.0 |
| Default order | 5.4 | 5.0 | 2.4 | 1.7 |
| Nebius | 5.7 | 7.1 | 4.2 | 1.5 |
| Together | 11.4 | 20.6 | 7.5 | 2.9 |
| Crusoe | 12.7 | 14.6 | 8.6 | 1.5 |
| DeepInfra | 41.6 | 60.7 | 16.4 | 5.2 |

The three pre-execution operations, run at high reasoning, account for most of every session's model time; `EXECUTE` at low reasoning is short on every provider.

---

## 5. Errors and retry behaviour observed

| Behaviour | Where | What the harness did |
|---|---|---|
| Schema rejected at request time (HTTP 400) | Groq, `EXECUTE` and `EMIT_RESULT_IR` | Before this release: pinned, exit 4 with the provider's message; default order, OpenRouter fell back. Now these calls are never sent to Groq (§3). |
| Provider removed for an unsupported parameter (HTTP 404) | SambaNova, every schema-carrying operation | Pinned: no retry, exit 4. Before this release the message wrongly suggested a misspelled provider name; it now names the unsupported parameter and suggests `--no-structured-output` (`test_a_provider_without_a_requested_parameter_is_named_as_such`). |
| Generation rejected against the schema (error inside an HTTP 200) | Groq, with the flattened schema only (§3) | `EXECUTE`: counted as a failed attempt, then one repair, then `CLOSED_CANCELLED`. OpenRouter did not fall back. |
| Output cap reached | DeepInfra (probe `EXECUTE`; benchmark at high reasoning) | Counted as `OUTPUT_LIMIT_REACHED`, never retried silently. |
| Verification repair | Default order and Together, one product session each | One repair, then `CLOSED_SUCCESS`. |
| Transient retries (429, 5xx, timeouts) | none observed | The worker would retry these with backoff, up to 5 attempts within the call deadline. |
| Reply stalled in whitespace under the output schema | `nvidia/nemotron-3-super-120b-a12b:free` (Nvidia), `EXECUTE`; intermittent (§6.7) | Counted as `OUTPUT_LIMIT_REACHED`; the cut-off reply is kept (`model-response.truncated.txt`), and later `EXECUTE` calls in the session go without the decoding constraint. Before this change the repair was an identical request and failed the same way. |

---

## 6. Findings and recommendations

1. **Groq cannot serve `EXECUTE` or `EMIT_RESULT_IR`** (§3). It is no longer in the default order, and when a user configures it the harness routes those two operations away from it explicitly; verified per call. Do not "fix" Groq by flattening the schema: Groq then fails generations instead, and OpenRouter does not fall back on that.
2. **SambaNova needs `--no-structured-output`** to be usable; it was not tested in that mode.
3. **For speed, Cerebras is the clear choice** (7–8 s per session against 17–21 s for Baseten and Nebius). It receives the closed-object schema, so model-asserted positive witnesses cannot be expressed there; the sandbox witness is unaffected.
4. **DeepInfra is usable but slow** (45 tok/s), and at high reasoning it can exhaust a small output cap on reasoning alone.
5. **The harness does not record which provider served a call.** OpenRouter's `/responses` reply has no provider field; the generation lookup (`GET /api/v1/generation?id=<response_id>`, `provider_name`) does. Each call's `response_id` is now in the session's `call-trace.jsonl`, and `scripts/model_compare.py` joins the two (TTFT, provider, served model, native finish reason).
6. **Throughput alone does not predict session time.** Session time depends on reasoning tokens per pre-execution call, the number of calls, and repairs; Groq's raw speed does not help if `EXECUTE` cannot run there.
7. **Nemotron 3 Super (`:free`, served by Nvidia) can stall under the `EXECUTE` schema** (2026-10-03). In two sessions, every `EXECUTE` reply held the complete answer through `"open_defects": []` and then only `"\n   "` until the 16,384-token cap (26K–29K characters; 39–150 s per call), so the turn closed with no answer. Replaying the captured request: with the schema 0/3 completed (two whitespace stalls, one 8K-token reasoning run); with `json_object` 3/3 and with no format 3/3. Fifty minutes later the same request completed 4/4 with the schema, and six graded catalogue sessions had no stall: the fault is in the provider's constrained decoding and comes and goes. The free endpoint accepts neither `frequency_penalty` nor `repetition_penalty`, so a sampling penalty is not available. When it stalls, the worker drops the constraint for later calls of that operation (ARCHITECTURE §8).

| 2026-10-03, graded catalogue (`scripts/model_compare.py`) | gpt-oss-120b (Baseten) | Nemotron 3 Super `:free` (Nvidia) |
|---|---|---|
| Sessions closed `CLOSED_SUCCESS` | 4/4 | 6/6 |
| Correct answers (16-01 three gods, 16-03 knights, 01-03 coloring, 16-06 siblings) | 3/4 (gods wrong) | 3/6 (gods wrong 3/3) |
| `EXECUTE`: latency / output tokens (reasoning) | 3.0–3.7 s / 372–770 (0) | 12–32 s / 1.8K–3.0K (0.9K–2.3K) |
| `EXECUTE` time to first token | not reported by the generation lookup | 367–504 ms (3 calls reported) |
| Turn time | 52–81 s | 53–126 s |

---

## 7. How to reproduce

```bash
# Raw provider speed (streaming, pinned, no fallbacks)
python scripts/provider_benchmark.py --providers Groq,Cerebras,SambaNova,DeepInfra,Together,Nebius,Baseten,Crusoe --runs 5 --reasoning low
python scripts/provider_benchmark.py --providers Groq,Cerebras,SambaNova,DeepInfra,Together,Nebius,Baseten,Crusoe --runs 3 --reasoning high

# Harness conformance (the harness's own requests and schemas)
python scripts/provider_probe.py --providers Groq,Cerebras,SambaNova,DeepInfra,Together,Nebius,Baseten,Crusoe

# A live session pinned to one provider
printf 'Compute the product of 7 and 8.\n/confirm\n/confirm\n' | pdlt --dev --non-interactive --exit-on-close --new-session --api-providers Cerebras
```

All three need `OPENROUTER_API_KEY`. The benchmark writes `runs/provider-bench/<timestamp>/results.json`; the probe writes one record per call under `runs/provider-probe/<timestamp>/`. To check which providers currently serve the model and their OpenRouter statistics:

```bash
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models/openai/gpt-oss-120b/endpoints
```

| File | Contents |
|---|---|
| `docs/providers/2026-10-02/stream-benchmark-reasoning-low.json` | Every streaming run at low reasoning |
| `docs/providers/2026-10-02/stream-benchmark-reasoning-high.json` | Every streaming run at high reasoning |
| `docs/providers/2026-10-02/harness-probe.json` | Probe verdicts per provider and operation |
| `docs/providers/2026-10-02/live-sessions.json` | Every live session with per-call latency and tokens, plus the rejected flattened-schema variant |
| `docs/providers/2026-10-02/routing-verification.json` | Sessions after the routing change, with the provider that served each call |

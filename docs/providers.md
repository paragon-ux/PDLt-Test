# Providers and models

PDLt calls two kinds of model, both through [OpenRouter](https://openrouter.ai) by default, with one key (`OPENROUTER_API_KEY`):

| Role | What it does | Default | Change it with |
|---|---|---|---|
| **Task model** (System 2) | Interprets the request, plans, and writes the deliverable and its programs | `openai/gpt-oss-120b` (L167; `nvidia/nemotron-3-super-120b-a12b:free` is the free option, not yet measured with the defaults) | `--model` (REPL, headless); `create_worker("api", model=...)` (Python) |
| **System 1** | Routes each request and refuses out-of-bounds ones before any task-model call | `typesafe/jev-1.13`, on OpenRouter's decisions endpoint | `SYS1_MODEL`, `SYS1_ENDPOINT`, `SYS1_API_KEY`; or `create_system1(...)` in Python |

## Which models work

PDLt's requests use structured output (a JSON schema the reply must follow) and reasoning effort settings. Its request setup was developed and measured on `openai/gpt-oss-120b` (the default and the catalogue baseline model) and Nemotron 3 Super free. Other models may reject the schema or the settings; such a rejection is reported as a provider error (exit 4), never as a task result. Try a model on one task before relying on it. Measurements by provider, and the providers known to reject the schemas, are in [PROVIDERS.md](https://github.com/paragon-ux/PDLt-Test/blob/main/PROVIDERS.md).

## Provider order

OpenRouter serves one model through several providers. Unless told otherwise, PDLt asks for **Baseten**, then **Crusoe**, and lets OpenRouter fall back to others. Both serve every operation with PDLt's schemas. Saver mode with in-call tools, the default, asks for **Cerebras** first, then Baseten and Crusoe (ADR-0031). These orders apply to the model families with recorded settings (`gpt-oss`, Nemotron 3 Super); any other model is routed by OpenRouter's own defaults.

| To | Use |
|---|---|
| Put another provider first | `OPENROUTER_PROVIDER=Name` |
| Set the whole order | `OPENROUTER_PROVIDER_ORDER=A,B` |
| Use only some providers, in order (REPL, headless) | `--api-providers A,B` |

A name PDLt does not know gets a warning, not a refusal, since OpenRouter adds providers.

## Reasoning effort

By default each operation gets the model's own mapping: for `gpt-oss` and Nemotron 3 Super, low on every operation (L155, ADR-0031). To override it:

| Where | Every operation | One operation |
|---|---|---|
| REPL, headless | `--api-reasoning-effort low` | `--api-reasoning-operation EXECUTE=medium` (repeatable) |
| Catalogue runner | `--reasoning low` | `--reasoning-op EXECUTE=medium` (repeatable) |

The operations: `BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `REVISE_PROMPT`, `INTERPRET_PROMPT_REVIEW`, `DRAFT_PLAN`, `REVISE_PLAN`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT`, `DRAFT_EXECUTE`, `EXECUTE`, `EXECUTE_UNCONFIRMED`, `EMIT_RESULT_IR`.

## Other limits per call

| Setting | Default | Flag |
|---|---|---|
| Output tokens per call, reasoning included | 16,384 | `--max-output-tokens` |
| Wall-clock seconds per call, retries included | 300 | `--api-call-deadline` |

A reply cut off at the output cap is a failed attempt. Network timeouts and provider errors are harness errors (exit 4), not model outcomes.

## Your own provider

Any OpenAI-compatible Responses API host: `--api-base-url URL --api-key-env NAME_OF_KEY_VARIABLE`. Anything else: register a provider through the [Extensions SDK](extensions.md#providers).

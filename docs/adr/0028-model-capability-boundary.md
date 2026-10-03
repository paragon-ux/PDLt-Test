# ADR-0028: Provider Boundary: the Protocol States Intent, an Adapter Speaks to Providers

## Status
**Proposed.** Date: 2026-10-03. Deciders: project maintainers.

- Implements the capability-descriptor part of [ADR-0024](0024-operation-profiles.md); its profiles, budgets and System 1 configuration stay there.
- Amends [ADR-0022](0022-default-reasoning-high-pre-execution.md): per-model reasoning choices become data, expressed in provider-neutral levels.
- Extends [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md) (Pydantic as the single source of truth) to the output schema the model reads.
- Implemented by [IMPL-0001](impl/IMPL-0001-output-contracts-from-pydantic.md), [IMPL-0002](impl/IMPL-0002-openrouter-capability-adapter.md) and [IMPL-0003](impl/IMPL-0003-model-profiles.md). Plan: [`docs/plans/0028-model-capability-boundary-plan.md`](../plans/0028-model-capability-boundary-plan.md).

## Context
PDLt's protocol (stages, gates, operation contracts, verification) is meant to be independent of which model serves it. In practice the two are blended. The worker that calls the model also decides:
- which reasoning settings each model gets, by matching its name;
- which providers to prefer;
- which provider quirks to apply to every request.

The schema that constrains the model's output is built separately from the schema the model is shown.

Switching the default model exposed both problems at once.
- **The turn failed.** A turn closed with no answer: the model wrote its full answer, then stalled until the output cap. The grammar the provider enforced required a key that the schema shown to the model did not contain, so the model could not legally finish (evidence in [IMPL-0001](impl/IMPL-0001-output-contracts-from-pydantic.md)).
- **Settings went out unchecked.** The same requests carried a reasoning setting the model does not support, and nothing checked or reported it.

Neither problem was specific to that model; each was waiting for any model that differed from the one the code was written against.

The provider (OpenRouter) publishes what each model and endpoint supports. The harness did not read it.

## Decision
The protocol and the providers are separated the way MVVM separates the ViewModel from the Model:

- **View:** the REPL and host presentation. Unchanged.
- **ViewModel:** the protocol plane. It states what each operation needs: its output contract, a reasoning depth, an output budget, and how strictly the output's form must be enforced. It never names a model, a provider or an API parameter.
- **Model:** the provider plane, reached only through an **adapter**. The adapter owns everything provider-specific: discovering capabilities, translating intent into a request, adjusting to what the model supports, and normalizing the reply.

Five rules follow.

1. **One output contract per operation.** The schema shown to the model and the constraint sent to the provider come from the same definition. Whatever the provider enforces, the model has been shown. Optional parts of a contract stay optional unless a provider requires otherwise, and then the model is shown that form too.
2. **Capabilities are discovered, not assumed.** The adapter learns what each model and provider supports from the provider's own published metadata. Code does not encode what a model can do.
3. **Adjustments are explicit.** When intent asks for something a model does not support, the adapter uses the nearest supported equivalent and reports it. It never sends a parameter the model does not list, and never changes a setting silently.
4. **Model-specific choices are data, per stage.** What metadata cannot express is declared per model in configuration, and can be set separately for each operation (stage). That includes reasoning depth and budget, sampling, how strictly output is constrained, output limits, and which provider serves the model, including pinning one provider with no fallback. Adding a model or tuning a stage never requires a code change.
5. **Neutrality is unchanged.** The adapter changes how a request is expressed, never the task or the method. No adjustment may add guidance (GUARD-01, GUARD-04), and the text the model reads changes only through reviewed changes to the contracts.

## Options considered

### A. Fix the failure where it occurred
Correct the one schema, add a branch for the new model.

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Next model | Repeats the investigation; unsupported settings still go out silently |

### B. Read capabilities, keep the rest
Discover capabilities and adjust parameters; leave schemas as they are.

| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| This failure | **Not fixed**: the model advertises structured output, so the mismatched constraint is still sent |

### C. Separate the planes, single-source the contracts (chosen)

| Dimension | Assessment |
|---|---|
| Complexity | Medium to high |
| This failure | Fixed for every model and provider |
| Next model | Metadata, plus at most a configuration entry |

A alone keeps the defect class. B alone misses the cause, which is independent of the model. C removes both the class (shown and enforced schemas cannot disagree) and the blending.

## Consequences
- **Easier:**
  - changing or adding models;
  - seeing exactly what was sent to a provider and what was adjusted;
  - testing the protocol with no provider at all, because intent is plain data.
- **Harder:**
  - output contracts can only be changed in one place, which is intended;
  - startup depends on provider metadata, mitigated by caching and a conservative fallback.
- **To measure:** the model now sees keys the constraint already required. Each model's effective settings move to the nearest supported values.
- **Unchanged:** protocol stages, gates, verification, witness authority, guardrails.
- **Revisit:** System 1 behind the same boundary, and operation profiles and budgets (both ADR-0024).

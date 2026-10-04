# ADR-0022: One Effective Reasoning Configuration for Live Sessions and Catalogue Runs

## Status
Accepted. Amends the 2026-09-16 amendment to [ADR-0006](0006-bounded-pre-execution-reasoning.md) (Decision D25) for gpt-oss. ADR-0006's decision (no solving, researching or calculating before execution) is unchanged. Per-model values move to data under [ADR-0028](0028-model-capability-boundary.md). The values and evidence are in [IMPL-0004](impl/IMPL-0004-reasoning-allocation-per-model.md).

## Context
A live REPL session and a catalogue run of the same request did not behave alike, because they did not run at the same reasoning effort: each had its own default. The configuration the user had validated as working was not the default of either.

Running every operation at the lowest effort also degraded the artifacts. Plans copied the prompt verbatim, and prompts carried drafting meta-rules that the deliverable then obeyed.

## Decision
1. **The production model's default** (gpt-oss when decided) is deep reasoning for every operation before execution, and light reasoning at `EXECUTE`.
2. **One resolution, in one place.**
   - Per-operation settings win.
   - An explicitly requested effort applies to every other operation.
   - With no request, the model's default allocation applies.
3. **The catalogue runner has no default of its own.** Without an explicit setting it uses the harness's, exactly as a live session does.
4. **The effective configuration is recorded:** in run metadata, in every session transcript, and in dev telemetry.

## Consequences
- A catalogue result describes the REPL a user actually runs.
- Pre-execution calls cost more output tokens and time. Each response is still capped by the output limit and the per-call deadline.
- Deeper reasoning before execution makes it more tempting for the model to work the task out early. ADR-0006 still applies, and copied plans are recorded.
- Scores from runs under different defaults are not directly comparable.

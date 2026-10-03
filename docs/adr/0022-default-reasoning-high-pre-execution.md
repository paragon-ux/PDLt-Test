# ADR-0022: Default Reasoning for gpt-oss: High Before Execution, Low at EXECUTE

## Status
Accepted. Amends the model class matrix of [ADR-0006](0006-bounded-pre-execution-reasoning.md) (Amendment D25) for `openai/gpt-oss-120b`. ADR-0006's decision (no solving, researching or calculating before execution) is unchanged.

## Context
A live REPL session and a catalogue run of the same request did not behave alike, because they did not run at the same reasoning effort:

- With no flags, `ApiWorker` used `get_proportional_reasoning_mapping`, which for gpt-oss mapped every operation to `low`. The catalogue runner's `--reasoning` also defaulted to `low`.
- The configuration the user validated as working ran `--reasoning high --reasoning-op EXECUTE=low` with providers Cerebras and `--max-repairs 0` (run-20261001-221930): high everywhere, low at EXECUTE.
- At all-low, live sessions produced plans that copied the prompt verbatim (identical prompt and plan bodies) and prompts that carried PDL-08 drafting meta-rules ("DO NOT perform the calculation"), which the deliverable then obeyed.

## Decision
1. The gpt-oss mapping is `high` for every operation it lists (`BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `REVISE_PROMPT`, `INTERPRET_PROMPT_REVIEW`, `DRAFT_PLAN`, `REVISE_PLAN`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT`, `DRAFT_EXECUTE`, `EMIT_RESULT_IR`) and `low` for `EXECUTE`. Operations it does not list (`ANSWER_PROTOCOL_DISCUSSION`, `BYPASS_ORDINARY`) use the worker default, `low`.
2. `model_classification.resolve_reasoning` resolves the effective configuration in one place: per-operation flags win; an explicit effort applies to every other operation; with no effort, the model mapping is the default.
3. `run_catalogue.py --reasoning` has no default of its own: without it the harness default applies, exactly as in a live session. Explicit flags keep working.
4. The effective configuration is recorded: `RUN_META.json` carries `reasoning_effective` (default and per operation), and every REPL session writes a `REASONING:` transcript line (and a `[dev:telemetry]` line in dev mode).

## Consequences
- Live sessions and catalogue runs share one default, so a catalogue result describes the REPL a user runs.
- Pre-execution calls cost more output tokens and take longer. Each response is still capped by `max_output_tokens` and the per-call deadline.
- High effort before execution makes it more tempting for the model to work the task out early. ADR-0006 still applies: the prompt and plan state the task and the procedure, never the answer. `PLAN_PROMPT_ECHO` records copied plans; answer leakage into artifacts is not linted.
- Catalogue scores from runs at the old `low` default are not directly comparable with runs at the new default.

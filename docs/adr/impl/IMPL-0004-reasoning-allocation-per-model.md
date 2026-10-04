# IMPL-0004: Reasoning Allocation per Model (Current Mapping)

## Status
**Accepted.** Implements the amendment to [ADR-0006](../0006-bounded-pre-execution-reasoning.md) (Decision D25, 2026-09-16) and [ADR-0022](../0022-default-reasoning-high-pre-execution.md). It is to be superseded by [IMPL-0003](IMPL-0003-model-profiles.md) when ADR-0028 is accepted.

## Context
ADR-0006 bounds pre-execution reasoning. Its 2026-09-16 amendment and ADR-0022 decide that effort is allocated per operation, and resolved in one place shared by live sessions and catalogue runs. This record holds the concrete mapping and where it lives.

## Decision (as implemented)
- **Where.** `runtime/model_classification.py`:
  - `get_proportional_reasoning_mapping(model_id)` returns per-operation efforts, chosen by substring of the model id;
  - `resolve_reasoning` applies per-operation flags first, then an explicit global effort, then the model mapping;
  - `DEFAULT_REASONING_EFFORT = "low"` covers unlisted operations.
- **gpt-oss** (`"gpt-oss"`; Nemotron 3 Super also maps here, see below), from ADR-0022:
  - `high` for `BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `REVISE_PROMPT`, `INTERPRET_PROMPT_REVIEW`, `DRAFT_PLAN`, `REVISE_PLAN`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT`, `DRAFT_EXECUTE` and `EMIT_RESULT_IR`;
  - `low` for `EXECUTE`;
  - `ANSWER_PROTOCOL_DISCUSSION` and `BYPASS_ORDINARY` use the default.
- **The model class matrix from the 2026-09-16 amendment:**
  - **Class A, native effort tiers** (GLM-4.7, o-series): `BOOTSTRAP_ANALYSIS` high; prompt drafting low; plan drafting and `EXECUTE` none.
    - The GLM entry was later amended by the ADR-0009 benchmark: `EXECUTE` and `DRAFT_EXECUTE` high, `EMIT_RESULT_IR` low.
  - **Class B, explicit token budgets** (Claude): `BOOTSTRAP_ANALYSIS` 4096; prompt drafting 1024; planning and `EXECUTE` none.
  - **Class C, open-weights thinking models** (R1, Qwen Thinking): thinking on for bootstrap and prompt drafting, off for planning and `EXECUTE`.
  - **Class D, instruct models** (the default): reasoning disabled everywhere; deliberation is carried in-band by structured fields.
- **Recording.** `RUN_META.json` carries `reasoning_effective`; every REPL session writes a `REASONING:` transcript line, plus a `[dev:telemetry]` line in dev mode.

## Evidence
- **Class matrix (2026-09-16).**
  - Effort labels do not map to fixed token counts across providers: GLM-4.7 used 2,123 reasoning tokens at `low`, and Anthropic enforces a 1,024-token minimum budget.
  - Forcing `none` on lower-capacity models dropped nested entities (for example "Apartment 4B") and took parsing shortcuts.
- **gpt-oss mapping (ADR-0022, run-20261001-221930).** At all-`low`, plans copied the prompt verbatim and prompts carried PDL-08 meta-rules. `high` before execution with `low` at `EXECUTE` was the validated configuration.
- **Nemotron 3 Super (2026-10-03).**
  - Before `aada9387` it reached the gpt-oss mapping through a bare `"120b"` match; it is now named explicitly with the same values.
  - OpenRouter lists only `low` and `medium` for it, so `high` is sent unchecked. ADR-0028 and IMPL-0002/0003 replace this.

## Consequences
- Adding a model family means editing code. This is the defect ADR-0028 removes.
- Catalogue scores from runs at different mappings are not directly comparable.

## Verification
`tests/test_reasoning_wire.py`; `tests/test_wire_repairs.py::test_nemotron_keeps_its_reasoning_profile_without_a_bare_120b_match`.

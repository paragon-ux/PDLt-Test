# IMPL-0008: System 1 Client, Recipes, Gating and Boundary Routing

## Status
**Accepted.** Implements [ADR-0012](../0012-system-1-decision-models-via-rlcd.md), Pillar 1 of [ADR-0017](../0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md), and [ADR-0020](../0020-system-1-environment-conditioned-refusal-routing.md). Recorded 2026-10-03 from the 2.6.0rc1 code.

## Context
ADR-0012 assigns governance classifications to a non-generative System 1 decision model, behind a calibrated gate, with the harness owning every transition. ADR-0020 adds boundary refusals conditioned on the declared environment. This record holds the client, the recipes, the thresholds and the configuration.

## Decision (as implemented)
- **Client** (`providers/sys1/client.py`):
  - endpoint `https://openrouter.ai/api/alpha/decisions` (`DEFAULT_SYS1_ENDPOINT`);
  - model `typesafe/jev-1.13`, overridable by `SYS1_MODEL`;
  - key `SYS1_API_KEY`, else `OPENROUTER_API_KEY`;
  - calls are traced in the worker's call lifecycle as `SYSTEM1:<question>`.
- **Recipes** (`providers/sys1/recipes/`):
  - `activation_route`: route, including `BLOCKED_BY_HIGHER_PRIORITY`;
  - `problem_class`: `VERIFIED_EXECUTION` or `STANDARD_EXECUTION`;
  - `execution_profile`: the budget tier, see IMPL-0010;
  - `confirmation_match` and `review_facets`: review interpretation;
  - `follow_up`;
  - `plan_advancement`: PLAN-02, with its own 0.80 floor and binary-entropy ceiling.
- **Gate** (`providers/sys1/gating.py`). A decision passes only if:
  - calibrated confidence ≥ 0.85 (`DEFAULT_CONFIDENCE_FLOOR`);
  - the top-2 margin ≥ 0.40;
  - normalized entropy ≤ 0.35.
- **Fallback.**
  - **Review interpretation:** an ungated or unavailable System 1 decision falls through to the System 2 operation (`INTERPRET_*`).
  - **Activation:** ambiguity resolves to applying the protocol.
  - **Reviews:** unresolved intent never advances a stage (REVIEW-09/13/14).
- **Boundary routing environment** (System 1 recipe state only, never shown to System 2):
  - `PDLT_POLICY_SCOPE` (default `technical`);
  - `PDLT_SANDBOX_NETWORK` (default `false`);
  - `PDLT_KNOWLEDGE_CUTOFF` (default `2024-06`).

  No refusal is published without a gated System 1 decision. When System 1 is unavailable the request proceeds under the sandbox's limits.

## Divergence from the ADRs as written
- **ADR-0012 §2 (RLCD training), and Laya as a local model,** are not part of this repository; only the Jev API is used.
- **ADR-0020 decision 2 (pattern fast paths)** is superseded. `tests/test_harness_anti_overfitting.py::test_routing_recipes_have_no_pattern_matching` asserts no pattern matching. ADR-0020's latency figures are design targets, not measurements.

## Evidence
- **ADR-0012 threshold prior:**
  - Track P fidelity traces had mean true-positive probability 0.94 (σ 0.04);
  - F6 adversarial cases clustered at 0.62–0.82;
  - 0.85 sits about 2.25σ below the benign mean.
- **ADR-0017 (REG-008):** before System 1 was wired in, review gates cost 1.5–3.0 s and showed grammar rejections (session16) and dropped fields.
- **OpenRouter activity (2026-10-03):** Jev calls showed 118–141 ms TTFT and cost $0.000026–0.000054 per decision.

## Verification
`tests/test_sys1_foundation.py`, `tests/test_sys1_recipes.py`, `tests/test_sys1_worker_wiring.py`, `tests/test_harness_anti_overfitting.py`; `run_plan_gate.py` (live).

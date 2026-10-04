# IMPL-0009: Verification Plane: Witnesses, Checkers and Problem Domains

## Status
**Accepted.** Implements [ADR-0013](../0013-substantive-correctness-verification.md) (P2, P3, P5), [ADR-0015](../0015-model-synthesized-verification-and-confinement-boundaries.md) §1–2 and [ADR-0018](../0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md). Recorded 2026-10-03 from the 2.6.0rc1 code.

## Context
Requests that need a checkable answer are verified mechanically, from a structured witness the model's own program produces. The harness confines and checks; it never solves. This record holds the witness types, the checkers, domain dispatch and how code is found and run.

## Decision (as implemented)
- **Classification.** System 1's `problem_class` recipe decides `VERIFIED_EXECUTION` or `STANDARD_EXECUTION`, recorded as `PROBLEM_CLASS_CLASSIFIED`.
- **Domain dispatch.** The domain is a typed `ProblemDomain` (`verification/checkers/base.py`), and it has one member, `GENERAL`. The harness registers no problem-specific checkers (GUARD-02). `OutputVerifier.detect_domain` (`verification/output_verifier.py:37-60`):
  - accepts a typed domain or an explicit `domain` field;
  - otherwise it accepts only an exact enum string;
  - problem text is never searched for vocabulary.
- **Witnesses** (`runtime/wire_payloads.py`):
  - `PositiveWitness` carries the solution data;
  - `NegativeWitness` requires `search_exhausted: Literal[True]`, `nodes_explored: PositiveInt` and a `method`;
  - they form a discriminated union on `polarity`.
- **Witness from the sandbox.**
  - A program certifies a result by printing one line, `WITNESS: <json>`.
  - The host runs the deliverable as one program when the whole body parses as a Python module, and otherwise runs each ```python fenced block (`session_engine._python_blocks`, decided by grammar, not keywords).
  - The witness is the last one printed by a block that ran cleanly.
- **Checkers.**
  - Every witness is checked by `FallbackChecker` (`verification/checkers/fallback.py`): structural conformance, a complete certificate, and the result labelled provisional.
  - The witness the host reproduces by running the program is authoritative over one the model only asserts.
  - Ground-truth checks for catalogue prompts live in the evaluation plane (`graders.py`), never in the harness.
  - A failed verification goes through the bounded repair mechanism, and exhausting it yields an explicit unverified result.
- **No scraping.** No checker reads deliverable prose to build or recover a witness (GUARD-05). A missing or malformed witness fails closed.

## Divergence from the ADRs as written
- **ADR-0013 P0** (the plan must commit to code execution before `EXECUTE`) is not implemented. It conflicts with GUARD-03, under which derivations and proofs are first-class. The review-gate lint checks notation only (IMPL-0007).
- **ADR-0013 P4** (stored witness projected into the next turn's `REQUIRED_TASK_INPUTS`) is replaced by RS-09: the previous turn's request and result are passed as labelled reference only.
- **ADR-0015 §1 "canonical instructions compiled in-code".** The Result standard is read from the repository copy when present, with an in-code canonical fallback (`runtime/result_ir.py`).
- **ADR-0015 §3** cites a regressions log at `docs/governance/regressions-log.jsonl`. It does not exist; the live-verification rule lives in `AGENTS.md`.
- **ADR-0015 §2 (harness-resident domain checkers kept as calibration oracles)** and **ADR-0018 §3.1's domain enum values** (`PARTITION_SUM_TRIPLES`, `EXACT_COVER`, `SUBSET_SUM`) were removed under GUARD-02. The calibration role moved to the evaluation plane's graders.
- **ADR-0018 §3.3 (contradictory reconciliation by keyword)** is not implemented. It awaits a typed requirement kind.
- **ADR-0018 §3.4** described bare-code detection by primitives. The current rule is grammatical: the whole body parses as a module.

## Evidence
- **session9 (v2.4.0):** a correct "YES" on the Schur-triples instance, followed by a fabricated justification. The on-disk `result_ir` cited only `execution://body`.
- **session-20260929-063836 (REG-010):**
  - regex domain routing missed "divided into 15 disjoint triples";
  - a negative witness with `nodes_explored: 0` was accepted;
  - bare code was not extracted.

## Verification
- `tests/test_execution_phase.py`: witness rules, repairs, unverified closure.
- The checker tests.
- `tests/test_harness_anti_overfitting.py`: no deliverable scraping, no domain regex.

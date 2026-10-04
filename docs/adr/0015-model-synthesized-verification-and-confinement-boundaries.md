# ADR-0015: Model-Synthesized Verification and Confinement Boundaries in Ephemeral Sandboxes

- **Status:** Accepted (shipped in v2.5.0), amended.
  - **Harness-resident domain checkers have been removed (GUARD-02).** Ground-truth checking for the catalogue lives in the evaluation plane.
  - **Confinement is decided by [ADR-0021](0021-session-scoped-os-native-confinement.md).**
  - **The live-verification rule lives in `AGENTS.md`.** The regressions ledger named in §3 was never created.
- **Date:** 2026-09-27
- **Related:** [ADR-0011](0011-in-memory-vfs-and-microvm-sandboxing.md), [ADR-0013](0013-substantive-correctness-verification.md), [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md), [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md)
- **Implementation and evidence:** [IMPL-0009](impl/IMPL-0009-verification-witnesses-and-checkers.md), [IMPL-0010](impl/IMPL-0010-sandbox-backends-and-execution-budgets.md)

## Context

ADR-0013's verification pattern raised two risks:

1. **A runaway verifier library.** If the harness must hand-write a checker for every problem class, it stops being a protocol referee and becomes a hand-maintained solver library. Models are unreliable at combinatorial search in plain text, but reliable at writing short checkers for candidate solutions.
2. **Instructions read from the workspace.** Reading normative instructions from workspace paths failed outside the source tree, and let modified workspace files tamper with the instructions.

## Decision

1. **A clear division of responsibility.**
   - **The harness** provides confinement and invariants. It runs programs in a confined sandbox, validates the witness's structure, keeps the canonical normative instructions out of reach of workspace edits, and passes retained results forward without letting a turn invent a trace that does not exist.
   - **The model** writes both its solver and its own checker. Both run in the sandbox, and the model packages the result or the negative certificate as the witness.
2. **No domain verifier library in the harness.** Witnesses are checked structurally, with complete certificates, and labelled provisional. Gold-standard checking of known problems belongs to the evaluation plane, not the harness.
3. **Live verification before release.** Every completed pass is verified live in dev mode, across every stage, with no unhandled errors (`AGENTS.md`).

## Consequences

- The harness stays a substrate for the model's own problem solving, not an oracle library.
- The host runs in any workspace without copying harness files into it.
- Model-authored programs run only inside the confined sandbox.

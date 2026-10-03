# Architecture decision records

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](0001-controller-gated-pseudocode-protocol.md) | Accepted | Adopt the umbrella controller-gated pseudocode protocol. |
| [ADR-0002](0002-controller-owned-artifact-controls.md) | Accepted | Put artifact UI and deterministic branching in the host controller. |
| [ADR-0003](0003-phase-projected-single-model-contexts.md) | Accepted | Use controller-compiled phase contexts with one model as the core implementation. |
| [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md) | Accepted | Execute from a clean projection containing the confirmed pair and required task inputs. |
| [ADR-0005](0005-optional-result-pseudocode.md) | Accepted | Offer Result Pseudocode as an optional execution-output mode. |
| [ADR-0006](0006-bounded-pre-execution-reasoning.md) | Accepted | Limit pre-execution reasoning and avoid materially consequential guessing. |
| [ADR-0007](0007-operationalize-negative-constraints-by-omission.md) | Accepted | Operationalize negative constraints by omission. |
| [ADR-0008](0008-context-and-session-management.md) | Accepted | Separate normative store from dynamic zero-template session workspaces. |
| [ADR-0009](0009-result-pseudocode-decomposition-standard.md) | Accepted (prototype, feature-gated) | Require decomposed Result Pseudocode with mechanically validated evidence citations, chained across epochs. |
| [ADR-0010](0010-pydantic-wire-enforcement.md) | Accepted | Pydantic v2 schema enforcement and automated operator retry corrections for wire contracts. |
| [ADR-0011](0011-in-memory-vfs-and-microvm-sandboxing.md) | Accepted in part | Software-defined in-memory VFS context flow (implemented). The MicroVM and MCP sandboxing clauses were never implemented; see ADR-0021 and ADR-0025. |
| [ADR-0012](0012-system-1-decision-models-via-rlcd.md) | Accepted | Realign Track L to System 1 decision models (Laya/Jev) aligned via RLCD contrastive distillation. This repository uses Jev only; the training pipeline is not included. |
| [ADR-0013](0013-substantive-correctness-verification.md) | Accepted | Verified execution and bidirectional witness retention for substantive correctness. |
| [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md) | Accepted | Dual-plane boundary architecture: positive structural guidance, wire-level Pydantic contract enforcement, and tripartite clause governance. |
| [ADR-0015](0015-model-synthesized-verification-and-confinement-boundaries.md) | Accepted | Model-synthesized verification and confinement boundaries in ephemeral sandboxes. |
| [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md) | Accepted | Pydantic Single Source of Truth (SSOT) for wire and deliverable boundary enforcement. |
| [ADR-0017](0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md) | Accepted; Pillar 2 superseded by GUARD-01 and GUARD-04 | Dual-Plane Runtime Realignment: System 1 (Jev) Baseline & Constraint-Ordered Solver Governance. |
| [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md) | Accepted (§3.3 not implemented) | Elimination of Regex Heuristics in Substantive Verification & Reconciliation Semantic Integrity. |
| [ADR-0019](0019-headless-waiting-input-exit-and-wire-tolerance.md) | Accepted, amended | Headless WAITING_INPUT Exit Code & Execution Wire Input Tolerance; amended for refusals (exit 0), harness errors (exit 4) and interrupts (exit 130). |
| [ADR-0020](0020-system-1-environment-conditioned-refusal-routing.md) | Accepted, amended | System 1 Environment-Conditioned Boundary Interception & Immediate Refusal Routing; the pattern fast path is superseded, and no refusal is published without System 1. |
| [ADR-0021](0021-session-scoped-os-native-confinement.md) | Accepted | Session-scoped OS-native confinement (Landlock, Seatbelt, AppContainer, opt-in container), failing closed; supersedes ADR-0013's unenforced filesystem clause. |
| [ADR-0022](0022-default-reasoning-high-pre-execution.md) | Accepted | Default reasoning for gpt-oss: high before execution, low at EXECUTE, shared by live sessions and the catalogue runner; amends ADR-0006's model class matrix. |
| [ADR-0023](0023-taskmaster-host-interface-and-event-contract.md) | Proposed (future) | Taskmaster host interface and event contract: commands, live events, result envelope, approvals, budgets; presentation layers as pure clients. |
| [ADR-0024](0024-operation-profiles.md) | Proposed (future) | Operation profiles: reasoning depth, artifact length, verification depth and model routing as separate axes; provider capability descriptors; session budgets. |
| [ADR-0025](0025-agentic-capability-boundary.md) | Proposed (future) | Agentic capability boundary: effects as reviewed change sets, a tool broker with declared permissions, and a policy for agent workers. |
| [ADR-0026](0026-extension-and-workflow-model.md) | Proposed (future) | Extension and workflow model: closed core, versioned and validated contracts, workflow packs. |

The records are intentionally separated so UI, context construction, execution
isolation, output representation, and reasoning policy can evolve without
replacing the entire protocol decision.

**Status values.** *Accepted* records a decision in force; notes in the table and in each record say where the code differs. *Proposed (future)* records a direction that is **not implemented** in the current release; see [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md). Requirement documents cited by the early records (TRD-0001 to TRD-0003) are upstream documents that are not included in this repository.

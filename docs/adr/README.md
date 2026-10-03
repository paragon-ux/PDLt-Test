# Architecture decision records

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](0001-controller-gated-pseudocode-protocol.md) | Accepted | Adopt the umbrella controller-gated pseudocode protocol. |
| [ADR-0002](0002-controller-owned-artifact-controls.md) | Accepted | Put artifact UI and deterministic branching in the host controller. |
| [ADR-0003](0003-phase-projected-single-model-contexts.md) | Accepted | Use controller-compiled phase contexts with one model as the core implementation. |
| [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md) | Accepted | Execute from a clean projection containing the confirmed pair and required task inputs. |
| [ADR-0005](0005-optional-result-pseudocode.md) | Accepted | Offer Result Pseudocode as an optional execution-output mode. |
| [ADR-0006](0006-bounded-pre-execution-reasoning.md) | Accepted, amended | Limit pre-execution reasoning and avoid materially consequential guessing; reasoning is allocated per operation by intent (D25), with per-model values in IMPL-0004. |
| [ADR-0007](0007-operationalize-negative-constraints-by-omission.md) | Accepted | Operationalize negative constraints by omission. |
| [ADR-0008](0008-context-and-session-management.md) | Accepted | Separate a versioned normative store from on-demand workspaces; turns and invocations as a two-level hierarchy; confirmed deliverables chain across turns. IMPL-0005. |
| [ADR-0009](0009-result-pseudocode-decomposition-standard.md) | Accepted (prototype, feature-gated), amended | Execution emits a structured, evidence-cited result record, validated by the host; requirement IDs and forward chaining retired (RS-02, RS-03, RS-09). IMPL-0006. |
| [ADR-0010](0010-pydantic-wire-enforcement.md) | Accepted | Pydantic models are the schema authority for every operation's output, with field-level corrections; the prompt-side schema is completed by ADR-0028. IMPL-0007. |
| [ADR-0011](0011-in-memory-vfs-and-microvm-sandboxing.md) | Accepted in part | In-memory context flow (implemented); turn-boundary persistence (partial); microVM and MCP clauses never implemented, see ADR-0021 and ADR-0025. IMPL-0005. |
| [ADR-0012](0012-system-1-decision-models-via-rlcd.md) | Accepted | System 1 decision models govern activation and review behind a calibrated gate; the harness owns every transition. RLCD training is not in this repository. IMPL-0008. |
| [ADR-0013](0013-substantive-correctness-verification.md) | Accepted, amended | Verified execution with witnesses for both answers and bounded mechanical verification; P0 not in force (GUARD-03), P1 superseded by ADR-0021, P4 replaced by RS-09. IMPL-0009, IMPL-0010. |
| [ADR-0014](0014-dual-plane-boundary-and-wire-conformance.md) | Accepted, amended | Task plane separated from drafting discipline: positive guidance, checked never repaired, tripartite clause contract; notation enforced at the review gate. IMPL-0007. |
| [ADR-0015](0015-model-synthesized-verification-and-confinement-boundaries.md) | Accepted, amended | The harness confines and checks structure; the model writes its solver and checker; no domain verifier library in the harness (GUARD-02). IMPL-0009, IMPL-0010. |
| [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md) | Accepted | One Pydantic schema for the result record across every channel; structure is validated before semantics. IMPL-0006. |
| [ADR-0017](0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md) | Accepted, amended | System 1 as the governance baseline; Pillar 2 repealed (GUARD-01, GUARD-04); deferral meta-rules redrafted, never stripped; budgets supersede the fixed timeout. IMPL-0008. |
| [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md) | Accepted (§3.3 not implemented) | No pattern matching in verification: typed dispatch, strict certificates, intake by grammar, no deliverable scraping. IMPL-0009. |
| [ADR-0019](0019-headless-waiting-input-exit-and-wire-tolerance.md) | Accepted, amended | The headless exit contract (0, 1, 2, 3, 4, 130) and tolerant input requests; refusals exit 0. IMPL-0011. |
| [ADR-0020](0020-system-1-environment-conditioned-refusal-routing.md) | Accepted, amended | Boundary refusals decided by System 1 alone, conditioned on the declared environment; the pattern fast path is superseded. IMPL-0008. |
| [ADR-0021](0021-session-scoped-os-native-confinement.md) | Accepted | Session-scoped OS-native confinement, failing closed; supersedes ADR-0013's unenforced filesystem clause. IMPL-0010. |
| [ADR-0022](0022-default-reasoning-high-pre-execution.md) | Accepted | One effective reasoning configuration, resolved in one place, shared by live sessions and catalogue runs, and recorded; amends ADR-0006 D25. IMPL-0004. |
| [ADR-0023](0023-taskmaster-host-interface-and-event-contract.md) | Proposed (future) | Taskmaster host interface and event contract: commands, live events, result envelope, approvals, budgets; presentation layers as pure clients. |
| [ADR-0024](0024-operation-profiles.md) | Proposed (future) | Operation profiles: reasoning depth, artifact length, verification depth and model routing as separate axes; provider capability descriptors; session budgets. |
| [ADR-0025](0025-agentic-capability-boundary.md) | Proposed (future) | Agentic capability boundary: effects as reviewed change sets, a tool broker with declared permissions, and a policy for agent workers. |
| [ADR-0026](0026-extension-and-workflow-model.md) | Proposed (future) | Extension and workflow model: closed core, versioned and validated contracts, workflow packs. |
| [ADR-0027](0027-typed-task-entity-extraction.md) | Accepted (provisional) | Typed task entities for every problem type (surface, kind, the request's own definition), contained against the sanitized request. IMPL-0012. |
| [ADR-0028](0028-model-capability-boundary.md) | Proposed | Provider boundary: the protocol states what each operation needs; an adapter discovers each model's capabilities, translates, adjusts and reports; one output contract per operation; model specifics are data, not code. Implemented by IMPL-0001 to IMPL-0003. |

**Implementation records.** Decisions that carry out an ADR (modules, generators, provider endpoints, per-model values, and the evidence behind them) live in a separate set, [`impl/`](impl/README.md) (`IMPL-NNNN`), so this index stays at project scope.

The records are intentionally separated so UI, context construction, execution
isolation, output representation, and reasoning policy can evolve without
replacing the entire protocol decision.

**Status values.** *Accepted* records a decision in force; notes in the table and in each record say where the code differs. *Proposed (future)* records a direction that is **not implemented** in the current release; see [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md). Requirement documents cited by the early records (TRD-0001 to TRD-0003) are upstream documents that are not included in this repository.

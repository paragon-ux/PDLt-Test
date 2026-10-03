# ADR-0025: Agentic Capability Boundary

## Status
**Proposed.** Future work; not implemented in 2.6.0rc1. Date: 2026-10-02. Deciders: project maintainers.

- Direction: [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md) §4.3. Current behaviour: [`ARCHITECTURE.md`](../../ARCHITECTURE.md) §5.
- Builds on: [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md) (confirmed artifacts as the execution boundary) and [ADR-0021](0021-session-scoped-os-native-confinement.md) (OS-native confinement). Would supersede the capability and MCP clauses of [ADR-0011](0011-in-memory-vfs-and-microvm-sandboxing.md), which were never implemented. Depends on [ADR-0023](0023-taskmaster-host-interface-and-event-contract.md) (approvals and events) and, for tools, [ADR-0024](0024-operation-profiles.md) (capability routing).
- Requirements: `CAP-*` in `REQUIREMENTS.md` (planned; this section will list them).

## Context
PDLt confines model-authored code well (ADR-0021), but confinement is all it does. A program can compute and print inside a fresh run directory; everything it writes is deleted when the run ends. It cannot create or edit files in the user's project, change project state, run tools, or reach the network. The Result IR's `files` list names and grounds the deliverable's files, but nothing materializes them: the deliverable is text the user applies by hand.

That is safe, and it is enough for computing answers and witnesses. It is not enough for coding, research or general agent workflows, which the public release is expected to support. The question is where the capability boundary sits and how useful actions cross it without weakening containment.

Two further facts shape the decision:

- The protocol already has a review boundary: nothing substantive happens before the Prompt and Plan are confirmed (ADR-0004). New capabilities should enter through that boundary, not beside it.
- Some workers are agents themselves. The `codex` worker runs the Codex CLI with its own sandbox setting (`--worker-sandbox read-only|workspace-write`), which is a second, independent sandbox. If such a worker edits files with its own tools, PDLt's review gates and confinement are bypassed.

ADR-0011 named microVM sandboxing "strictly gated behind MCP", but no MCP capability layer exists and ADR-0021 records the microVM as roadmap.

## Decision
Define the boundary as **effects are reviewed artifacts**: model-authored code never gains write access to the user's project; it proposes effects, and the host applies approved effects.

1. **Declared project root.** A session may declare a project root and its access (none, read, propose-changes). The default is none, which is today's behaviour.
2. **Copy-on-write runs.** With propose-changes access, a sandbox run sees a copy-on-write view of the project root. Confinement is unchanged: the real project is never writable from the sandbox.
3. **Change sets.** After the run, the host computes the change set (files created, modified, deleted, as a diff). The change set is a protocol artifact: it is shown through an approval (ADR-0023), recorded, and verified like any deliverable.
4. **Host-applied effects.** Only the host applies an approved change set, and only to the declared root. Rejected change sets are discarded with the run.
5. **Tool broker.** Tools other than file changes (running a test command, fetching a URL, calling an external tool server) are requested through a broker. Each tool has a declared permission; the Plan states which tools the execution will use; the broker grants only declared tools, records every use as an event, and fails closed when a permission is missing.
6. **Capabilities are stated, not taught.** Model-facing text describes available capabilities only, as `AVAILABLE_EXECUTION_TOOLS` does today; it never suggests a method (`GUARD-01`, `GUARD-04`).
7. **Agent workers.** A worker that has its own tools is either restricted to model-only use (its own sandbox read-only and its edits ignored), or its tool use is routed through the broker. A worker's own sandbox never counts as PDLt's boundary.
8. **Environment honesty.** Declared capabilities come from what is enforced. For example, network access reported to System 1 must match what the sandbox and broker actually allow (today `PDLT_SANDBOX_NETWORK` is routing state only and can disagree with the sandbox).

### Incremental delivery
1. Materialize Result IR `files` as a proposed change set against a declared root, review it, and apply on approval (no copy-on-write runs yet).
2. Add copy-on-write project views to sandbox runs.
3. Add the tool broker with a first tool (running a declared test command inside the sandbox).
4. Define the agent-worker policy and enforce it for `codex`.
5. Derive the network and capability state given to System 1 from the broker and sandbox.

## Options considered

### A. Keep the current boundary (compute and print only)
| Dimension | Assessment |
|---|---|
| Safety | Strongest |
| Usefulness | Answers and witnesses only |
| Complexity | None |

**Pros:** nothing new to secure. **Cons:** no coding or agent workflows; users copy deliverables by hand.

### B. Give the sandbox write access to the project
| Dimension | Assessment |
|---|---|
| Safety | Weak: model code writes real files before any review |
| Usefulness | High |
| Complexity | Low |

**Pros:** simple. **Cons:** breaks the confirmed-artifact boundary; a bad run damages the project; contradicts ADR-0004 and ADR-0021.

### C. Expose tools to the model directly (for example raw MCP tools)
| Dimension | Assessment |
|---|---|
| Safety | Depends on each tool; effects happen before review |
| Usefulness | High |
| Complexity | Medium |

**Pros:** a large tool ecosystem. **Cons:** effects bypass the review gates; permissions are per tool, not per plan; hard to audit.

### D. Effects as reviewed change sets plus a tool broker (chosen)
| Dimension | Assessment |
|---|---|
| Safety | Sandbox stays read-only to the project; effects are reviewed before they happen |
| Usefulness | Coding and agent workflows become possible |
| Complexity | Medium to high |

**Pros:** keeps the protocol's core promise (nothing happens that was not reviewed) while enabling real work; every effect is auditable. **Cons:** copy-on-write views and diffing must be implemented per platform; large change sets need a usable review experience.

## Consequences
- **Easier:** coding and file-producing workflows; auditing every effect; a clear answer to what the sandbox may do.
- **Harder:** per-platform copy-on-write support; presenting large diffs for review.
- **Unchanged:** confinement backends, fail-closed behaviour and the guardrails. With no declared project root, behaviour is exactly today's.
- **Revisit:** whether some change kinds may be pre-approved by policy (TARGET_ARCHITECTURE §8), and whether a stronger isolation mechanism (container or microVM) should be required for propose-changes access.

## Out of scope
Choice of virtualization technology; the approval transport (ADR-0023); tool selection by model capability (ADR-0024); packaging tool grants in workflow packs (ADR-0026).

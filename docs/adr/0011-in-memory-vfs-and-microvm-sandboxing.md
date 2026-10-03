# ADR-0011: Software-Defined In-Memory VFS and Ephemeral MicroVM Sandboxing

- Status: Accepted in part.
  - Decision 1 is implemented.
  - Decision 2 is implemented partially: a per-turn archive is written, and stage files are still written without synchronous flushes ([IMPL-0005](impl/IMPL-0005-normative-store-and-workspace-layout.md)).
  - Decisions 3–4 (microVM sandboxing, MCP capability boundary) were never implemented. Execution confinement is decided by [ADR-0021](0021-session-scoped-os-native-confinement.md), and the capability boundary is proposed in [ADR-0025](0025-agentic-capability-boundary.md), which would supersede them.
- Date: 2026-09-26
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related decisions: [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md), [ADR-0008](0008-context-and-session-management.md), [ADR-0010](0010-pydantic-wire-enforcement.md)
- Related requirements: TRD-0002 (upstream document, not included in this repository)

## Context

ADR-0008 removed template duplication, but the context flow between stages was still tied to disk. Synchronous, journaled writes for every stage file made each turn wait on I/O, especially on Windows. Large evaluation batteries created very many small files. Separately, running model-generated code on the bare host was a security risk.

## Decision drivers

- Remove blocking file-system latency from the active turn.
- Keep stage isolation, verifiable handoffs and deterministic replay.
- Avoid creating large numbers of transient files.
- Run untrusted code in an isolated, ephemeral environment.
- Mediate tool and file access through a typed capability boundary.

## Decision

1. **In-memory context flow.** A turn's stages, inputs, outputs, projections and events live in memory while the turn is active. Replay hashes are computed from the in-memory content, and nothing waits on synchronous disk flushes.
2. **Persistence at turn boundaries.** A turn is persisted as one record when it completes or is cancelled. Intermediate steps are not separately persisted, unless explicitly requested for debugging.
3. **Ephemeral isolated execution.** Untrusted code runs in a disposable sandbox that leaves nothing behind on the host. *(Not implemented as specified; see ADR-0021.)*
4. **A typed capability boundary.** Sandboxed code reaches files and tools only through typed, monitored endpoints; anything outside the confirmed task is rejected. *(Not implemented; see ADR-0025.)*

## Consequences

### Positive
- A turn no longer waits on synchronous disk writes.
- Far fewer files are created.
- Isolation of untrusted code becomes a design requirement rather than an afterthought.

### Neutral / Negative
- An in-memory layer must be kept alongside disk serialization for inspection and tests.
- Strong isolation requires a runtime backend: a microVM, a container or an OS-native sandbox (ADR-0021).

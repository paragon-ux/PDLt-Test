# ADR-0008: Context, session, and normative storage architecture

- Status: Accepted
- Date: 2026-09-17
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related decisions: [ADR-0002](0002-controller-owned-artifact-controls.md), [ADR-0003](0003-phase-projected-single-model-contexts.md), [ADR-0004](0004-confirmed-artifacts-as-execution-boundary.md), [ADR-0007](0007-operationalize-negative-constraints-by-omission.md)
- Related requirements: TRD-0002 (upstream document, not included in this repository)
- Implementation, paths and evidence: [IMPL-0005](impl/IMPL-0005-normative-store-and-workspace-layout.md)

## Context

The protocol needs strict isolation across stages, evaluation runs and interactive sessions. As it scaled to multi-turn use and large test batteries, three problems appeared:

1. **Duplicated scaffolding.** Copying a full workspace template for every invocation produced large numbers of redundant files and slowed file-system access, especially on Windows.
2. **Blurred task boundaries.** Without a formal separation between a session and the tasks inside it, rejected drafts and conversation from one task could leak into the next or muddy its audit record.
3. **Standards tied to one checkout.** Protocol standards, contracts and schemas had to stay identical and verifiable across checkouts, CI, monorepo subtrees and scratch directories, without depending on a particular repository root.

## Decision drivers

- No static duplication when a workspace starts.
- A clear lifecycle that separates the session from each task.
- ADR-0004's execution boundary held across turns: confirmed deliverables chain forward, drafting history does not.
- Standards decoupled from any project directory, with deterministic replay.
- The same behaviour on Windows and POSIX file systems.

## Decision

### 1. A normative store
The canonical standards, contracts and schemas live in a store that is versioned and resolved independently of any project.
- A project may pin the version it uses.
- Replay determinism comes from hashing the clause content, not file paths.
- An installed version is immutable.

### 2. Workspaces created on demand
Workspaces start empty. A stage's inputs and outputs are created only when an operation runs, and current artifacts and an append-only event log record each stage.

### 3. A two-level session hierarchy
- **A task epoch (turn)** is one protocol cycle, from the user's instruction through both reviews to completion or cancellation. Each turn owns its stages, controller state and event log.
- **Invocations** are the reviews, clarifications and corrections within a turn. They are numbered inside that turn and recorded individually, without splitting it.

### 4. Cross-turn deliverable chaining
A new task in the same session starts a new turn. It receives the previous turn's confirmed deliverable as clean background input, per ADR-0004. Drafts, rejected plans and negotiation from earlier turns are excluded.

## Consequences

### Positive

- Starting a workspace creates no template files.
- Turns are hermetic: earlier drafts cannot contaminate later tasks.
- Standards are shared across projects without copies in each repository.
- Every task has a self-contained, reproducible record.

### Negative

- The hierarchy creates deep paths, so name components must stay short for Windows path limits.
- Offline environments without a bundled fallback need the store provisioned in advance.

## Alternatives considered

### Standards stored in each project repository
Rejected. It duplicates files across projects and branches, and rules out scratch directories and non-git workspaces.

### Flat, single-level session directories
Rejected. Drafts from different tasks would intermingle, which complicates replay and risks context leaking across tasks.

### Copy-on-write file-system templates
Rejected. It needs OS-specific mechanisms that fail or need elevated privileges on Windows. Creating directories on demand is portable.

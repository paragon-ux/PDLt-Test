# ADR-0021: Session-Scoped OS-Native Confinement

## Status
Accepted. Supersedes the filesystem clause of ADR-0013 P1 ("file writes strictly restricted to an ephemeral scratchpad directory"), which no code enforced. Backends, layout, budgets and platform notes: [IMPL-0010](impl/IMPL-0010-sandbox-backends-and-execution-budgets.md). User guide: [`docs/SANDBOX.md`](../SANDBOX.md).

## Context
Model-authored programs ran in a fresh interpreter, with resource limits, an environment allowlist and an in-process audit hook. Nothing confined the file system: a program could read and write any file the user could, including secrets, the repository and other sessions' workspaces. A native-code escape gets past any audit hook.

Two facts constrain where a program may write:
- **The referee reads by search.** It searches session and result trees for deliverables, events and evidence. A model-writable directory inside those trees could plant a deliverable or evidence.
- **Workspaces are not stable anchors.** One session can span several workspaces.

The harness also keeps its zero third-party dependency rule.

## Decision
1. **One sandbox per session.** It is created on first use, outside every tree the referee reads, and recorded in the session's events. The host releases it on every exit path. Sandboxes left by dead processes are swept later, not on interpreter exit.
2. **A fresh, empty directory per program.** Nothing from one run is visible to the next.
3. **One policy per session:**
   - write only the run directory;
   - read only the run directory, the base interpreter's installation, and what the OS loader needs;
   - execute only the base interpreter;
   - no network, and no new processes.
4. **OS-native confinement on every supported platform,** using only the standard library and the OS's own mechanisms.
   - An opt-in container mode is offered for stronger isolation.
   - An explicit opt-out (audit hook and limits only) exists, and the host warns loudly when it is used.
5. **Fail closed.** If the selected confinement cannot apply, no program runs. The host says so, records a finding, and spends no repair on it.
6. **The audit hook stays, as defense in depth.** It is built from the same policy.
7. **Model-facing text states capabilities only** (GUARD-01/02): what a program may and may not do, never how to solve the task.

## Consequences
- **Positive:** a program cannot read the user's secrets or the repository, nor write deliverables, evidence or another session's files, even with the audit hook defeated. An escape suite checks every backend with the hook on and off.
- **Positive:** native confinement adds no measurable cost per run on Linux. The container mode costs more per session and per run.
- **Negative:** each platform mechanism has its own gaps and requirements (kernel versions, protocols not covered, interpreter installations that cannot be confined). Each fails closed and is documented in IMPL-0010.
- **Neutral:** this is not a VM boundary. Side channels and kernel exploits are out of scope; the container mode exists for stronger isolation, and a microVM (ADR-0011) remains roadmap.

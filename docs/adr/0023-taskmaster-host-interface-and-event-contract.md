# ADR-0023: Taskmaster Host Interface and Event Contract

## Status
**Proposed.** Future work; not implemented in 2.6.0rc1. Date: 2026-10-02. Deciders: project maintainers.

- Direction: [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md) §4.1. Current behaviour: [`ARCHITECTURE.md`](../../ARCHITECTURE.md) §2, §3.4, §8.
- Related: [ADR-0002](0002-controller-owned-artifact-controls.md) (controller-owned artifact controls), [ADR-0019](0019-headless-waiting-input-exit-and-wire-tolerance.md) (headless exit codes). Prerequisite for [ADR-0025](0025-agentic-capability-boundary.md) and [ADR-0026](0026-extension-and-workflow-model.md).
- Requirements: `HOST-*` in `REQUIREMENTS.md` (planned; this section will list them).

## Context
PDLt is used today through one client: the terminal REPL in `host/repl.py`. Headless callers, including the catalogue runner, pipe text into stdin, read text from stdout and interpret an exit code. The public release will also be used as a subagent of another agent, as several taskmasters run in parallel, by a person guiding an agent, through subscription workers, and with local models.

The inside of the system is already well separated:

- `SessionEngine` never reads stdin or prints; all terminal I/O is in `repl.py`.
- `PDLtHost.handle(user_message) -> HostTurn` is a per-turn API with a text, a closure flag and a controller snapshot.
- Each session owns its sandbox and workspace, so separate processes do not share protocol state.

The gaps are at the boundary:

1. **Results are text.** A caller must parse prose to learn the deliverable, the witness and whether it was verified. Only the exit code is structured.
2. **Review gates are prose prompts.** A caller answers them by sending `/confirm` text. Headless scripts confirm blindly, and mismatches between the script and the gates have produced defects (before 2.6.0rc1, `/confirm` lines left over after closure restarted the closed task).
3. **No live events.** Observation records (`observation/observed_session.py`) are written when a turn completes; in-turn progress goes to a log file. A presentation layer cannot show what is happening now: which operation is running, what the sandbox is doing, what is waiting for approval.
4. **No session budget.** Each model call has a deadline; a session does not, so a caller cannot bound a subagent's time or tokens (ADR-0024 defines the budgets; this contract carries them).
5. **No capability report.** A caller cannot ask what this host can do here: which sandbox mode applies, whether System 1 is reachable, which providers are configured.

A TUI would make the system more trustworthy to use, but without these the TUI would have to scrape the same text a subagent does.

## Decision
Define a versioned **host contract** that every client uses, and make the REPL one client of it.

1. **Commands.** A session accepts: `submit(request)`, `approve(approval_id, decision, feedback?)`, `supply_input(input)`, `status()`, `cancel()`, `close()`. Commands request transitions; the controller decides them.
2. **Events.** A session emits typed events while it works, at least: session started (with the environment report), stage changed, model call started and finished (operation, model, usage, latency), sandbox run started and finished, approval requested and resolved, verification verdict, budget warning, closed. Events are append-only and carry a session ID and sequence number. Events are emitted live, during a turn.
3. **Result envelope.** Every closure produces one structured result: final stage, closure kind (success, refused, cancelled, waiting for input, error), deliverable, witness with verification status (sandbox-reproduced or provisional), usage, and the exit code it maps to (ADR-0019).
4. **Approvals.** Review gates become approval objects naming the artifact under review, the allowed decisions, and who may answer. A session declares its approval policy at start: `human` (default), `caller` (the invoking agent answers through `approve`), or a named pre-approval policy. Today's piped `/confirm` is the `caller` policy expressed in text. Unanswered approvals behave as today: the session halts at the gate.
5. **Environment report.** The first event states the sandbox mode and whether it is available, System 1 availability, the configured providers and their capabilities (ADR-0024), and the contract version.
6. **Presentation separation.** A presentation layer (REPL, TUI, web view) only renders events and issues commands. It holds no protocol state and cannot change protocol semantics.
7. **Transports.** The contract is transport-neutral. Planned bindings, in order: in-process Python API; JSONL over stdio for headless and subagent use; an agent-facing server (for example MCP). The text REPL stays the default interactive client.

### Incremental delivery
1. Emit live events from the existing engine and host, recorded beside today's observation records.
2. Add the result envelope and a `--output jsonl` headless mode; the exit codes are unchanged.
3. Introduce approval objects and approval policies; the REPL renders them as today's prompts.
4. Add the environment report and budget fields once ADR-0024 defines them.
5. Build further clients (TUI, agent server) on the contract.

## Options considered

### A. Keep the text REPL as the only interface
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Parity across uses | Poor: every integration parses text |
| Trust and observability | Limited to printed telemetry |

**Pros:** no new surface to maintain. **Cons:** every agent integration reimplements gate driving and result parsing; gate-script mismatches recur; a TUI must scrape text.

### B. Add a TUI directly on the REPL
| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Parity across uses | Unchanged for non-terminal uses |
| Trust and observability | Better for terminal users only |

**Pros:** visible improvement quickly. **Cons:** couples presentation to the REPL's internals, does nothing for subagents or parallel use, and still lacks live events.

### C. Host contract with events, results and approvals (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium; formalizes the existing `PDLtHost` seam |
| Parity across uses | One contract for terminal, headless, subagent and parallel use |
| Trust and observability | Live events serve the REPL, a TUI and callers alike |

**Pros:** one semantics for every client; presentation is replaceable; review delegation becomes explicit. **Cons:** a versioned public interface to maintain; event and envelope schemas need care to stay stable.

## Consequences
- **Easier:** subagent and parallel use, a TUI as a pure client, delegated review, testing clients against recorded event streams.
- **Harder:** the contract is a compatibility surface; changes need versioning.
- **Unchanged:** stage semantics, review-gate rules, exit codes and guardrails. The REPL keeps working as it does today throughout the incremental steps.
- **Revisit:** which agent transport to ship first (TARGET_ARCHITECTURE §8).

## Out of scope
Operation profiles and budget values (ADR-0024), the change-set approval flow (ADR-0025), and extension points (ADR-0026). The TUI's visual design is an implementation matter, not an architectural one.

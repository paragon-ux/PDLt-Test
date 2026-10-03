# PDL Taskmaster: Target Architecture

**Status:** Direction, not implementation. Nothing in this document exists in 2.6.0rc1 unless the "Today" column says so.
**Current architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) describes what runs today.
**Decisions:** [ADR-0023](docs/adr/0023-taskmaster-host-interface-and-event-contract.md), [ADR-0024](docs/adr/0024-operation-profiles.md), [ADR-0025](docs/adr/0025-agentic-capability-boundary.md) and [ADR-0026](docs/adr/0026-extension-and-workflow-model.md), all **Proposed**.
**Source:** the architecture review of 2026-10-02, which examined token cost, sandbox capability, extensibility, deployment parity and interface trust before the first public release.

---

## 1. Why a target architecture

PDL Taskmaster 2.6.0rc1 is a working protocol referee for one main use: a person at a terminal, or a headless runner, driving one task at a time against an OpenRouter model. The public release will be used in more ways than that: as a subagent of another agent, several taskmasters in parallel, through subscription workers such as Codex or Claude, against local models, and for workflows beyond the benchmark (research, coding, mathematics, writing, Q&A). Several assumptions in the current design only hold for the terminal case.

This document fixes the direction so that future work is incremental and consistent. It is deliberately high level. The work is traced in this order:

```
TARGET_ARCHITECTURE.md  →  REQUIREMENTS.md (planned)  →  ADR-0023 … ADR-0026  →  implementation
```

`REQUIREMENTS.md` does not exist yet. It will hold the concrete, testable requirements derived from §4; each requirement will name the ADR that addresses it, and each ADR will list its requirements. The ADRs reserve requirement ID prefixes for this (§6).

---

## 2. What does not change

The target architecture extends the current one; it does not replace its core. These hold in every target state:

1. **The referee invariant.** The harness governs the protocol and never solves the task: no algorithmic coaching, no keyword gates, no fabricated witnesses (`GUARD-01` to `GUARD-05`).
2. **Confirmed artifacts are the execution boundary** (ADR-0004). Nothing substantive happens before the Prompt and the Plan are confirmed, and every new capability (file changes, tools) enters through a reviewed artifact, never around one.
3. **The controller owns state.** Every stage transition is decided by `MechanicalController`; clients, models and extensions request transitions and never perform them.
4. **Containment fails closed.** When a confinement or capability cannot be applied, the action does not run.
5. **Two planes.** The harness never knows the benchmark; the evaluation plane drives and grades it.

---

## 3. Today and target

| Area | Today (2.6.0rc1) | Target | ADR |
|---|---|---|---|
| **Client interface** | A terminal REPL. Headless callers pipe text into stdin and read text and an exit code. Review gates are prose. `PDLtHost.handle()` is a clean per-turn API, but it is internal. | A versioned host contract: commands, a typed live event stream, a structured result envelope, review gates as approval objects that a human, a calling agent or a declared policy can answer, and an environment report. The REPL, a TUI, a JSONL headless mode and an agent-facing server are all clients of it. | 0023 |
| **Observability** | Per-turn JSONL records written after the turn completes; in-turn progress goes to a log file; dev telemetry is printed text. | Live events for stage changes, model calls, sandbox and tool actions, pending approvals and verification verdicts, consumed by any presentation layer. | 0023 |
| **Cost and latency** | Reasoning effort per model family is hardcoded (ADR-0022); model, reasoning and token caps are separate flags; repairs scale with the routed tier; each call has a deadline, the session has none. | Operation profiles that set reasoning depth, artifact length, verification depth and model routing as separate, declared axes; provider capability descriptors; session time and token budgets with an explicit unverified closure when a budget ends verification. | 0024 |
| **System 1 dependency** | System 1 is OpenRouter's remote decisions endpoint. Without it, no boundary refusal runs and routing falls back to defaults. | System 1 is a declared capability like any other provider; each deployment states, and the session reports, what happens to boundary routing when it is absent. | 0024 |
| **Agentic capability** | Programs compute and print inside a per-run directory that is deleted afterwards. Nothing is written to the user's project; the Result IR's `files` list is descriptive. No tools. | Effects as reviewed change sets: programs run against a copy-on-write view of a declared project root, the host turns their effect into a diff, the diff is reviewed like any artifact, and only the host applies it. Other tools run through a broker with declared, visible permissions. | 0025 |
| **Agent workers** | `codex` runs the Codex CLI with its own sandbox setting (`--worker-sandbox`), separate from PDLt's sandbox. | Workers that are themselves agents are either constrained to model-only use or their tool use is routed through the same broker and review gates. | 0025 |
| **Customization** | Contracts can be overridden by directory precedence, which replaces the whole set and checks structure only. Operation prompts are Python strings. No packaging for workflows. | A closed core, versioned and validated contracts, and workflow packs (research, coding, mathematics, writing, Q&A, general) that bundle a profile, capability grants, checkers and prompt fragments as data, can tighten but never loosen core guarantees, and pass a conformance kit. | 0026 |

---

## 4. Target structure

```
┌──────────────────────────────── Clients ────────────────────────────────┐
│  REPL (text)   TUI (future)   headless JSONL   agent server (e.g. MCP)  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │  commands ↓   events, results ↑
┌───────────────────────────────────▼─────────────────────────────────────┐
│  Host contract (ADR-0023): sessions, commands, approvals, budgets,      │
│  environment report. Presentation never owns protocol state.            │
└───────────────────────────────────┬─────────────────────────────────────┘
┌───────────────────────────────────▼─────────────────────────────────────┐
│  Protocol core (closed): SessionEngine, MechanicalController, wire      │
│  schemas, verifier, guardrails. Unchanged in kind.                      │
└──────┬──────────────────────────────┬───────────────────────────┬───────┘
       │                              │                           │
┌──────▼──────────────┐   ┌───────────▼────────────┐   ┌──────────▼─────────┐
│ Operation profiles  │   │ Capability boundary    │   │ Extension layer    │
│ (ADR-0024): routing │   │ (ADR-0025): sandbox,   │   │ (ADR-0026):        │
│ to providers by     │   │ reviewed change sets,  │   │ versioned contracts│
│ capability; budgets │   │ tool broker            │   │ and workflow packs │
└──────┬──────────────┘   └────────────────────────┘   └────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│  Providers with capability descriptors: System 1, System 2 (remote,     │
│  local, subscription), recorded replay                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Host contract (ADR-0023)

Every way of using PDLt goes through one contract. A session accepts a small set of commands (submit a request, answer an approval, supply requested input, ask for status, close), emits typed events while it works, and ends with a result envelope that states the stage, the closure, the deliverable, the witness and its verification status, and usage. Review gates become approval objects that carry what is being approved and who may approve it. The REPL becomes one renderer of this contract, so a TUI or an agent integration needs no change to protocol semantics.

### 4.2 Operation profiles (ADR-0024)

Four concerns that are entangled today become separate axes:

- **Reasoning depth:** hidden reasoning a model spends per operation.
- **Artifact length:** the visible Prompt, Plan, Result IR and witness the protocol requires.
- **Verification depth:** whether a witness is required, and how many repairs are allowed.
- **Model routing:** which provider and model serve each operation, chosen by declared capability (structured output, reasoning control, throughput, locality) rather than by name.

A profile (for example fast, balanced or verified) sets these together, and a session budget bounds time and tokens, closing explicitly as unverified rather than repairing without end.

### 4.3 Capability boundary (ADR-0025)

The sandbox stays the place where untrusted code runs. What changes is that a run can have a reviewed effect: the run sees a copy-on-write view of a declared project root, the host computes the resulting change set, the change set is reviewed like the Prompt and the Plan, and the host alone applies it. Tools other than file changes run through a broker that grants declared permissions, shows them in the plan and the event stream, and records every use.

### 4.4 Extension model (ADR-0026)

Three tiers, each with its own change process:

- **Core (closed):** controller, gates, wire schemas, confinement and the guardrails. Changed only by ADR.
- **Contracts (versioned):** standards and contracts declare the core versions they support and are validated at load, with layered overrides rather than wholesale replacement.
- **Workflow packs (open):** named, schema-validated bundles for a kind of work. A pack is user-originated content; packs shipped with PDLt pass the same integrity gate as the harness.

---

## 5. Evidence behind the direction

**Output tokens and latency.** From 762 recorded catalogue sessions on `openai/gpt-oss-120b` (`catalogue-runs/`, 2026-10-02):

| | Output tokens per session | Model time per session |
|---|---|---|
| Median | about 3.1k | about 8 s |
| 90th percentile | about 11.7k | about 31 s |
| Worst | about 138k | about 888 s |

| EXECUTE calls in the session | Sessions | Median output | Median model time |
|---|---|---|---|
| 1 (no repair) | 581 | about 3.1k | about 8 s |
| 2 | 87 | about 4.0k | about 26 s |
| 3 or more | 26 | about 11.4k | about 66 s |

- 11% of sessions took more than 30 s of model time, and 56 of those 82 involved at least one verification repair: the slow tail comes from verification and repair, not from long answers.
- The three pre-execution operations produce a median 62% of a session's output tokens. At the ADR-0022 default (high reasoning before execution), a trivial request spends about 3.6k output tokens before execution, 89% of them hidden reasoning.
- `EXECUTE` itself is about 4% reasoning; its output is the deliverable.

This is why ADR-0024 treats cost as latency and capability fit (whether a fast provider is usable at all), not only as money, and why it separates verification depth from reasoning depth.

**Deployment parity.** The engine has no terminal I/O and `PDLtHost.handle()` is already a per-turn API, so the host contract formalizes an existing seam rather than restructuring the engine. The gaps are on the outside: text-only results, prose review gates, no live events, no session budget, a remote-only System 1, and OpenRouter-specific provider routing.

---

## 6. Sequencing

1. **ADR-0023 first.** Approval objects, events and the result envelope are prerequisites for the TUI, agent integrations, delegated review and the reviewed change sets of ADR-0025.
2. **ADR-0024 and ADR-0025 next, in either order.** Tool-using operations need capability-aware routing, so ADR-0025's tool broker depends on ADR-0024's provider descriptors; its change-set review depends only on ADR-0023.
3. **ADR-0026 last.** A workflow pack bundles a profile (ADR-0024), capability grants (ADR-0025) and presentation hints (ADR-0023), so those seams must exist first.

Requirement ID prefixes reserved for `REQUIREMENTS.md`: `HOST-` (ADR-0023), `PROF-` (ADR-0024), `CAP-` (ADR-0025), `EXT-` (ADR-0026).

---

## 7. Non-goals

- PDLt does not become an autonomous agent that acts without review: every new capability is reviewed through the protocol.
- A TUI is a presentation layer; it never changes REPL or protocol semantics.
- No commitment to a specific virtualization technology. The microVM in ADR-0011 stays exploratory; ADR-0025 defines the boundary, not the mechanism.
- No change to how the catalogue is scored.

## 8. Open questions

- Should boundary routing fail closed (refuse) or open (proceed without refusal) when System 1 is unavailable, and is that a per-deployment setting? (ADR-0024)
- Which agent-facing transport comes first: an MCP server, a JSONL stdio protocol, or both? (ADR-0023)
- How are reviewed change sets presented for large diffs, and can a policy pre-approve some kinds of change? (ADR-0023, ADR-0025)
- How is a user-authored pack's methodological content recorded, so that it is clearly user-originated under `GUARD-01`? (ADR-0026)

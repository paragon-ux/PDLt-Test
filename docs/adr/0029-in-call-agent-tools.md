# ADR-0029: In-Call Agent Tools: Validated Submission and Sandbox Inspection

## Status
**Proposed.** Date: 2026-10-10. Deciders: project maintainers.

- Amends [ADR-0025](0025-agentic-capability-boundary.md): a tool with no effect outside the confined sandbox, used inside one model call, is not an effect and does not go through the tool broker or a change set. The broker stays the route for every tool with an effect.
- Amends the worker premise in `worker-bootstrap.txt` ("The supplied projection is the complete invocation for this call") for the operations that get tools: the projection stays the complete statement of the task; tool results are inspection inside the call, never new task content.
- Keeps [ADR-0018](0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md) (the submission is checked by the Pydantic wire model), [ADR-0019](0019-headless-waiting-input-exit-and-wire-tolerance.md) (exit codes unchanged) and [ADR-0021](0021-session-scoped-os-native-confinement.md) (every program runs in the same confined sandbox).
- Evidence: ledger L111 and L112, `docs/plans/TOOL_LOOP_MCP_EVAL.md`, `docs/plans/TOOL_EXTRACTION_PLAN.md`, `docs/plans/PASS_RATE_TRACKER.md`.

## Context
The worker is stateless and commits blind. On EXECUTE_UNCONFIRMED it cannot run its program before committing, cannot see the program it is repairing, and learns the host's rules (how programs are extracted from the body, the step budget, the WITNESS line) only from a correction after a counted attempt. Of 2,423 recorded EXECUTE calls, 381 were corrected after the fact (PROGRAM_FAILED 190, WITNESS_NOT_PRINTED 153, STEP_BUDGET_EXCEEDED 134).

Measured in the evaluation plane (all live, gpt-oss-120b on Cerebras through OpenRouter):
- **Frozen 01-01 repairs** (12 recorded failures x 3): host-verified success 15/36 with the best repair-text variant; 11/35 with inspection tools alone; 22/31 once the loop ended in a validated submission; 31/36 after L110.
- **Full 01-01 runs**, the loop on every EXECUTE_UNCONFIRMED call: 18/18, against 5/10 and 3/10 in the recorded full runs before it (historical). No host-side failure reached a repair: the submission check caught them inside the call.
- **Code tasks without a witness** (04-02, 04-03, full runs): no measurable change against the recorded rates.
- **Submit loops on other operations** (checked submission only, no work tools): on BOOTSTRAP_ANALYSIS it saved nothing, because the one wire retry already recovered every schema failure (5 of 83), and on 04-03 the replies were about 20% shorter with fewer literal entities, without a lower pass rate (L112 step 3); on DRAFT_PROMPT and DRAFT_PLAN with the PDL lint it cut the engine's lint redrafts from 13 to 5 with no outcome change and more provider rounds, lint not being on the failure path (L112 step 4). Adopted all the same (the user's decision, 2026-10-10: no reason to exclude a loop). A scratchpad kept across attempts was never used (0 notes in 9 runs) and is not adopted.

Provider fact: Cerebras rejects `tools` together with `response_format`, so a tool turn cannot carry the operation's output format. A submission made as a tool call carries the output schema in its parameters instead.

## Decision
1. **A registry of in-call tools per operation.** EXECUTE_UNCONFIRMED: `run_python`, `read_attempt` (only when there is a previous attempt) and `submit_execute_unconfirmed`. BOOTSTRAP_ANALYSIS, DRAFT_PROMPT and DRAFT_PLAN: their submission only (`submit_bootstrap_analysis`, `submit_draft_prompt`, `submit_draft_plan`). Work tools only where the host can run something; no other operation has tools.
2. **The submission is the only way a loop ends with an accepted reply.** It is checked by the checks the host already runs after the call, and only those: the operation bridge's Pydantic parse; for EXECUTE_UNCONFIRMED the deliverable's programs run as the host will run them, at the attempt's budget; for a draft the pseudocode notation lint (`plan_soundness`). The host still runs its own post-call checks on the accepted reply. Every error comes back at once, in one envelope (`ok`, `errors` with `code`, `path`, `problem`, `expected`, `facts`). At most 3 submissions.
3. **No verdict tool.** Submission checks are structural. The host verifies the accepted reply itself, in its own sandbox run, exactly as it verifies a reply today. Tool output is never evidence and never reaches the deliverable or the protocol state.
4. **Inspection only.** `run_python` runs in the session's confined sandbox under the attempt's limits; it has no network, no project access and no effect that outlives the run. `read_attempt` returns the previous attempt's programs as the host ran them, numbered, with the host's correction.
5. **Capabilities are stated, not taught** (ADR-0025 §6, GUARD-01). Tool descriptions and the capability note say what each tool does and its budget; they never suggest a method.
6. **Budgets and records.** At most 6 calls of `run_python` and `read_attempt` per model call. Every tool call and submission is an event and is written to the call trace.
7. **Off by default.** A run setting (`agent_tools`, CLI `--agent-tools`, environment `PDLT_AGENT_TOOLS=1`) turns the loop on. With it off, every request is byte-identical to today's.
8. **Provider handling.** Tool turns carry the tools and no response format; when the provider refuses the full output schema in the submission's parameters, the submission falls back to a plain object, still checked by the host. When the budgets are spent, the last submission stands as the reply (the host verifies and corrects it as any reply); with no submission, one final call goes with the operation's own format and no tools.
9. **Replay.** The prompt hash is taken before the loop; a recorded replay returns the accepted reply. Loop rounds are recorded in the trace, not replayed.
10. **MCP.** EXECUTE_UNCONFIRMED's tools (`run_python` and its checked submission) are served over MCP's stdio transport for agents outside PDLt (`python -m pdl_taskmaster.host.mcp_server`; ADR-0023 section 7): a thin adapter with the same definitions, budgets, sandbox confinement and submission check, and no verdict.

## Options considered

### A. Keep correcting after the call
**Pros:** no new mechanism. **Cons:** every class-B failure costs a counted attempt; measured repair success stayed at 33–42% across four repair-text variants (L107, L109).

### B. In-call tools for every operation at once
**Pros:** one mechanism everywhere. **Cons:** unmeasured where the host has nothing to check before acceptance; the BOOTSTRAP measurement showed no benefit and an extraction signal.

### C. In-call inspection and a validated submission, per operation, behind a setting (chosen)
**Pros:** removes the measured failure classes on EXECUTE_UNCONFIRMED; one pattern on every operation the host checks; reuses the host's checks; no new rule; off by default. **Cons:** more provider rounds per call; the worker becomes stateful within one call.

### D. Expose the tools through an external MCP server only
**Pros:** standard protocol. **Cons:** the worker's own model calls would still commit blind. An MCP server over the same registry stays possible (TOOL_EXTRACTION_PLAN.md step 6).

## Consequences
- **Easier:** a failed program, an exhausted budget or a missing WITNESS line is found inside the call, before an attempt is counted.
- **Harder:** a model call is several provider rounds; latency and token use grow with tool use (01-01 full runs: about $0.012 a run).
- **Unchanged:** final verification, witness acceptance, L110 labelling, exit codes, confinement, System 1.
- **Revisit:** the BOOTSTRAP entity signal if it recurs at a larger sample; work tools for other operations only with a measurement; the scratchpad if a task family shows failures that survive the in-call loop; MCP clients beyond stdio.

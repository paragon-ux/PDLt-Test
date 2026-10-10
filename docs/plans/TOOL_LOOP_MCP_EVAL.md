# Tool loop and MCP: evaluation plan (2026-10-10, proposed)

**Origin.** The user (2026-10-10) asked for MCP to be investigated as an architectural answer to the repair failures. The reasoning: the worker is stateless and guesses. It can't discover line numbers or gather context before acting, and adding schemas one at a time won't scale. The user pointed to waymark-engine and Agy-Context-Saver under Antigravity, where agents discover typed tools and call them within a turn (`C:\Users\USER\Desktop\Installation\antigravity_export\Project Comparison Analysis_2.md`). A second concern was protocol integrity: L110 suggests that a model given a scratchpad may try to game the schema.

## 1. What the capability is, and where MCP fits

There are two separate things here:

- **The capability: a tool loop inside an operation.** The model calls a tool, the host runs it and returns the result, and the model calls more tools or submits its deliverable. The loop is what lets the model discover line numbers, run its program, and see what happened before committing. Today every operation is one request and one JSON reply. `ApiWorker.build_request_body` (`providers/api_worker.py:837-934`) sends no `tools` and sets `text.format` to `json_object` or `json_schema`.
- **MCP: a protocol for packaging and serving tools** between a host and tool servers. PDLt is the host that talks to the model (OpenRouter Responses API, `api_worker.py:1167`). Whether a tool lives in-process or behind an MCP server, the model sees the same thing: a function schema in `tools`.

So MCP alone doesn't give the model agency; the loop does. MCP becomes useful in two places:
1. **Getting tools from MCP servers**, such as waymark-engine for code navigation.
2. **Serving PDLt to other agents**: ADR-0023 lists an MCP server as a transport.

**Provider support** (OpenRouter's free model-metadata endpoint, no key, no tokens): the Cerebras endpoint for `openai/gpt-oss-120b` lists `tools`, `tool_choice`, `response_format` and `structured_outputs`. Pricing is $0.35/M input and $0.75/M output. Whether the model calls tools well at low reasoning effort is not known.

**On the Antigravity comparison:** those agents are frontier models in a native tool loop. The token and latency figures in the analysis are specific to those experiments (the analysis says so itself). What carries over is the design: few, typed, discoverable tools with compact results.

## 2. Which recorded failure causes a tool loop reaches

Causes as numbered in `L107_SCRATCHPAD_REVIEW.md` §3:

| Cause | Today | With a sandbox tool loop |
|---|---|---|
| 2. The repair can't see its program | rewrites from scratch; line numbers point at nothing | `read_attempt` returns the failed program with line numbers and the host's correction |
| 3. Traceback dropped | L108 restores it in the correction | `run_python` returns the full traceback for any program the model tries |
| 4. The JSON layer eats a backslash | the line the host runs differs from what the model meant | the model runs the decoded program and sees the SyntaxError before submitting |
| 5. Budget stops carry no measurement | "stopped after 10M steps" | the model sees `steps_used`, and can measure its own program before submitting |
| 6. One repair | memory never used | tool calls are iterations within one attempt, consuming no repairs |
| "tests now pass" claims | the model can't run anything | it can run its tests and see the results |

Cause 1 (note order) and cause 7 (enforcement) are schema matters, outside the loop.

## 3. Integrity: what L110 shows, and what the prototype must hold

**L110 predates the scratchpad.** Recorded artifacts, all 4,505 turns in `catalogue-runs`:
- A negative proof witness passed verification 41 times.
- On 01-01, which has a solution, that happened 10 times, across 7 runs going back to 2026-09-30. 9 of the 10 had no scratchpad, and 9 closed as CLOSED_SUCCESS: 7 provisional (declared witnesses, from before L104) and 2 printed by a program and labelled sandbox-reproduced.
- The other 31 were on 13-01: 29 graded PASS, 2 FAIL.

So the scratchpad didn't create the behaviour; it made it visible. The v3 note said the program "simply prints the required WITNESS line, satisfying the verification requirement without heavy computation".

**The sandbox held; the referee rule is what's weak.** The host accepts a proof it can't check, and calls it reproduced when a program prints it. Fixing the grader alone wouldn't address that, as the user says. The fix belongs in the host's acceptance rule (L110), independent of any tool loop.

**A tool loop sharpens the risk:** the model gets something it can probe. Invariants for the prototype, enforced by the host, never by the model's behaviour:
1. **Tools expose capabilities, never the verifier.** No "check my witness" tool. `run_python` returns raw sandbox facts only, so the model can't search for forms the verifier accepts.
2. **Final verification stays independent.** The host re-runs the submitted deliverable in a fresh sandbox run. Tool-call outputs are never evidence, as RS-09 already rules for previous turns.
3. **Confinement is unchanged.** Every tool run is a normal sandbox run (ADR-0021): own directory, no network, no processes, step and time limits. Each attempt also has a tool-call budget and a total step budget.
4. **Everything is audited.** Each tool call and result is an event, the broker of ADR-0025 in its smallest form.
5. **GUARD-01:** tool descriptions state capabilities, never methods. Notes and tool results never reach the deliverable or the protocol state.

## 4. Prototype (evaluation plane first)

- **Stage 0: capability probe.** Static part already done (provider metadata). Live part: one call (about $0.003) to check that OpenRouter's Responses API carries a function call for this model, and that the final reply still meets the JSON contract.
- **Stage 1: in-process tool loop**, as a worker variant used only by the frozen-repair runner. No change to the protocol path.
  - **Tools:**
    - `read_attempt()`: the failed program with line numbers, plus the correction;
    - `run_python(code)`: exit status, stdout tail, the full traceback with line numbers, `steps_used` and `step_budget_exceeded`, at the tier's limits.
  - **Definitions** follow MCP's tool shape (name, description, inputSchema), so they can be served over MCP later unchanged.
  - **Loop:** at most 6 tool calls, then the deliverable.
  - **Offline tests:** the loop with a scripted worker; the invariants in §3 as tests (no verifier tool; the final run is the host's own; tool outputs absent from the deliverable; the budgets hold).
- **Stage 2: frozen-repair pilot.**
  - Same frozen failures as L109.
  - The 12 01-01 failures first: they're the budget stops, where the note had nothing to infer from.
  - Control: their recorded repairs and the v3 run.
  - **Measures:** PASS; tool calls per repair; tokens and cost per repair; whether the model used the line numbers; any fixed-witness attempts (L110); any tool misuse in the audit events.
  - **Cost, to be fixed before the run:** a repair becomes up to 7 calls with growing context, roughly 3–4× a single repair, so about $0.01 each. 12 failures × 3 repeats ≈ $0.36. The key has $1.31.
- **Stage 3 (only if stage 2 shows uplift): MCP.** Serve the same tools from an MCP stdio server, and check offline that the schemas and outputs match. Then decide the ADR-0023 question: whether external agents (Claude Code, Antigravity) drive PDLt through it.

**Out of scope for now:** subagents, and project-file tools (ADR-0025's change sets).

## 5. Decisions this needs from the user

- **The stateless worker is a protocol premise.** The worker instruction says "The supplied projection is the complete invocation for this call." A tool loop changes that for the operations that get it, so it needs an ADR (an amendment to ADR-0025, which is proposed).
- **Whether to approve stages 0–2 and their cost.** Stage 0's one probe call is about $0.003; stage 1 is offline.

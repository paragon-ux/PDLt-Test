# MCP tools PDLt exposes to the model (internal)

The in-call agent tools (ADR-0029), offered to the worker inside one model call when `--agent-tools` is on. Source: `runtime/agent_tools.py` (registry, host, loop); the engine wires them in at `runtime/session_engine.py:2455-2488`. Static review, 2026-10-15 (ledger L121).

**Requirements** (the user, 2026-10-15):
- **R1** No tool gives the model a way to undermine the sandbox.
- **R2** No tool is a route for injected instructions: tool results and any external content are data, never instructions.
- **R3** Fail closed: deny by default.
- **R4** Every input is validated against a schema.
- **R5** Every call is logged, so it can be monitored.

## Tools

| Tool | Offered on | Purpose | Inputs | Side effects | Reads | Writes | Network | Filesystem outside the sandbox |
|---|---|---|---|---|---|---|---|---|
| `run_python` | EXECUTE_UNCONFIRMED | Run a program for the model's own inspection before it commits | `{code: string}` | One sandbox run at the attempt's step, time and memory limits; uses up one of 6 work calls | Python's standard library, from inside the confined run | Its own empty run directory, removed after the run | None: the sandbox never has network (`allow_network` is always false) | None (AppContainer, native or container confinement; nothing runs when confinement is unavailable) |
| `read_attempt` | EXECUTE_UNCONFIRMED, only when there is a previous attempt | Show the previous attempt's programs as the host ran them, numbered, with the host's correction | none (`{}`) | Uses up one of 6 work calls | That call's in-memory record of the previous attempt | Nothing | None | None |
| `submit_execute_unconfirmed` | EXECUTE_UNCONFIRMED | End the call with an outcome the host's own checks accept | `{outcome: <the operation's output schema>}` | Runs the deliverable's programs in the sandbox, as the host will (at most 3 submissions); acceptance ends the call | As `run_python` | As `run_python` | None | None |
| `submit_bootstrap_analysis` | BOOTSTRAP_ANALYSIS | The same, checked by the wire model | `{outcome: …}` | Wire parse only; at most 3 | Nothing | Nothing | None | None |
| `submit_draft_prompt` | DRAFT_PROMPT | The same, plus the host's pseudocode lint | `{outcome: …}` | Wire parse and lint; at most 3 | Nothing | Nothing | None | None |
| `submit_draft_plan` | DRAFT_PLAN | The same | `{outcome: …}` | Wire parse and lint; at most 3 | Nothing | Nothing | None | None |

No tool reads the user's project, the workspace, other sessions or the network. No tool returns a verdict (ADR-0029 decision 3). Tool output never reaches the deliverable or the protocol state (`agent_tools.py:17`). The host verifies the accepted reply itself, in its own sandbox run.

## Against the requirements

| | Status | Evidence |
|---|---|---|
| R1 sandbox | **Met** | Every run is `ExecutionSandbox.run_code` at the attempt's limits, the same path as the deliverable's own runs. Confinement unavailable means nothing runs (`sandbox.py:871`, `sandbox_unavailable`). Escape tests: `tests/test_confinement.py`. One open item: the six container-backend escape tests fail while Docker Desktop is running (task chip, 2026-10-15). |
| R2 injection | **Partly met; flagged** | The host never acts on tool output. It arrives as `function_call_output` items, the data channel of the Responses API, and never enters the deliverable or protocol state. Its content comes from the model's own programs or the host's own correction. However, nothing tells the model that tool output is data: the capability note says only "Tool results are for your inspection only" (`agent_tools.py:137`). A program the model writes can print text copied from the task's untrusted input, and that text comes back unlabelled. **Flag I-1:** state in the tool descriptions that results are data and never instructions. |
| R3 deny by default | **Met** | An unknown tool, or one not offered on this call, returns an error and runs nothing (`agent_tools.py:170`). Budgets are enforced by the host (6 work calls and 3 submissions per model call; `agent_tools.py:292-300`). |
| R4 schema validation | **Partly met; flagged** | Submissions go through the operation's Pydantic wire model (ADR-0018). Work-tool arguments do not: `dispatch` checks only that `code` is a string, accepts extra properties although `inputSchema` declares `additionalProperties: false`, and ignores any arguments to `read_attempt` (`agent_tools.py:164-179`). `code` has no size limit before the sandbox's own limits apply. **Flag I-2:** validate every argument object against the tool's `inputSchema` and reject on mismatch. |
| R5 logging | **Met in the harness** | Every tool call and submission becomes an `AGENT_TOOL_CALL` event (`session_engine.py:2488`, text trimmed to 2,000 characters by `event_view`) and goes into the call trace. |

## Related configuration notes
- **The sandbox network setting is not what System 1 is told.** `PDLT_SANDBOX_NETWORK` changes only System 1's environment state (`activation_route.py:57`); the sandbox itself never gets network. If the variable is set to true, System 1 is told that network access exists while the sandbox denies it. That's not a hole in the sandbox, but it is a mismatch.

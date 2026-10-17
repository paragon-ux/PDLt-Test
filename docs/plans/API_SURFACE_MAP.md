# API surface map: where the three target forms share code and where they bypass it

The user (2026-10-15) named three target forms: the interactive REPL, headless runs and the MCP server. Planned: a documented programmatic API/SDK that all three go through, with extension points for model providers, task types and verifiers (ledger L120). This map records today's paths (static read of `main` at `75bbfce6`). It is the input for that API, not a design.

## Status (2026-10-16): batch B1 built (`pdl_taskmaster.api`, `docs/api.md`)

The map below is the state it started from. What B1 changed:

| Concern | Now |
|---|---|
| Session lifecycle | `api.Session`: open, restore, send, confirm, revise, stop, cancel, run, status, close. The REPL's `open_session` uses its folder helpers (`prepare_worker`, `stored_workspace`, `write_pointer`). |
| Model providers | `api.providers` registry (`api`, `recorded`); both REPL chains (startup, `/worker`) create workers through it with one settings helper. Codex stays outside (L114 deprecation). |
| Verifiers | The engine holds one `output_verifier`; `Session.open(output_verifier=...)` injects a registry. |
| Sandbox | `api.create_sandbox`; the MCP server uses it with `require_confined=True`. |
| Results and exit status | `api.outcome.exit_status` and `TurnResult`; the REPL's headless exit and `run_catalogue.py` use the one mapping. |
| Reading closed sessions | `api.closed_turns`; the MCP resources are built on it. |

**B2 (2026-10-17, L124): every gap in the map below is closed.**
- **Extension points** are defined by versioned profiles (`src/pdl_taskmaster/extensions/`): task types (`pdlt.task-type/1`), verifiers (`pdlt.verifier/1`) and providers (`pdlt.provider/1`, worker and system1 roles).
- **Configuration:** typed `RunSettings` replace the host's attribute copying.
- **System 1** is a provider of its own.
- **The direct reply** is produced by the engine.
- **Interfaces** pass one conformance suite.

Not extensible by design: stages, review gates, execution modes and the workspace structure. See `docs/extensions.md`.

## The paths today

```
pdlt (host/cli.py:main) ──> host/repl.py:main ──┬── REPL (interactive loop)
                                                └── headless (--non-interactive; exit codes)
        both: repl.open_session ──> SessionRuntime ──> PDLtHost (host/app.py) ──> SessionEngine (runtime/session_engine.py)

python -m pdl_taskmaster.host.mcp_server ──> AgentToolServer
        tools:     build_host ──> its own ExecutionSandbox + OperationBridge + agent_tools.ToolHost   (no SessionEngine)
        resources: ClosedSessions ──> reads session folders directly                              (no WorkspaceRun)
```

The REPL and headless runs are one code path: headless is a flag on the same `main`. The MCP server shares only lower-level pieces with them.

## Concern by concern

| Concern | REPL / headless | MCP server | Shared layer today | What the API would need to cover |
|---|---|---|---|---|
| Entry and configuration | One argparse parser, about 250 lines (`repl.py:910` `_build_parser`). Settings travel to the engine as attributes on the worker and are copied by `getattr` (`app.py:140-145`: `contract_form`, `max_repairs`, `draft_execute`, `agent_tools`, `representation`, `tier_d1`). | Its own argparse: tier, witness requirement, sandbox, sessions folder (`mcp_server.py` `main`). | None. | A typed configuration object that every form builds and the engine reads. |
| Session lifecycle (open, restore, close) | `repl.open_session` → `SessionRuntime` → `PDLtHost.start` builds or restores `SessionEngine`. The session folder layout is the REPL's (`repl.py:36` `_default_session_base`). | No session. The resources import the REPL's private `_default_session_base` (`mcp_server.py:197`). | `PDLtHost` is the nearest thing to a library layer, but it is shaped for the REPL. | A session or client object: open, restore, send, confirm/revise/cancel, status, close, with the folder layout behind it. |
| Turn handling | `PDLtHost.handle` → `SessionEngine.handle_user_message`. A bypass path calls the worker directly from the host (`app.py:171` `worker.call(_PlainRequest…)`), outside the engine. | Not applicable; the outside agent is the model. | `SessionEngine.handle_user_message`, `handle_explicit_review`, `record_interruption`, `record_standing_confirmation`. | One turn API that owns the bypass too, so every form gets the same routing. |
| Model providers | `WorkerAdapter` Protocol (`providers/base.py:17`: `call(request) → WorkerResult`). Chosen by an if-chain in `repl.py:1190-1236` (recorded, codex, api), repeated for `/model` switching at `repl.py:1692`. System 1 rides on the worker (`getattr(worker, "sys1_client")`, `app.py:116,134`). | None. | The `WorkerAdapter` Protocol. | A provider registry for the main model and System 1, kept separate; selection by name, not an if-chain. |
| Task types | Problem class is a System 1 recipe choice (VERIFIED_EXECUTION or STANDARD_EXECUTION); operations and their inputs come from `contracts/EXECUTION_CONTRACT.json`; the route (confirmed, unconfirmed, control) is an engine flag. | The tool registry per operation (`agent_tools.TOOLS`, `TOOL_OPERATIONS`). | The contracts JSON, read by both. | A task-type extension point: problem class, route, operations and the witness forms (ADR-0030) a type accepts. |
| Verifiers | `SessionEngine._verify_result` creates `OutputVerifier()` on every call (`session_engine.py:2664`). The checker registry (`output_verifier.py:26` `register`) therefore has no injection point; only `FallbackChecker` runs. | The submission check `agent_tools.make_validator` reuses the bridge parse and two private engine helpers (`mcp_server.py:171`: `_parse_sandbox_witness`, `_python_blocks`). | `OutputVerifier` and its registry exist; the witness parse and program extraction are private engine functions. | Verifier injection per task type or domain; public witness and program helpers. |
| Sandbox | The engine builds its sandbox; the host passes `sandbox_mode`. | `build_host` builds its own `ExecutionSandbox(label="mcp")` (`mcp_server.py:175`). | `ExecutionSandbox` and its backends. | One sandbox factory owned by the session layer. |
| Results and exit status | Headless maps the final stage to an exit code inside `repl.py` (`EXIT_*`, `repl.py:487-489`, closure mapping near `:1845`). `run_catalogue.py:113-118` repeats the constants. | JSON-RPC results; no closure. | None. | A result object: stage, exit status, witness form, host notes, deliverable. Exit codes derived from it in one place. |
| Reading closed sessions | Resume goes through `SessionEngine.restore`; the workspace is written by `WorkspaceRun`. | `ClosedSessions` reads `turn.json`, `current.md` and `program-output.json` by path (L117). | `WorkspaceRun` writes them. | A read API over closed sessions that the MCP resources and any client use. |

## Outside the three forms
- **`run_catalogue.py`** (evaluation plane) drives the headless form as a subprocess (`pdl_taskmaster.host.cli`, `run_catalogue.py:400`) and reads exit codes and files. It is a natural first consumer to port to the API.
- **`host/control_cli.py`** (the control route) queries the model directly, bypassing the protocol. It is evaluation tooling, not a target form.

## What this means for the API
1. **The REPL and headless runs need little new code.** Most of their gaps are about pulling REPL-shaped pieces out of `repl.py` and `PDLtHost`: configuration, provider selection, exit mapping and the session folder layout.
2. **The MCP server is the form that bypasses a common layer.** Its tools build their own sandbox and validator, and its resources read files by layout. Under an API they would open a session, or a tool context, and use the read API.
3. **Two extension points exist but cannot be reached:** the `WorkerAdapter` Protocol has no registry, and the checker registry has no injection point. Task types have no extension point; they are spread across System 1 recipes, the contracts JSON and engine flags.

# MCP tools and resources PDLt exposes externally

`python -m pdl_taskmaster.host.mcp_server` (ADR-0029 decisions 10 and 11) lets other harnesses and models use PDLt: run programs in its sandbox, have a deliverable checked, and read what closed sessions produced. Static review, 2026-10-15 (ledger L121).

**Requirement** (the user, 2026-10-15): artifacts carry their status and provenance, so consumers can tell verified results from unverified ones. This matters most while code tasks can pass without their hidden tests (L115). A "PASS" patch from such a task has not been fully verified.

**Transport and permissions:** stdio only. The client is the process that starts the server, running as the local user. There is no network listener and no authentication beyond the right to start the process. The server needs read access to the sessions folder (`--sessions`, by default the REPL's `runs/live-sessions`); programs need the sandbox's confinement backend. It writes nothing outside the sandbox's run directories and its call log (`--log`, by default a new file in `mcp-server/` beside the sessions folder). Programs run only under OS-native confinement: `--sandbox` accepts `auto`, `native` or `container`, never `audit-only`.

**What the server is, and is not.** It is a narrow execution and submission service: two in-call tools (`run_python`, `submit_execute_unconfirmed`) and read-only access to closed sessions (`resources/list`, `resources/read`). It does not run a PDLt session: no System 1 routing, bootstrap analysis, review gates or verification after an accepted submission. Inside the harness, `--agent-tools` gives the model the same tools within selected operations (`EXECUTE_UNCONFIRMED`, `BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `DRAFT_PLAN`), and the host then verifies the deliverable itself; here nothing does.

## Run and check the server

The server needs no API key: it runs programs and reads closed sessions, and never calls a model. An MCP client starts it as `python -m pdl_taskmaster.host.mcp_server`, using the Python of the environment PDLt is installed in; the client configuration for each host is on the host pages ([Windows](../hosts/windows.md#use-the-mcp-server-from-another-agent), [Linux](../hosts/linux.md#use-the-mcp-server-from-another-agent), [macOS](../hosts/macos.md#use-the-mcp-server-from-another-agent)).

To check it without a client, send it two requests on standard input, with the environment active.

bash (Linux, macOS):

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"setup-check","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_python","arguments":{"code":"print(6 * 7)"}}}' \
  | python -m pdl_taskmaster.host.mcp_server
```

PowerShell (Windows):

```powershell
@'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"setup-check","version":"0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_python","arguments":{"code":"print(6 * 7)"}}}
'@ | python -m pdl_taskmaster.host.mcp_server
```

Expected: two JSON lines. The first names the server (`"serverInfo": {"name": "pdlt-agent-tools", ...}`); the second contains `standard output:\n42` and `"isError": false`. Every call is logged to `mcp-server/calls-<time>-<pid>.jsonl` beside the sessions folder (or to `--log`).

| Flag | Effect |
|---|---|
| `--sessions FOLDER` | The sessions folder whose closed results are served read-only (default: the REPL's) |
| `--tier MINIMAL\|STANDARD\|HEAVY_COMPUTE` | The execution budget every program runs under (default `STANDARD`) |
| `--witness-required` | A submission must contain a program that prints a `WITNESS` line |
| `--sandbox auto\|native\|container` | The sandbox backend; the audit-only opt-out is not offered (default `auto`) |
| `--log FILE` | The JSON-lines call log (default: a new file in `mcp-server/` beside the sessions folder) |

## Session lifecycle and protocol versions

One server process is one MCP session, with one tool host, one sandbox and one set of budgets (L121, L138):

- **`initialize` comes first, once.** Before it, only `ping` is answered; `tools/*` and `resources/*` get the JSON-RPC error `-32600` ("not initialized"), so nothing can run a program before the version is negotiated. A second `initialize` gets `-32600` ("already initialized"): it neither resets the budgets nor starts a new sandbox. A new task that needs fresh budgets needs a new server process, which is also the pattern for scripts: one process per task.
- **The budgets last as long as the process:** 6 work calls (`run_python`) and 3 submissions. Spent, a call returns a tool result with `isError: true` and "the tool-call budget is spent" or "the submission budget is spent".
- **Protocol revisions** (`SUPPORTED_PROTOCOL_VERSIONS`): `2025-11-25` (the newest), `2025-06-18`, `2025-03-26` and `2024-11-05`. A supported request is echoed; any other is offered `2025-11-25`, as the MCP lifecycle requires, and a client that cannot use it disconnects. **Not supported:** the stateless `2026-07-28` revision, whose per-request envelope (`server/discover`, no `initialize`) this server does not implement. A client asking for it in `initialize` is offered `2025-11-25`, never `2026-07-28`.
- **What depends on the revision:** `outputSchema` (in `tools/list`) and `structuredContent` (in submission results) are sent only from `2025-06-18` on. JSON-RPC batches are accepted only under `2025-03-26`, the one revision that has them: at most 32 messages, each handled and logged as if sent alone under the same budgets, with one response per request in order and none for notifications. A batch before `initialize`, under another revision, empty, too large, or holding `initialize` is refused whole with one `-32600` and nothing in it runs.
- **Errors.** A tool that runs and fails, arguments that do not match a tool's input schema, a rejected submission and a spent budget are tool results with `isError: true`. JSON-RPC errors are for the protocol: `-32700` unparseable JSON, `-32600` an invalid request (not an object, a null or non-scalar `id`, before `initialize`, a second `initialize`, a refused batch), `-32601` an unknown method, `-32602` an unknown or unoffered tool or non-object `params`, `-32002` an unknown resource, `-32603` a call log that cannot be written.
- **At exit** (end of standard input), the server closes its sandbox, deleting its run directories, and closes the call log.

## Tools

| Tool | Returns | Verification evidence with it | What the client needs |
|---|---|---|---|
| `run_python {code}` | Exit status, steps used, whether the step budget or time limit stopped it, and the last 2,000 characters of standard output and standard error | None. A run is "for inspection and is not evidence". | Only to start the server. Budget: 6 work calls for the life of the server process. |
| `submit_execute_unconfirmed {outcome}` | `{ok, result or errors, facts}`. Errors name the path, what was found and what is required. Facts give each program's exit status and whether it printed a WITNESS line. An accepted submission says "the structural checks passed; nothing verifies the deliverable afterwards here", and so does the tool's description. | Structural checks only: the wire model, the programs run as the host would run them, and, with `--witness-required`, a WITNESS line that the program does not write out itself (the host's rule, L113, L139). **No verification follows.** | The same. At most 3 submissions per server process. |

`read_attempt` is not offered externally (there is no previous attempt), and neither are the submit-only tools.

**Structured results.** From `2025-06-18` on, `submit_execute_unconfirmed` publishes an `outputSchema` (`agent_tools.SUBMIT_RESULT_SCHEMA`, JSON Schema 2020-12): either `{ok: true, result, facts}` or `{ok: false, errors: [{code, path, problem, expected}], facts, submissions_left}`, with no other fields. Each submission result carries that envelope as `structuredContent` and as JSON text in `content`; under older revisions, the text only. A spent submission budget is a plain `isError` text result. MCP's `structuredContent` is tool-result data; it is unrelated to `pdlt --api-structured-output`, which constrains how a provider decodes a model's reply.

## Resources (read-only, L117)

| Resource | Returns | Verification evidence with it | What the client needs |
|---|---|---|---|
| `pdlt://sessions/<session>/<workspace>/<turn>/response` | The response as published: the deliverable text, any host notes (for example "unverified" or "written into the program"), and the attached Result IR with its witness | The closure stage is in the listing's `description` (`CLOSED_SUCCESS: …` or `CLOSED_UNVERIFIED: …`). The witness's `provisional` flag and the host notes are in the text. | Read access to the sessions folder. Only closed turns with a result are listed. A URI is resolved by listing, never by joining a path, and the file must lie under the folder. |
| `pdlt://sessions/<session>/<workspace>/<turn>/program-output` | `{runs: [{block, exit_code, stdout, stderr}]}`: what the host's programs printed for the result, each stream cut at 64 KiB | None beyond the runs themselves | The same. Present only for sessions closed after L117. |
| `pdlt://sessions/<session>/<workspace>/<turn>/provenance` | The turn's provenance (`runtime/provenance.py`): status; verification level (`host_verified`, `contract_checked` or `unverified`), problem class, witness form, whether the host reproduced the result, the unverified reason, and a caveat for `contract_checked`; `deliverable_sha256`; model; PDLt version; closing time | It is the evidence statement. Recorded by the host at closure; for turns closed before, derived from the turn's events, with no model and never a stronger claim than the records support | The same. |

Every read of a turn's `response` or `program-output` returns the turn's provenance as a second content item, and each listing's description starts with the status and level (for example `CLOSED_SUCCESS, contract_checked: ...`).

## Status and provenance before L121 (kept for the record)

| What a consumer needs to tell verified from unverified | Today |
|---|---|
| The closure stage | Only in the listing's description; not inside the artifact |
| The problem class: VERIFIED_EXECUTION (a witness the host reproduced) or STANDARD_EXECUTION (contract checks only, no hidden tests; L115) | Not exposed. It is in the turn's `routing.json` and events. |
| The witness form: computed, certificate, argued or negative (ADR-0030) | Partly: the Result IR witness is in the response, but whether the host reproduced it is in the events |
| The deliverable's hash | Not exposed; `turn.json` has `deliverable_sha256` |
| The model, the PDLt version or commit, and the time | Not exposed |

**Flags** (all fixed in L121, 2026-10-15; the section above is how it stood before):
- **E-1 Provenance.** Artifacts do not carry their own status and provenance. A consumer cannot tell a STANDARD_EXECUTION "success" (contract checks only, with the L115 caveat) from a VERIFIED_EXECUTION success without reading files the server does not serve. Proposal: a `provenance` resource per turn holding the stage, problem class, witness form and reproduction, the L115 caveat for STANDARD_EXECUTION, `deliverable_sha256`, model, PDLt version and time.
- **E-2 Misleading acceptance text.** An accepted submission says "accepted; the host now verifies the deliverable" (`agent_tools.py:202`). Through the MCP server nothing verifies afterwards, so an external client can mistake a structural acceptance for verification.
- **E-3 No call log.** The server builds its tool host without a logger (`mcp_server.py:179`), so external tool calls and submissions are recorded nowhere. Inside the harness they are (`AGENT_TOOL_CALL`).
- **E-4 Weaker sandbox on request.** `--sandbox audit-only` is accepted and runs external programs with Python audit hooks only, without OS confinement. For an externally exposed server this should be refused, or at least announced in `initialize`.
- **E-1 to E-4, as fixed:** the `provenance` resource and the provenance returned with every read; the MCP-specific acceptance text and description; the JSON-lines call log, written before each request runs and after (a log that cannot be written stops the request; one that cannot be opened stops the server); `audit-only` refused.
- **E-5 Arguments not validated.** Fixed in L122, as internal flag I-2: arguments outside `inputSchema` are refused and nothing runs.

## Call log

Every request is written to a JSON-lines call log (`--log`, default `mcp-server/calls-<time>-<pid>.jsonl` beside the sessions folder): an entry before the request runs (`event: request`: the id, method and parameters) and one after (`event: response`: the duration, any JSON-RPC error and `isError`), plus each tool call and submission as the tool host records it (the code, the output, the envelope and the outcome). Strings are cut at 20,000 characters. A refused batch is recorded as one `event: batch` entry. A log that cannot be opened at start stops the server (exit status 1); one that cannot be written refuses the request with `-32603`, and nothing runs. The log keeps submitted code and outputs in plain text and the server never deletes it: protect and rotate the folder as the code and data it will hold require.

## Tested from outside

`tests/test_mcp_external.py` (L123) starts the server process and drives it with the official MCP Python SDK client: the handshake (which lands on `2025-11-25`), the published schemas (the SDK checks `structuredContent` against the `outputSchema`), tool calls and their errors, budgets, resources with provenance, the call log and the refused `audit-only` start. `tests/test_mcp_server.py` covers the lifecycle, version negotiation, the revision-dependent fields, batches, error codes, the result schema and the cleanup at exit (L138).

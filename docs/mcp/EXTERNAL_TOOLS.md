# MCP tools and resources PDLt exposes externally

`python -m pdl_taskmaster.host.mcp_server` (ADR-0029 decisions 10 and 11) lets other harnesses and models use PDLt: run programs in its sandbox, have a deliverable checked, and read what closed sessions produced. Static review, 2026-10-15 (ledger L121).

**Requirement** (the user, 2026-10-15): artifacts carry their status and provenance, so consumers can tell verified results from unverified ones. This matters most while code tasks can pass without their hidden tests (L115). A "PASS" patch from such a task has not been fully verified.

**Transport and permissions:** stdio only. The client is the process that starts the server, running as the local user. There is no network listener and no authentication beyond the right to start the process. The server needs read access to the sessions folder (`--sessions`, by default the REPL's `runs/live-sessions`); programs need the sandbox's confinement backend. It writes nothing outside the sandbox's run directories and its call log (`--log`, by default a new file in `mcp-server/` beside the sessions folder). Programs run only under OS-native confinement: `--sandbox` accepts `auto`, `native` or `container`, never `audit-only`.

## Tools

| Tool | Returns | Verification evidence with it | What the client needs |
|---|---|---|---|
| `run_python {code}` | Exit status, steps used, whether the step budget or time limit stopped it, and the last 2,000 characters of standard output and standard error | None. A run is "for inspection and is not evidence". | Only to start the server. Budget: 6 work calls for the life of the server process. |
| `submit_execute_unconfirmed {outcome}` | `{ok, result or errors, facts}`. Errors name the path, what was found and what is required. Facts give each program's exit status and whether it printed a WITNESS line. An accepted submission says "the structural checks passed; nothing verifies the deliverable afterwards here", and so does the tool's description. | Structural checks only: the wire model, the programs run as the host would run them, and a WITNESS line when `--witness-required`. **No verification follows.** | The same. At most 3 submissions per server process. |

`read_attempt` is not offered externally (there is no previous attempt), and neither are the submit-only tools.

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

## Tested from outside

`tests/test_mcp_external.py` (L123) starts the server process and drives it with the official MCP Python SDK client: the handshake, the published schemas, tool calls and their errors, budgets, resources with provenance, the call log and the refused `audit-only` start.

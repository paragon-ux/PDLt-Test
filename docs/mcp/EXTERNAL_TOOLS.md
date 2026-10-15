# MCP tools and resources PDLt exposes externally

`python -m pdl_taskmaster.host.mcp_server` (ADR-0029 decisions 10 and 11) lets other harnesses and models use PDLt: run programs in its sandbox, have a deliverable checked, and read what closed sessions produced. Static review, 2026-10-15 (ledger L121).

**Requirement** (the user, 2026-10-15): artifacts carry their status and provenance, so consumers can tell verified results from unverified ones. This matters most while code tasks can pass without their hidden tests (L115). A "PASS" patch from such a task has not been fully verified.

**Transport and permissions:** stdio only. The client is the process that starts the server, running as the local user. There is no network listener and no authentication beyond the right to start the process. The server needs read access to the sessions folder (`--sessions`, by default the REPL's `runs/live-sessions`); programs need the sandbox's confinement backend. It writes nothing outside the sandbox's run directories.

## Tools

| Tool | Returns | Verification evidence with it | What the client needs |
|---|---|---|---|
| `run_python {code}` | Exit status, steps used, whether the step budget or time limit stopped it, and the last 2,000 characters of standard output and standard error | None. A run is "for inspection and is not evidence". | Only to start the server. Budget: 6 work calls for the life of the server process. |
| `submit_execute_unconfirmed {outcome}` | `{ok, result or errors, facts}`. Errors name the path, what was found and what is required. Facts give each program's exit status and whether it printed a WITNESS line. | Structural checks only: the wire model, the programs run as the host would run them, and a WITNESS line when `--witness-required`. **No verification follows.** | The same. At most 3 submissions per server process. |

`read_attempt` is not offered externally (there is no previous attempt), and neither are the submit-only tools.

## Resources (read-only, L117)

| Resource | Returns | Verification evidence with it | What the client needs |
|---|---|---|---|
| `pdlt://sessions/<session>/<workspace>/<turn>/response` | The response as published: the deliverable text, any host notes (for example "unverified" or "written into the program"), and the attached Result IR with its witness | The closure stage is in the listing's `description` (`CLOSED_SUCCESS: …` or `CLOSED_UNVERIFIED: …`). The witness's `provisional` flag and the host notes are in the text. | Read access to the sessions folder. Only closed turns with a result are listed. A URI is resolved by listing, never by joining a path, and the file must lie under the folder. |
| `pdlt://sessions/<session>/<workspace>/<turn>/program-output` | `{runs: [{block, exit_code, stdout, stderr}]}`: what the host's programs printed for the result, each stream cut at 64 KiB | None beyond the runs themselves | The same. Present only for sessions closed after L117. |

## Status and provenance today, and the gaps

| What a consumer needs to tell verified from unverified | Today |
|---|---|
| The closure stage | Only in the listing's description; not inside the artifact |
| The problem class: VERIFIED_EXECUTION (a witness the host reproduced) or STANDARD_EXECUTION (contract checks only, no hidden tests; L115) | Not exposed. It is in the turn's `routing.json` and events. |
| The witness form: computed, certificate, argued or negative (ADR-0030) | Partly: the Result IR witness is in the response, but whether the host reproduced it is in the events |
| The deliverable's hash | Not exposed; `turn.json` has `deliverable_sha256` |
| The model, the PDLt version or commit, and the time | Not exposed |

**Flags:**
- **E-1 Provenance.** Artifacts do not carry their own status and provenance. A consumer cannot tell a STANDARD_EXECUTION "success" (contract checks only, with the L115 caveat) from a VERIFIED_EXECUTION success without reading files the server does not serve. Proposal: a `provenance` resource per turn holding the stage, problem class, witness form and reproduction, the L115 caveat for STANDARD_EXECUTION, `deliverable_sha256`, model, PDLt version and time.
- **E-2 Misleading acceptance text.** An accepted submission says "accepted; the host now verifies the deliverable" (`agent_tools.py:202`). Through the MCP server nothing verifies afterwards, so an external client can mistake a structural acceptance for verification.
- **E-3 No call log.** The server builds its tool host without a logger (`mcp_server.py:179`), so external tool calls and submissions are recorded nowhere. Inside the harness they are (`AGENT_TOOL_CALL`).
- **E-4 Weaker sandbox on request.** `--sandbox audit-only` is accepted and runs external programs with Python audit hooks only, without OS confinement. For an externally exposed server this should be refused, or at least announced in `initialize`.
- **E-5 Arguments not validated.** As internal flag I-2: work-tool arguments are not validated against `inputSchema`.

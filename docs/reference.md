# Reference

Settings, file locations and failure symptoms that are the same on every host. How to set an environment variable differs by shell: `export NAME=value` in bash or zsh (Linux, macOS), `$env:NAME = "value"` in PowerShell (Windows). Your host's page shows both the one-window and the permanent form ([Windows](hosts/windows.md#5-configure-a-model), [Linux](hosts/linux.md#5-configure-a-model), [macOS](hosts/macos.md#5-configure-a-model)).

## Environment variables

Only `OPENROUTER_API_KEY` is required, and only for live runs. Every other variable is optional.

| Variable | Required? | Effect |
|---|---|---|
| `OPENROUTER_API_KEY` | For live runs | The key for the task model and, unless overridden below, System 1 |
| `SYS1_API_KEY`, `SYS1_MODEL`, `SYS1_ENDPOINT` | No | System 1's own key, model or endpoint |
| `OPENROUTER_PROVIDER`, `OPENROUTER_PROVIDER_ORDER` | No | Pin the OpenRouter providers that serve requests ([Providers](providers.md)) |
| `PDLT_SANDBOX` | No | Sandbox mode: `auto` (the default: the host's native backend), `native`, `container`, or `audit-only` (no OS confinement; prints a warning) |
| `PDLT_CONTAINER_RUNTIME`, `PDLT_CONTAINER_IMAGE` | No | The container backend's runtime (default `docker`, else `podman`) and image (default `python:<major.minor>-slim`) |
| `PDLT_SANDBOX_NETWORK`, `PDLT_POLICY_SCOPE`, `PDLT_KNOWLEDGE_CUTOFF` | No | What System 1 is told about the environment when it decides whether a request is in bounds (ADR-0020). `PDLT_SANDBOX_NETWORK` never gives programs network access. |
| `PDLT_TIER_D1` | No | `0` stops feeding the model its own sandbox failures as repairs (default on) |
| `PDLT_AGENT_TOOLS` | No | `1` turns on in-call tools (ADR-0029) |
| `PDLT_RESULT_IR` | No | `1` asks for a Result IR on every task, not only verified ones |
| `PDLT_CATALOGUE_RUNS` | No | Where catalogue runs are written (default: `PDLt-Catalogue-Archive` beside the checkout) |
| `PDLT_THEME`, `PDLT_USER_COLOR`, `PDLT_ASSISTANT_COLOR`, `NO_COLOR` | No | REPL colours; `NO_COLOR` turns them off |
| `PDLT_VIEWER_ROOT` | No | The root the local viewer reads (`python -m viewer`, source checkout only) |

## Where files are written

| What | Where |
|---|---|
| REPL and headless sessions | `runs/live-sessions/<session>/` in a source checkout, else `~/.pdlt/runs/live-sessions/<session>/`; `--workspace-root` chooses another folder. Each holds `workspaces/`, `observations/`, the transcript, `worker-progress.log` and `call-trace.jsonl`. |
| Python API sessions | The folder passed to `Session.open`, laid out the same way |
| A published result | `<workspace>/turns/<turn>/stages/50_execution/output/`: `current.md`, `program-output.json`, `provenance.json` |
| MCP server call log | `--log`, else `mcp-server/calls-<time>-<pid>.jsonl` beside the sessions folder |
| Catalogue runs (source checkout only) | `$PDLT_CATALOGUE_RUNS`, else `PDLt-Catalogue-Archive` beside the checkout; never inside the repository |
| Seeded contracts (`pdlt init`) | `~/.pdlt/versions/v2/contracts`, or `./contracts` with `--local` |

## Exit codes

The same codes come from a headless run, from `TurnResult.exit_status` in the Python API, and from `api.outcome.exit_status(stage)`: 0 success, a direct reply or a published refusal; 1 cancelled; 2 stopped at a review gate; 3 waiting for input; 4 harness or provider error; 5 published but not established by the host; 130 interrupted. The full table, with what to do for each, is in [REPL and headless runs](repl.md#exit-codes).

## When something fails

| Symptom | Look at |
|---|---|
| `[warn] code execution unavailable` when the REPL starts, or `SandboxNotConfined` | No OS-native sandbox on this machine: your host's page, step 4, and the [Sandbox guide](SANDBOX.md) |
| `OPENROUTER_API_KEY` errors, or exit 4 on the first model call | The key is not set in this shell, or is wrong. Print whether it is set without showing it: `python -c "import os; print(bool(os.environ.get('OPENROUTER_API_KEY')))"` |
| Exit 4, or `[harness-error]` on standard error | The session's `worker-progress.log` and `call-trace.jsonl`. Common causes: a model that rejects the request format (try another; [Providers](providers.md)), a rate-limited free model, no credit for a paid model, or a provider timeout. |
| Exit 2 in a headless run | It stopped at a review gate: pipe `/confirm` lines, or run without `--review` |
| Exit 1 | The task failed its checks and its repairs: the transcript names each finding |
| Exit 5, or a result you doubt | The turn's `provenance.json`: the verification level (`host_verified`, `contract_checked` or `unverified`), the witness, and what was not established |

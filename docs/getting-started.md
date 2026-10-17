# Getting started

A setup runbook for agents and people: each step says what to run and what a correct result looks like. Steps 1 to 4 need no API key and no network; only step 5 calls a model.

## 1. Prerequisites

- **Python** 3.10 to 3.14 (the suite is run on 3.11), and `git`.
- **A sandbox backend.** Model-written programs run only under OS-native confinement; without it, PDLt fails closed and runs no program. See [SANDBOX.md](SANDBOX.md).

| OS | Backend | Needs |
|---|---|---|
| Windows | AppContainer | Nothing to install. Not the Microsoft Store build of Python, which cannot start a nested AppContainer. |
| Linux | Landlock | Kernel 5.13 or later, with Landlock enabled |
| macOS | Seatbelt | Nothing to install |
| Any | Container | Docker or Podman (`PDLT_SANDBOX=container`) |

## 2. Install

```bash
git clone https://github.com/paragon-ux/PDLt-Test.git
cd PDLt-Test
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

**Check:** `pdlt --help` prints the usage, and `python -c "import pdl_taskmaster.api"` exits 0.

## 3. Verify offline

```bash
python -m pytest -q -n auto
python -m pytest tests/test_harness_anti_overfitting.py -W error
```

**Check:** both report no failures.
- The first runs about 1,300 tests. Some are skipped: they test sandbox backends this OS does not have.
- The second is the integrity gate. It must pass with no warnings, failures or skips.

These need no key: models are scripted or replayed from recordings.

## 4. Check the sandbox

```bash
python -c "from pdl_taskmaster.api import create_sandbox; s = create_sandbox('auto', label='setup-check', require_confined=True); r = s.run_code('print(6 * 7)'); print(s.backend_name, r.exit_code, r.stdout.strip()); s.close()"
```

**Check:** it prints the backend, then `0 42`, for example `appcontainer 0 42`. If it raises `SandboxNotConfined`, no OS-native backend is available: fix that before any live run (step 1). For the escape tests: `python -m pytest tests/test_confinement.py -v`.

## 5. Configure a model and run a task

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."        # PowerShell: $env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

The same key serves the worker model and System 1, the classifier that routes each request.

**Through the Python API** (the primary entry point; [api.md](api.md)):

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="nvidia/nemotron-3-super-120b-a12b:free")
with Session.open(worker, "runs/sessions/setup-check", no_review=True) as session:
    result = session.send("Count the primes below 1000 and print the count.")
    print(result.stage, result.exit_status)
```

**Headless:**

```bash
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
echo $?
```

**Check:** stage `CLOSED_SUCCESS` and exit 0. A free model can also legitimately end in 1 (cancelled after failed repairs) or 5 (published but not established). Exit 4 is a provider or harness error: see "When something fails" below.

## 6. Choose how to use it

| Entry point | Start with |
|---|---|
| Python API | [api.md](api.md) |
| Extensions (task types, verifiers, providers) | [extensions.md](extensions.md) |
| MCP server, for other agents | [mcp/EXTERNAL_TOOLS.md](mcp/EXTERNAL_TOOLS.md), and the configuration below |
| REPL | `pdlt --new-session` (add `--review` for the review gates); commands in the [README](../README.md#repl-quickstart) |
| Headless | `pdlt --non-interactive`; exit codes in the [README](../README.md#headless-runs) |

**MCP server.** It serves the sandbox tools, and the closed sessions of one sessions folder as read-only resources. Every request is logged; it refuses to start without OS-native confinement.

```json
{
  "mcpServers": {
    "pdlt": {
      "command": "python",
      "args": ["-m", "pdl_taskmaster.host.mcp_server", "--sessions", "/path/to/PDLt-Test/runs/live-sessions"]
    }
  }
}
```

Flags: `--tier MINIMAL|STANDARD|HEAVY_COMPUTE` (the execution budget), `--witness-required`, `--sandbox auto|native|container`, `--sessions <folder>`, `--log <file>` (default: `mcp-server/` beside the sessions folder).

## Environment variables

| Variable | Effect |
|---|---|
| `OPENROUTER_API_KEY` | The key for the API worker and, by default, System 1 |
| `SYS1_API_KEY`, `SYS1_MODEL`, `SYS1_ENDPOINT` | System 1's own key, model or endpoint |
| `OPENROUTER_PROVIDER`, `OPENROUTER_PROVIDER_ORDER` | Pin the OpenRouter providers that serve requests |
| `PDLT_SANDBOX` | Sandbox mode: `auto` (default, native), `native`, `container`, or `audit-only` (an opt-out with no OS confinement) |
| `PDLT_CONTAINER_RUNTIME`, `PDLT_CONTAINER_IMAGE` | The container backend's runtime and image |
| `PDLT_SANDBOX_NETWORK`, `PDLT_POLICY_SCOPE`, `PDLT_KNOWLEDGE_CUTOFF` | The environment System 1 is told about when it decides whether a request is in bounds (ADR-0020) |
| `PDLT_TIER_D1` | `0` turns off feeding the model its own test failures (default on) |
| `PDLT_AGENT_TOOLS` | `1` turns on in-call tools (ADR-0029) |
| `PDLT_RESULT_IR` | `1` asks for a Result IR on every task, not only verified ones |
| `PDLT_CATALOGUE_RUNS` | Where catalogue runs are written (default: `PDLt-Catalogue-Archive` beside the checkout) |
| `PDLT_THEME`, `PDLT_USER_COLOR`, `PDLT_ASSISTANT_COLOR` | REPL colours |
| `PDLT_VIEWER_ROOT` | The root the local viewer reads (`python -m viewer`) |

## Where files are written

| What | Where |
|---|---|
| REPL and headless sessions | `runs/live-sessions/<session>/` in a checkout, else `~/.pdlt/runs/live-sessions/`. Each session folder holds `workspaces/`, `observations/`, `worker-progress.log` and `call-trace.jsonl`. |
| Library sessions | The folder passed to `Session.open`, laid out the same way |
| A published result | `<workspace>/turns/<turn>/stages/50_execution/output/`: `current.md`, `program-output.json`, `provenance.json` |
| MCP call log | `--log`, or `mcp-server/calls-<time>-<pid>.jsonl` beside the sessions folder |
| Catalogue runs | `$PDLT_CATALOGUE_RUNS`, else `PDLt-Catalogue-Archive` beside the checkout, never the repository |

## When something fails

| Symptom | Look at |
|---|---|
| `[warn] code execution unavailable` at REPL start | No OS-native backend: step 4 and [SANDBOX.md](SANDBOX.md) |
| Exit 4, or `[harness-error]` on stderr | The session's `worker-progress.log` and `call-trace.jsonl`. Common causes: a missing key, a model that rejects the request (try another; [providers.md](providers.md)), or a provider timeout. |
| Exit 2 in a headless run | It stopped at a review gate: pipe `/confirm` lines, or run without `--review` |
| A result you doubt | The turn's `provenance.json`: the level, the witness form, and what was not established |

## Evaluation catalogue (optional)

`python run_catalogue.py --dry-run` validates the 112-prompt manifest without calling a model. Live sweeps cost API credit; see [evaluation.md](evaluation.md) and [benchmarks.md](benchmarks.md). The local viewer (`python -m viewer`, http://127.0.0.1:8090) shows sessions and runs read-only.

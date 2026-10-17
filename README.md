# PDLt

**A protocol harness for verified, auditable model execution: a Python library first, with an MCP server, an interactive REPL and a headless CLI on top.**

[![License](https://img.shields.io/badge/License-Apache%202.0%20%2F%20MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-Zensical-purple.svg)](https://paragon-ux.github.io/pdlt-test/)
[![Python](https://img.shields.io/badge/python-3.10%20--%203.14-blue.svg)](pyproject.toml)

PDLt sits between a request and a model.
- **Interpretation:** the model restates the request as short pseudocode. In review mode, the run stops for confirmation before anything executes.
- **Sandboxing:** generated programs run in an OS-native sandbox (AppContainer, Landlock or Seatbelt).
- **Checking:** the host checks every reply against its contract and runs the programs itself.
- **Provenance:** every published result says what it rests on: `host_verified`, `contract_checked` or `unverified`.

The harness is a referee, never a solver: it adds no hints, keyword gates or fabricated witnesses (`docs/guardrails/`).

## Entry points

| Use | Entry point | Read |
|---|---|---|
| **Run tasks from Python** (primary) | `pdl_taskmaster.api`: `Session`, `TurnResult`, `create_worker`, `RunSettings` | [docs/api.md](docs/api.md) |
| **Add task types, verifiers or model providers** (SDK) | `register_task_type`, `register_verifier`, `register_provider`, plus a conformance kit | [docs/extensions.md](docs/extensions.md) |
| **Use PDLt from another agent** | MCP server: `python -m pdl_taskmaster.host.mcp_server` | [docs/mcp/EXTERNAL_TOOLS.md](docs/mcp/EXTERNAL_TOOLS.md) |
| **Work interactively** | REPL: `pdlt` | [REPL quickstart](#repl-quickstart) |
| **Automate (CI, scripts)** | Headless: `pdlt --non-interactive`, with exit codes | [Headless runs](#headless-runs) |

All of them go through the same library layer, and one conformance suite (`tests/test_interface_conformance.py`) checks that they agree on sessions, reviews, exit codes and provenance.

## Setup

Agents setting PDLt up should follow [docs/getting-started.md](docs/getting-started.md) step by step; each step ends with a check. The short version:

```bash
python -m pip install -e ".[test]"                       # Python 3.10 to 3.14
python -m pytest -q -n auto                               # offline suite: no API key, no network
python -m pytest tests/test_harness_anti_overfitting.py -W error   # integrity gate
export OPENROUTER_API_KEY="sk-or-v1-..."                  # for live runs only
```

## Python API

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="nvidia/nemotron-3-super-120b-a12b:free")
with Session.open(worker, "runs/sessions/demo", no_review=True) as session:
    result = session.send("Count the primes below 1000 and print the count.")
    print(result.text)
    print(result.stage, result.exit_status)        # e.g. CLOSED_SUCCESS 0
    if result.provenance:                          # present when a result was published
        print(result.provenance["verification"]["level"])
```

`Session.open` defaults to the review route (`no_review=False`): `send` then stops at the prompt review, and `confirm()` moves on, or `run(message, confirm=True)` accepts each review for you. See [docs/api.md](docs/api.md) for results, exit codes, providers, run settings, closed sessions and the sandbox.

## REPL quickstart

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."     # PowerShell: $env:OPENROUTER_API_KEY = "sk-or-v1-..."
pdlt --new-session                           # the unconfirmed route: no review gates
pdlt --new-session --review                  # stop at the prompt and the plan for review
```

| Command | Effect |
|---|---|
| `/confirm` | Accept the prompt or plan under review |
| `/revise <feedback>` | Ask for a revised prompt or plan |
| `/stop`, `/cancel` | Stop the task |
| `/no-review on\|off` | Turn the review gates off (the REPL's default) or on |
| `/fast on\|off` | Accept a review automatically when the host has no findings on it |
| `/worker <name>` | Switch to another worker provider |

Sessions are kept under `runs/live-sessions/` in a checkout (else `~/.pdlt/runs/live-sessions/`); `--session-id <name>` resumes one.

## Headless runs

```bash
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
echo $?
```

| Exit | Meaning |
|---|---|
| 0 | Closed with a result the host established or contract-checked; a direct reply; a published boundary refusal |
| 1 | Cancelled, or failed closed |
| 2 | Stopped at a review gate (pipe `/confirm` lines, or run without `--review`) |
| 3 | Waiting for input the task needs |
| 4 | Harness or provider error (never a protocol result) |
| 5 | Published, but not established by the host (`CLOSED_UNVERIFIED`) |
| 130 | Interrupted |

## Repository map

| Path | What it is |
|---|---|
| `src/pdl_taskmaster/api/` | The library layer every interface uses |
| `src/pdl_taskmaster/extensions/` | Versioned extension profiles, registries and the conformance kit |
| `src/pdl_taskmaster/runtime/` | Session engine, workspace, provenance, run settings |
| `src/pdl_taskmaster/providers/` | Model workers (`api_worker.py`) and System 1 (`sys1/`) |
| `src/pdl_taskmaster/verification/` | Sandbox, confinement backends, output verifier |
| `src/pdl_taskmaster/host/` | REPL, headless CLI, MCP server |
| `contracts/` | Hash-pinned operation contracts and the PDL Standard (`contracts/standards/`) |
| `tests/` | The offline suite (about 1,300 tests) |
| `run_catalogue.py`, `graders.py`, `prompts/` | The evaluation plane: the 112-prompt catalogue and its graders |
| `docs/` | Documentation; `docs/plans/LEDGER.md` records every decision |

Reviewers: start with [REVIEWER.md](REVIEWER.md). Agents working on the code: [AGENTS.md](AGENTS.md).

## Evaluation catalogue

`python run_catalogue.py --dry-run` lists the 112 prompts. Runs are written outside the repository, to `PDLt-Catalogue-Archive` beside the checkout, or to `$PDLT_CATALOGUE_RUNS` if set (`catalogue_runs.py`). See [docs/evaluation.md](docs/evaluation.md) and [docs/benchmarks.md](docs/benchmarks.md).

## Documentation

The full site is built with Zensical (`py -3.11 -m zensical serve`), from [docs/index.md](docs/index.md).

## License

Dual-licensed under Apache 2.0 and MIT. See [LICENSE](LICENSE).

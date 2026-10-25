# PDLt

**A protocol harness for verified, auditable model execution: a Python library first, with an extensions SDK, an interactive REPL, a headless CLI and an MCP server on top.**

[![PyPI](https://img.shields.io/pypi/v/pdl-taskmaster.svg)](https://pypi.org/project/pdl-taskmaster/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/paragon-ux/PDLt-Test/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-Zensical-purple.svg)](https://paragon-ux.github.io/PDLt-Test/)
[![Python](https://img.shields.io/badge/python-3.10%20--%203.14-blue.svg)](https://github.com/paragon-ux/PDLt-Test/blob/main/pyproject.toml)

PDLt sits between a request and a model.
- **Interpretation:** the model restates the request as short pseudocode. In review mode, the run stops for your confirmation before anything executes.
- **Sandboxing:** programs the model writes run under the operating system's own confinement (AppContainer on Windows, Landlock on Linux, Seatbelt on macOS), or in a Docker or Podman container you opt into. Without it, no program runs; the one opt-out, `--sandbox audit-only`, says so loudly ([Sandbox guide](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/SANDBOX.md)).
- **Checking:** the host checks every reply against its contract and runs the programs itself.
- **Provenance:** every published result says what it rests on: `host_verified`, `contract_checked` or `unverified`.

The harness is a referee, never a solver: it adds no hints, keyword gates or fabricated witnesses ([guardrails](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md)).

## Entry points

| Use | Entry point | Read |
|---|---|---|
| **Run tasks from Python** (primary) | `pdl_taskmaster.api`: `Session`, `TurnResult`, `create_worker`, `RunSettings` | [Python API](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/api.md) |
| **Add task types, verifiers or model providers** | Extensions SDK: `register_task_type`, `register_verifier`, `register_provider`, and a conformance kit | [Extensions SDK](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/extensions.md) |
| **Work interactively** | REPL: `pdlt` | [REPL quickstart](#repl-quickstart) |
| **Automate (CI, scripts)** | Headless: `pdlt --non-interactive`, with exit codes | [Headless runs](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/repl.md#headless-runs) |
| **Use PDLt from another agent** | MCP server: `python -m pdl_taskmaster.host.mcp_server` | [MCP server](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/mcp/EXTERNAL_TOOLS.md) |

All of them go through the same library layer. One conformance suite (`tests/test_interface_conformance.py`) checks that `Session`, the REPL and headless runs agree on sessions, reviews, exit codes and provenance, and that the MCP server serves the same provenance.

## Install

PDLt needs Python 3.10 to 3.14 and an OS-native sandbox, so setup differs by host. **Follow the page for your machine**: it gives every command, a check after each step, and troubleshooting. Agents doing the setup should follow it step by step.

| Host | Sandbox | Setup guide |
|---|---|---|
| Windows 10 or 11 | AppContainer | [docs/hosts/windows.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/windows.md) |
| Linux, kernel 5.13 or later | Landlock | [docs/hosts/linux.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/linux.md) |
| macOS | Seatbelt | [docs/hosts/macos.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/macos.md) |

In short, in a virtual environment:

```bash
python -m pip install "pdl-taskmaster>=2.6.0"   # from PyPI
python -m pip install -e ".[test]"               # or, from a clone of this repository
```

Live runs need an [OpenRouter](https://openrouter.ai) key in `OPENROUTER_API_KEY`; the offline test suite and the sandbox check need none.

## Python API

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="nvidia/nemotron-3-super-120b-a12b:free")
with Session.open(worker, "pdlt-sessions/demo", no_review=True) as session:
    result = session.send("Count the primes below 1000 and print the count.")
    print(result.text)
    print(result.stage, result.exit_status)        # e.g. CLOSED_SUCCESS 0
    if result.provenance:                          # present when a result was published
        print(result.provenance["verification"]["level"])
```

`Session.open` and `pdlt` share their defaults: saver mode with no review, on `openai/gpt-oss-120b` (ADR-0031, L165, L167; the example names the free model). Saver runs the protocol for what System 1 classes VERIFIED_EXECUTION and answers the rest directly. Review is the confirmed route, in protocol mode: `no_review=False` or `pdlt --review`. There `send` stops at the prompt review, and `confirm()` moves on, or `run(message, confirm=True)` accepts each review for you. [docs/api.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/api.md) covers results, exit codes, providers, run settings, closed sessions and the sandbox.

## Extensions SDK

Task types, verifiers and model providers are registered through versioned profiles (`pdlt.task-type/1`, `pdlt.verifier/1`, `pdlt.provider/1`). Registration validates a declaration and refuses it with every problem named; PDLt's own built-ins register the same way. `check_task_type` runs a declaration through real sessions offline before you rely on it. See [docs/extensions.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/extensions.md).

## REPL quickstart

bash (Linux, macOS):

```bash
export OPENROUTER_API_KEY="sk-or-v1-your-key"
pdlt --new-session                 # saver mode, no review gates (the default)
pdlt --new-session --review        # the confirmed route: stop at the prompt and the plan for review
```

PowerShell (Windows):

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-your-key"
pdlt --new-session
```

Type a task at the `>` prompt, for example `Count the primes below 1000 and print the count.`

| Command at the `>` prompt | Effect |
|---|---|
| `/confirm` | Accept the prompt or plan under review |
| `/revise <feedback>` | Ask for a revised prompt or plan |
| `/stop`, `/cancel` | Cancel the task |
| `/no-review on\|off`, `/fast on\|off` | Switch review mode |
| `/help`, `/quit` | Every command; leave |

Every command, flag and mode: [docs/repl.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/repl.md).

## Headless runs and the MCP server

**Headless** runs read tasks from a pipe or a file and exit with a code a script can test:

```bash
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
echo $?
```

| Exit | Meaning |
|---|---|
| 0 | Host-reproduced result (`CLOSED_SUCCESS`); a protocol bypass reply; a published boundary refusal |
| 1 | Cancelled, or failed closed |
| 2 | Stopped at a review gate |
| 3 | Waiting for input the task needs |
| 4 | Harness or provider error (never a task result) |
| 5 | Published, but not established by the host (`CLOSED_UNVERIFIED`) |
| 130 | Interrupted |

Contract-only published results and direct/saver answers exit 5. Exit 0 also covers a protocol bypass reply and a published refusal, so CI that requires a host-reproduced deliverable checks provenance too ([CI recipe](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/repl.md#check-the-verification-level-in-ci)). `host_verified` establishes reproduction, not general correctness. The PowerShell form and file input are in [docs/repl.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/repl.md#headless-runs).

**The MCP server** (`python -m pdl_taskmaster.host.mcp_server`, stdio) lets another agent run programs in PDLt's sandbox, have a deliverable checked, and read closed sessions' results with their provenance. It is a narrow service, not a remote session: it runs no PDLt session, and nothing verifies an accepted submission afterwards. One server process is one MCP session with its own budgets. Client configuration for each host is on the host pages; tools and resources are in [docs/mcp/EXTERNAL_TOOLS.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/mcp/EXTERNAL_TOOLS.md).

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
| `tests/` | The offline suite |
| `run_catalogue.py`, `graders.py`, `prompts/` | The evaluation plane: the 112-prompt catalogue and its graders |
| `docs/` | Documentation; `docs/plans/LEDGER.md` records every decision |

Reviewers: start with [REVIEWER.md](https://github.com/paragon-ux/PDLt-Test/blob/main/REVIEWER.md). Agents working on the code: [AGENTS.md](https://github.com/paragon-ux/PDLt-Test/blob/main/AGENTS.md).

## Evaluation catalogue

`python run_catalogue.py --dry-run` lists the 112 prompts (source checkout only). Runs are written outside the repository, to `PDLt-Catalogue-Archive` beside the checkout, or to `$PDLT_CATALOGUE_RUNS` if set (`catalogue_runs.py`). See [docs/evaluation.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/evaluation.md) and [docs/benchmarks.md](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/benchmarks.md).

## License

MIT. See [LICENSE](https://github.com/paragon-ux/PDLt-Test/blob/main/LICENSE) and [NOTICE.md](https://github.com/paragon-ux/PDLt-Test/blob/main/NOTICE.md).

## Documentation site

The full documentation is published at **[paragon-ux.github.io/PDLt-Test](https://paragon-ux.github.io/PDLt-Test/)**, built with Zensical from [`docs/`](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/index.md):

- **[Overview](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/index.md)**: what PDLt is, its entry points and its two planes.
- **Get started:** [choosing a host](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/getting-started.md), then [Windows](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/windows.md), [Linux](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/linux.md) or [macOS](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/hosts/macos.md).
- **Use PDLt:** [Python API](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/api.md), [Extensions SDK](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/extensions.md), [REPL and headless runs](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/repl.md), [MCP server](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/mcp/EXTERNAL_TOOLS.md).
- **Reference:** [environment variables, files and failures](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/reference.md), [providers and models](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/providers.md), [the OS sandbox](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/SANDBOX.md).
- **Design and evaluation:** [architecture and routing](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/architecture.md), [the catalogue](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/evaluation.md), [benchmarks](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/benchmarks.md).
- **Maintainers:** [releasing to PyPI](https://github.com/paragon-ux/PDLt-Test/blob/main/docs/releasing.md).

To build or preview it locally from a source checkout:

```bash
python -m pip install zensical==0.0.68
zensical build          # writes site/
zensical serve          # preview at http://localhost:8000
```

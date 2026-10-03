# PDL Taskmaster (lean build) and the PDLt System 2 Catalogue

A controller-gated REPL harness that has a model interpret your request as short, readable pseudocode and waits for confirmation before anything runs, plus the frozen **105-prompt catalogue** that measures it. Content quoted or pasted into a task stays passive data (semantic bootstrap containment).

Current design: [`ARCHITECTURE.md`](ARCHITECTURE.md). Direction (not yet implemented): [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md). Guardrails: [`docs/guardrails/`](docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md). Decisions: [`docs/adr/`](docs/adr/).

## Two planes

| Plane | Where | Knows the benchmark? |
|---|---|---|
| Harness | `src/pdl_taskmaster/` | **Never**: enforced by `tests/test_harness_anti_overfitting.py` |
| Evaluation | `run_catalogue.py`, `graders.py`, `prompts/` | Yes: drives runs and grades answers against `prompts/solutions/` |

The harness is a referee, never a solver: no algorithm hints, no keyword gates, no fabricated witnesses. A failed prompt is diagnostic data; a gamed pass is an integrity defect.

## Install and test (offline)

```bash
pip install -e ".[test]"   # Python 3.10+, pydantic v2
pytest -q                   # offline suite, includes the integrity gate
```

## Run

```bash
export OPENROUTER_API_KEY=...          # System 2 (default openai/gpt-oss-120b) and System 1
pdlt --new-session --dev                # interactive REPL
python run_catalogue.py --dry-run       # validate manifest, list prompts
python run_catalogue.py --prompt-id 06-04
python run_catalogue.py --category 13 --fail-fast
python run_catalogue.py                 # full 105-prompt run, one attempt each
python run_catalogue.py --regrade catalogue-runs/run-<ts>   # re-score a finished run, no model calls
```

REPL fast path: `/confirm`, `/revise <feedback>`, `/stop` or `/cancel`. `/help` in the REPL and `pdlt --help` list the rest.

On Windows, set the key with `setx OPENROUTER_API_KEY ...` (or `$env:OPENROUTER_API_KEY = '...'` for the current PowerShell session) and open a new terminal.

### Viewer (local browser)

```bash
python -m viewer                # http://127.0.0.1:8090, opens your browser; --no-open, --port N
```

Read-only and localhost-only. Browse every `catalogue-runs/run-*` (scoreboard, per-prompt verdict and ground-truth grade, transcript, deliverable, code, witness), follow the newest live session, and read the 105 catalogue prompts. It lives in the evaluation plane and imports nothing from the harness.

### Environment routing (System 1)

`PDLT_POLICY_SCOPE` (default `technical`), `PDLT_SANDBOX_NETWORK` (default `false`) and `PDLT_KNOWLEDGE_CUTOFF` (default `2024-06`) are **System 1 recipe state**. System 1 routes every new request against them before any System 2 call; they never appear in a System 2 prompt, and nothing matches keywords or dates. `PDLT_SANDBOX_NETWORK` only changes what System 1 is told: the sandbox never grants network access. System 1 is reached through OpenRouter; when it is unavailable, no boundary refusal is issued and the request goes ahead under the sandbox's limits.

## Exit codes (headless, ADR-0019 as amended)

| Code | Meaning |
|---|---|
| 0 | `CLOSED_SUCCESS`: verified deliverable, **or** a published boundary refusal (`closure=REFUSED`) |
| 1 | `CLOSED_CANCELLED`: cancel, verification failure after repair, or fatal error |
| 2 | `UNCONFIRMED_GATE`: halted at a review gate |
| 3 | `WAITING_INPUT`: paused for required input |
| 4 | Harness or provider error (for example a missing API key or a provider outage); not a protocol result |
| 130 | Interrupted (Ctrl+C) |

## Scoring

`run_catalogue.py` writes `catalogue-runs/run-<ts>/` with `RUN_META.json`, `SCOREBOARD.{json,md}` and per-prompt `result.json` + transcript. A prompt passes (`is_prompt_pass`) when it reaches its manifest stage **and** its ground-truth grade is not FAIL. `graders.py` grades answers (PASS / FAIL / MANUAL / N/A); a stage match with a FAIL grade is a **false positive**, reported by id and never counted as a pass. MANUAL prompts are listed for the human spot check. See [`GOAL.md`](GOAL.md) for the execution contract.

## Sandbox

Model-authored code runs in a session-scoped sandbox ([ADR-0021](docs/adr/0021-session-scoped-os-native-confinement.md)). Each program gets a fresh, empty directory under the system temp directory and may read and write only there; it can also read the base Python install. Other files, network access and starting processes are denied by the OS: Landlock on Linux, Seatbelt on macOS, an AppContainer on Windows, or a docker/podman container with `--sandbox container`. Programs also get an environment allowlist (no API keys), CPU and memory limits, and an in-process audit hook as defense in depth.

If the native confinement cannot apply (for example, Linux before 5.13), no program runs and the REPL says so. `--sandbox audit-only` (or `PDLT_SANDBOX=audit-only`) is the explicit opt-out: programs then run under the audit hook and limits only. This is not a VM boundary. See the [sandbox guide](docs/SANDBOX.md) for how it works and how to check it.

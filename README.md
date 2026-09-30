# PDL Taskmaster (lean build) and the PDLt System 2 Catalogue

A controller-gated REPL harness that has a model interpret your request as short, readable pseudocode and waits for confirmation before anything runs, plus the frozen **105-prompt catalogue** that measures it. Content quoted or pasted into a task stays passive data (semantic bootstrap containment).

Target design: [`TARGET_ARCHITECTURE.md`](TARGET_ARCHITECTURE.md). Guardrails: [`docs/guardrails/`](docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md). Decisions: [`docs/adr/`](docs/adr/).

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
```

REPL fast path: `/confirm`, `/revise <feedback>`, `/stop`. `pdlt --help` lists the rest.

## Exit codes (headless, ADR-0019 as amended)

| Code | Meaning |
|---|---|
| 0 | `CLOSED_SUCCESS`: verified deliverable, **or** a published boundary refusal (`closure=REFUSED`) |
| 1 | `CLOSED_CANCELLED`: cancel, verification failure after repair, or fatal error |
| 2 | `UNCONFIRMED_GATE`: halted at a review gate |
| 3 | `WAITING_INPUT`: paused for required input |

## Scoring

`run_catalogue.py` writes `catalogue-runs/run-<ts>/` with `RUN_META.json`, `SCOREBOARD.{json,md}` and per-prompt `result.json` + transcript. The pass definition (`is_prompt_pass`) is stage-based and unchanged; `graders.py` adds ground-truth grades (PASS / FAIL / MANUAL / N/A) and reports **false positives** (a stage pass with a wrong answer). See [`GOAL.md`](GOAL.md) for the execution contract.

## Sandbox

Model-authored code runs in a session-scoped subprocess sandbox with an environment allowlist (no API keys), an audit hook denying network and process creation, and CPU/memory limits. This is defense in depth, not a VM boundary.

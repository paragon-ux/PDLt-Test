# PDLt Taskmaster & The System 2 Catalogue

**Controller-gated REPL harness and evaluation platform for verified, auditable agentic execution.**

[![License](https://img.shields.io/badge/License-Apache%202.0%20%2F%20MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-Zensical-purple.svg)](https://paragon-ux.github.io/pdlt-test/)
[![Tests](https://img.shields.io/badge/offline%20contracts-85%2F85%20passing-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%20--%203.14-blue.svg)](pyproject.toml)

`PDLt` is a controller-gated REPL harness where models interpret user intent into concise, human-readable pseudocode and, in review mode (`--review`), halt for confirmation before synthesizing code. By default it runs the unconfirmed route: no review gates, no execution brief, Tier D1 repairs on. Content quoted or pasted into a task stays passive data (semantic bootstrap containment), and generated code executes strictly inside an isolated OS sandbox.

---

## Core Principles

- **Controller-Gated Execution**: With review on (`--review`, or `/no-review off`), review gates (`/confirm`, `/revise`) enforce human-in-the-loop auditability before code synthesis.
- **Two-Plane Separation**: The execution harness (`src/pdl_taskmaster/`) is strictly separated from the evaluation benchmark (`run_catalogue.py`), with zero benchmark leakage or keyword gaming.
- **Session-Scoped OS Confinement**: All model-generated code runs under OS-native sandboxing (Landlock on Linux, Seatbelt on macOS, AppContainer on Windows).
- **Four Execution Arms and a Control**: Routing from lean 2-call unconfirmed dispatch to human-reviewed gated execution, all with Tier-D1 sandbox feedback loops on by default, plus an unharnessed raw-model control for baseline comparison.

---

## Quickstart

```bash
# 1. Install harness and test suite
python -m pip install --upgrade pip
pip install -e ".[test]"

# 2. Run offline contract verification & anti-overfitting tests
pytest -q

# 3. Launch the interactive REPL
export OPENROUTER_API_KEY="sk-or-v1-..."
pdlt --new-session --dev
```

Common REPL commands:
- `/no-review on|off`: Turn the review gates off (the default) or on.
- `/confirm`: Approve pseudocode interpretation or execution plan.
- `/revise <feedback>`: Provide targeted revisions to the model.
- `/fast on|off`: Automatically accept pseudocode when no host lint findings exist.
- `/stop` or `/cancel`: Safely abort the active session.

---

## Comprehensive Documentation

For complete technical references, architectural specifications, and benchmark analyses, visit our **[Zensical Documentation Site](https://paragon-ux.github.io/pdlt-test/)**:

- 📖 **[Getting Started](docs/getting-started.md)**: Installation, CLI flags, offline test matrix, and localhost viewer.
- 🏗️ **[Architecture & Routing](docs/architecture.md)**: Multi-stage pipeline breakdown and the execution routes (four arms and a control).
- 📊 **[Benchmark & Four-Arm Parity](docs/benchmarks.md)**: The five-route sweep on the 112-prompt catalogue, Pareto frontier, paired tests and caveats.
- 🎯 **[Catalogue & Evaluation](docs/evaluation.md)**: The 112-prompt catalogue across 16 categories and ground-truth grading rules.
- 🛡️ **[OS Sandbox Confinement](docs/sandbox.md)**: Landlock, Seatbelt, and AppContainer security boundaries and session lifecycles.
- 🔌 **[Providers & Models](docs/providers.md)**: OpenRouter configuration, fallback tiers, and operation-level reasoning controls.

---

## Local Documentation Server

Build or serve the documentation locally using **Zensical**:

```bash
# Build static site
py -3.11 -m zensical build

# Serve live preview
py -3.11 -m zensical serve
```

---

## License

Dual-licensed under Apache 2.0 and MIT.

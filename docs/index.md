# PDLt Taskmaster & The System 2 Catalogue

**PDLt Taskmaster** is a protocol harness for verified, auditable model execution: a Python library first, with an extensions SDK, an MCP server, an interactive REPL and a headless CLI on top.

## Entry points

| Use | Entry point | Read |
| :--- | :--- | :--- |
| **Run tasks from Python** (primary) | `pdl_taskmaster.api`: `Session`, `TurnResult`, `create_worker`, `RunSettings` | [Python API](api.md) |
| **Add task types, verifiers or model providers** (SDK) | `register_task_type`, `register_verifier`, `register_provider`, plus a conformance kit | [Extensions](extensions.md) |
| **Use PDLt from another agent** | MCP server: `python -m pdl_taskmaster.host.mcp_server` | [MCP server](mcp/EXTERNAL_TOOLS.md) |
| **Work interactively** | REPL: `pdlt --new-session` | [Getting started](getting-started.md) |
| **Automate (CI, scripts)** | Headless: `pdlt --non-interactive`, with exit codes | [Getting started](getting-started.md) |

Setting PDLt up, for agents and people alike: follow [Getting started](getting-started.md) step by step; each step ends with a check.

---

## Core Premise: Controller-Gated Agentic Execution

Most agentic harnesses give large language models uncontrolled execution loops: the model generates code, runs arbitrary shell commands, and loops recursively without deterministic checkpoints or structured semantic bounds.

PDLt fundamentally shifts the paradigm:
1. **Semantic Bootstrap Containment**: Raw user text and untrusted prompt data remain passive data. The model cannot execute until interpretation and planning phases are complete.
2. **Controller-Gated Phases**: The model interprets user requests as short, human-readable pseudocode; in review mode, the run waits for confirmation before execution begins.
3. **OS-Native Confinement**: All generated code executes inside a restricted, session-scoped OS sandbox (Landlock on Linux, Seatbelt on macOS, AppContainers on Windows).
4. **Deterministic Delivery Verification**: Code and results are checked against formal output contracts, verification suites, and witness projections.

---

## The Two-Plane Separation

A foundational design invariant in PDLt is the strict separation between the execution harness and the evaluation benchmark:

```mermaid
graph LR
    subgraph HarnessPlane["Harness Plane (src/pdl_taskmaster/)"]
        H1["REPL Controller"]
        H2["State Machines"]
        H3["OS Confinement"]
        H4["Never knows benchmark questions or solutions"]
    end

    subgraph EvaluationPlane["Evaluation Plane (run_catalogue.py, graders.py)"]
        E1["Catalogue Manifest (112 prompts)"]
        E2["Solution Ground Truths"]
        E3["Automatic Graders"]
        E4["Multi-Arm Parity Sweeps"]
    end
```

| Plane | Location | Benchmark Knowledge | Enforced By |
| :--- | :--- | :--- | :--- |
| **Harness** | `src/pdl_taskmaster/` | **Zero** (cannot contain hints, regexes, or solutions) | `tests/test_harness_anti_overfitting.py` |
| **Evaluation** | `run_catalogue.py`, `graders.py` | Full access to ground truth solutions | Manifest integrity & automated grading |

The harness acts strictly as a referee, never a solver: no algorithm hints, no keyword gates, and no fabricated witnesses. A failed prompt is diagnostic data; a gamed pass is an integrity defect.

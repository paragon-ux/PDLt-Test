# PDLt as a library: `pdl_taskmaster.api` (v0)

The REPL, headless runs and the MCP server go through this layer (ledger L120). It is v0 and unversioned: names may change until it is.

| Need | Use |
|---|---|
| Run a task from Python | `Session.open(worker, folder)`, then `send`, `confirm`, `revise`, `stop`, `cancel` or `run` |
| A worker for a model | `create_worker("api", model=...)`, or your own provider via `register_provider` |
| The exit code a headless run would give | `TurnResult.exit_status`, or `exit_status(stage)` |
| Your own domain checkers | `Session.open(..., output_verifier=...)` |
| Results of closed sessions | `closed_turns(folder)` |
| A sandbox outside a session | `create_sandbox(mode, label=..., require_confined=True)` |

## A session

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="...")  # any model; the settings are ApiWorker's keywords
with Session.open(worker, "runs/sessions/demo") as session:
    review = session.send("...")              # stops at the prompt review: review.review == "prompt", exit 2
    result = session.run("...", confirm=True)  # or accept each review on a standing confirmation
    print(result.stage, result.exit_status, result.provenance["verification"]["level"])
```

- **The folder** holds the session's workspaces, observations, worker log (`worker-progress.log`) and call trace (`call-trace.jsonl`), as the REPL lays them out. Reopening the folder resumes its workspace (`restore=False` starts fresh). The layout is the REPL's: a session opened inside the REPL's sessions folder resumes there with `--session-id <folder name>`, and the other way round.
- **`no_review=True`** takes the unconfirmed route: one message, no prompt or plan review.
- **Review commands** are messages: `confirm()` is `send("/confirm")`; `revise(feedback)` is `send("/revise feedback")`. With no open review they are answered as such, never started as a request.
- **`run(message, confirm=True)`** accepts each review as a standing confirmation, recorded as one (`STANDING_CONFIRMATION` events, as the REPL's fast mode). An artifact the host has findings on is left open for review.
- **Errors:** a provider or transport error raises from `send` (a headless run exits 4 on it). The session stays usable.
- **`repo_root`** defaults to the checkout this package runs from (it holds the Standard, the operations and their schemas).

## The result of a message: `TurnResult`

| Field | Meaning |
|---|---|
| `text` | What the user would see: the review artifact, the published result, or a direct reply |
| `stage` | The protocol stage after the message; `None` when no instance is open (a direct reply, or a refusal) |
| `exit_status` | The headless exit code for that stage (below) |
| `closed` | The instance closed with this message |
| `review` | The review left open: `"prompt"`, `"plan"` or `None` |
| `refused` | System 1 refused the request at the boundary (ADR-0020) |
| `provenance` | For a published result: what it rests on and what it does not establish (`runtime/provenance.py`) |
| `workspace_path` | The session's workspace |

## Exit codes (ADR-0019 with its amendments)

One mapping, `api.outcome.exit_status(stage, refused=..., harness_error=...)`. The REPL's headless mode and `run_catalogue.py` use it.

| Code | Constant | When |
|---|---|---|
| 0 | `EXIT_SUCCESS` | `CLOSED_SUCCESS`; a direct reply; a published boundary refusal |
| 1 | `EXIT_CANCELLED` | `CLOSED_CANCELLED` (fail-closed) |
| 2 | `EXIT_UNCONFIRMED` | stopped at a review gate or any other non-terminal stage |
| 3 | `EXIT_WAITING_INPUT` | `WAITING_INPUT` |
| 4 | `EXIT_HARNESS_ERROR` | a harness or provider error; never a protocol result |
| 5 | `EXIT_UNVERIFIED` | `CLOSED_UNVERIFIED`: published without the host establishing it |
| 130 | `EXIT_INTERRUPTED` | interrupted by the user |

## Providers

A provider is a factory returning a worker: any object with `call(request) -> WorkerResult` (`providers/base.py`). If the worker has a `sys1_client`, System 1 uses it; without one, Phase 0 and the boundary refusal do not run (the engine never builds a network client itself).

| Name | Settings |
|---|---|
| `api` | `ApiWorker`'s keywords: `model`, `base_url`, `api_key_env`, `reasoning_effort`, `max_output_tokens`, `structured_output` and the rest. Request settings follow each model's OpenRouter metadata (L122). |
| `recorded` | `repo_root`, `evidence` (a `recorded-cases.json` fixture, or recorded evidence with `eval_root`), `case_ids` |

```python
from pdl_taskmaster.api import register_provider, create_worker

register_provider("mine", lambda **settings: MyWorker(**settings))
worker = create_worker("mine", endpoint="...")
```

`create_worker` with an unknown name raises `ValueError` naming the known ones. `register_provider` refuses to replace a name unless `replace=True`.

## Verifiers

The engine checks a result's witness against a registry of domain checkers (`verification/output_verifier.py`). PDLt ships none in the harness plane (ADR-0018): only the fallback runs. A caller may supply its own registry:

```python
from pdl_taskmaster.verification.output_verifier import OutputVerifier

verifier = OutputVerifier()
verifier.register(MyChecker())  # a BaseChecker whose name is the problem domain it checks
session = Session.open(worker, folder, output_verifier=verifier)
```

A registered checker is the caller's own verification. It changes what a result's provenance may claim, so it must be deterministic and must not solve the task (GUARD-01).

## Closed sessions

`closed_turns(folder)` lists the turns under a sessions folder that closed with a published result: `CLOSED_SUCCESS` or `CLOSED_UNVERIFIED`. Each `ClosedTurn` has `session`, `workspace`, `turn`, `status`, `artifacts()` (`response`, `program-output`) and `provenance()`. Read-only; nothing outside the folder is returned. The MCP server's resources are built on it.

## Sandbox

`create_sandbox(mode, label=..., require_confined=True)` returns an `ExecutionSandbox`. With `require_confined`, the audit-only opt-out raises `SandboxNotConfined`; the MCP server requires it. A session builds its own sandbox; pass `sandbox_mode` to `Session.open`.

## Not covered yet (L120 batch B2)

- A typed settings object: the REPL still copies run settings onto the engine from worker attributes (`app.py`).
- A task-type extension point (problem class, route, operations, accepted witness forms).
- System 1 as its own provider, apart from the worker.
- The direct-reply path still calls the worker from the host, outside the engine.

# PDLt as a library: `pdl_taskmaster.api` (v0)

The REPL, headless runs and the MCP server go through this layer (ledger L120). It is v0 and unversioned: names may change until it is.

| Need | Use |
|---|---|
| Run a task from Python | `Session.open(worker, folder)`, then `send`, `confirm`, `revise`, `stop`, `cancel` or `run` |
| A worker for a model | `create_worker("api", model=...)`, or your own provider via `register_provider` |
| System 1 apart from the worker | `create_system1("openrouter", ...)`, then `Session.open(..., sys1=...)` |
| Run settings (repairs, brief, tools, representation, review, sandbox, task type) | `RunSettings(...)`, then `Session.open(..., settings=...)` |
| The exit code a headless run would give | `TurnResult.exit_status`, or `exit_status(stage)` |
| A task type of your own, or pinning one | `register_task_type(declaration)`; `Session.open(..., task_type=...)` ([extensions.md](extensions.md)) |
| Your own domain checkers | `register_verifier(declaration)`, bound by a task type ([extensions.md](extensions.md)) |
| Results of closed sessions | `closed_turns(folder)` |
| A sandbox outside a session | `create_sandbox(mode, label=..., require_confined=True)` |

## A session

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="...")  # any model; the settings are ApiWorker's keywords
with Session.open(worker, "runs/sessions/demo", no_review=False) as session:  # review: the confirmed route
    review = session.send("...")              # stops at the prompt review: review.review == "prompt", exit 2
    result = session.run("...", confirm=True)  # or accept each review on a standing confirmation
    print(result.stage, result.exit_status, result.provenance["verification"]["level"])
```

- **The folder** holds the session's workspaces, observations, worker log (`worker-progress.log`) and call trace (`call-trace.jsonl`), as the REPL lays them out. Reopening the folder resumes its workspace (`restore=False` starts fresh). The layout is the REPL's: a session opened inside the REPL's sessions folder resumes there with `--session-id <folder name>`, and the other way round.
- **`no_review`** is True by default (L165): no prompt or plan review. `no_review=False` runs the confirmed route, in protocol mode; with no `mode` it selects protocol, and with `mode="direct"` or `"saver"` it raises `ValueError`, since neither has review.
- **`mode`** defaults to saver for the API worker (ADR-0031): the protocol's unconfirmed route for what System 1 classes VERIFIED_EXECUTION, a direct answer for the rest. `mode="protocol"` with `no_review=True` is the unconfirmed route for every request.
- **`mode="direct"` or `"saver"`** answers behind SECURE_GATEWAY ([routing.md](routing.md), section 7). A direct answer closes `CLOSED_UNVERIFIED` (exit 5), a gateway refusal REFUSED (exit 0). A folder keeps the mode it was opened in: reopening it in another mode raises `ValueError` (L153).
- **Review commands** are messages: `confirm()` is `send("/confirm")`; `revise(feedback)` is `send("/revise feedback")`. With no open review they are answered as such, never started as a request.
- **`run(message, confirm=True)`** accepts each review as a standing confirmation, recorded as one (`STANDING_CONFIRMATION` events, as the REPL's fast mode). An artifact the host has findings on is left open for review.
- **Errors:** a provider or transport error raises from `send` (a headless run exits 4 on it). The session stays usable.
- **One thread at a time.** A `Session` holds one engine and one workspace and has no locking: never call `send` or `run` on the same session from two threads or tasks at once. Concurrent tasks each get their own `Session.open`, with their own folder.
- **The defaults are the same in every interface:** saver mode, no review, in-call tools on except on the unconfirmed route, and `openai/gpt-oss-120b` (ADR-0031, L165 to L167). `ApiWorker(agent_tools=None)` takes the session's default; True or False sets it.
- **`repo_root`** defaults to the folder this package runs from: the checkout's root in a source install. `create_worker("api", ...)` defaults it the same way. The Standard, the operations and their schemas resolve from `$PDLT_STANDARDS_PATH`, else `<repo_root>/contracts/`, else contracts seeded with `pdlt init`, else the copies bundled in the package, so a PyPI install needs nothing here.
- **`task_type`** pins a registered task type for every request; without it System 1 classifies each request, and an unclassified one gets the default (STANDARD_EXECUTION).
- **`settings`** is a `RunSettings`: `max_repairs`, `draft_execute`, `agent_tools`, `representation`, `tier_d1`, `no_review`, `sandbox_mode`, `task_type`, `mode` and the optional execution/tool controls. It is validated when made, and every invalid field is named. Omitted `mode` and `agent_tools` remain `None` until the session resolves them against the destination, worker and review setting; equivalent typed/keyword forms use the same defaults, and explicit true/false or mode values win. For example, `RunSettings(agent_tools=True)` overrides an API worker constructed with `agent_tools=False`; the engine then applies operation eligibility and exclusions before attaching tools. Without a typed object, the session arguments and worker attributes supply the settings (`RunSettings.from_worker`). With it, pass `no_review`, `sandbox_mode`, `task_type` and `mode` inside it, not as separate arguments. Left unset, `sandbox_mode` comes from `$PDLT_SANDBOX` (default `auto`), and an API worker's `tier_d1` from `$PDLT_TIER_D1` (default on).
- **`sys1`** is the System 1 client the session asks (`create_system1`). Without it, the worker's is used; with it, a worker that has one uses the same.
- **A protocol bypass reply** (a request System 1 routes away from the protocol) comes back as `text`, with `stage` None and exit 0. The engine produces it from the user's own words. This is separate from the published answers in direct/saver mode, which close `CLOSED_UNVERIFIED` with exit 5.

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
| 5 | `EXIT_UNVERIFIED` | `CLOSED_UNVERIFIED`: published without the host establishing it (every result short of `host_verified`, L164) |
| 130 | `EXIT_INTERRUPTED` | interrupted by the user |

Exit 0 is a provenance claim, not a correctness claim: a result the host reproduced (`host_verified`), or a refusal. Since L164 a STANDARD_EXECUTION result that passed only the contract checks closes CLOSED_UNVERIFIED (exit 5). What a published result rests on is `provenance["verification"]["level"]` (`host_verified`, `contract_checked` or `unverified`). `host_verified` means a program the host ran reproduced the witness; with no domain checker registered, the host does not judge that witness correct (L140).

## Providers

A provider is a named factory for one role, registered against provider profile v1 (`pdlt.provider/1`):
- **`worker`:** returns an object with `call(request) -> WorkerResult` (`providers/base.py`).
- **`system1`:** returns an object with `is_configured` and `call(request) -> (answer, milliseconds)`.

System 1 is the session's `sys1`, else the worker's `sys1_client`. Without either, Phase 0 and the boundary refusal do not run: the engine never builds a network client itself.

A provider declares the settings it takes. An unknown setting is refused before the factory runs, and whatever the factory makes is checked against its role's interface before anything uses it (`ExtensionFailure`).

| Name | Role | Settings |
|---|---|---|
| `api` | worker | `ApiWorker`'s keywords: `model`, `base_url`, `api_key_env`, `reasoning_effort`, `max_output_tokens`, `structured_output` and the rest. Request settings follow each model's OpenRouter metadata (L122). |
| `recorded` | worker | `repo_root`, `evidence` (a `recorded-cases.json` fixture, or recorded evidence with `eval_root`), `case_ids` |
| `openrouter` | system1 | `Sys1Client`'s keywords: `api_key`, `endpoint`, `model`, `timeout` |

The REPL and headless runs take any registered worker provider: `--worker <name>`, with `--provider-setting KEY=VALUE` (repeatable; the value is read as JSON when it parses).

```python
from pdl_taskmaster.api import register_provider, create_worker

register_provider("mine", lambda **settings: MyWorker(**settings))
worker = create_worker("mine", endpoint="...")
```

`create_worker` with an unknown name raises `ValueError` naming the known ones. `register_provider` refuses to replace a name unless `replace=True`. It also takes a full declaration: `{"profile": "pdlt.provider/1", "name", "role", "factory", "settings"}`.

## Task types and verifiers

Task types and verifiers are extension points defined by versioned profiles: `pdlt.task-type/1` and `pdlt.verifier/1`. Registration validates a declaration and names every problem (`ProfileViolation`). The built-ins register the same way, and a conformance kit checks an extension against the profile. See [extensions.md](extensions.md).

Each session's verifier registry is built from the registered verifiers. `Session.open(output_verifier=...)` still replaces it whole, for callers that build an `OutputVerifier` themselves.

## Closed sessions

`closed_turns(folder)` lists the turns under a sessions folder that closed with a published result: `CLOSED_SUCCESS` or `CLOSED_UNVERIFIED`. Each `ClosedTurn` has `session`, `workspace`, `turn`, `status`, `artifacts()` (`response`, `program-output`) and `provenance()`. Read-only; nothing outside the folder is returned. The MCP server's resources are built on it.

## Sandbox

```python
from pdl_taskmaster.api import create_sandbox

with create_sandbox("auto", label="my-tool", require_confined=True) as sandbox:
    run = sandbox.run_code("print(6 * 7)")
print(run.success, run.exit_code, run.stdout)  # True 0 42
```

`create_sandbox(mode, label=..., require_confined=False)` returns an `ExecutionSandbox` ([Sandbox guide](SANDBOX.md)). The modes are `auto` (the host's native backend), `native`, `container` and `audit-only`. With `require_confined`, the audit-only opt-out raises `SandboxNotConfined`; the MCP server requires it. When confinement cannot apply, `run_code` runs nothing and returns a result whose `error` starts with `sandbox_unavailable:`; in a session that becomes the `SANDBOX_UNAVAILABLE` finding, which is never repaired. A session builds its own sandbox; pass `sandbox_mode` to `Session.open`.

## What is not an extension point

- **The core:** the stages, review gates and execution modes (`no_review`, standing confirmation), and the workspace structure.
- **Interfaces** (REPL, headless, MCP, and any future one) are clients of `pdl_taskmaster.api`, not extensions. The ones that run sessions (`Session`, the REPL, headless) must pass the interface conformance suite (`tests/test_interface_conformance.py`): the same scenarios, ending in the same state, with the same exit statuses and the same provenance. The MCP server runs no session; the suite checks that it serves the same provenance.
- **The Python API** is v0 and unversioned. Profiles carry versions; the API does not.

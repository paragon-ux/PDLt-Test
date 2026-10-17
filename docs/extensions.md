# Extending PDLt: task types, verifiers and providers

PDLt's extension points are defined by **versioned compatibility profiles** (ledger L124). A profile names the components an extension must provide and the invariants it must satisfy.

- **Validation:** registration checks a declaration against its profile and refuses it with every problem named.
- **Built-ins:** PDLt's own task types, verifier and providers register through the same call, with no special path.
- **Freezing:** a registered extension is frozen. What was validated is what runs; changing the declaration afterwards changes nothing.

| Extension point | Profile | Register with | Built in |
|---|---|---|---|
| Task type | `pdlt.task-type/1` | `api.register_task_type(declaration)` | `VERIFIED_EXECUTION`, `STANDARD_EXECUTION` (default) |
| Verifier | `pdlt.verifier/1` | `api.register_verifier(declaration)` | `witness-reproduction` |
| Provider | `pdlt.provider/1` | `api.register_provider(declaration)` | `api`, `recorded` (worker); `openrouter` (system1) |

**Not extensible:**
- the stages and review gates;
- the execution modes that affect review (`no_review`, standing confirmation);
- the workspace structure.

Interfaces (REPL, headless, MCP) are clients of `Session`: they pass a conformance suite instead of registering.

## What no extension can change

The host enforces these outside any extension's control (`tests/test_extension_invariants.py`):

- **Fail-closed:**
  - A checker that raises, or answers with anything but a `VerificationVerdict`, stops the turn with `ExtensionFailure`; nothing is published.
  - A classification that fails, or falls below the core floor (0.85), selects nothing.
  - A turn routed to a task type this process does not register is never resumed under another.
- **Sandbox confinement:** no profile has a sandbox component, and a checker never receives the sandbox. Programs run in the session's sandbox, whose mode is the run's (`RunSettings.sandbox_mode`).
- **GUARD-01:** no component carries text to the solver. A task type selects among instruction channels the host renders (`result_ir`, `witness`). Its classification criterion goes to System 1 only.
- **Anti-overfitting:** the harness plane registers no problem-specific verifier. An extension's checker is the caller's own, in the caller's code.
- **Provenance honesty:** the host computes the level (`runtime/provenance.py`), never the extension.
  - A task type bound to `verifier: "none"` is never above `contract_checked`.
  - A result is `host_verified` only when a program the host ran printed the witness.
  - A checker judges a copy of the witness, so it cannot change what the host records.
  - The record names the checker that judged the witness, when it is not the structural fallback.

## Writing a task type

A declaration is a mapping. This one is the sample outside type from the tests: it is recognised by a criterion and checks a computed witness with its own verifier.

```python
from pdl_taskmaster import api
from pdl_taskmaster.extensions.task_types import ROUTES

api.register_verifier({
    "profile": "pdlt.verifier/1",
    "name": "row-totals",            # what a task type binds
    "domain": "row-totals",          # the domain whose witnesses it judges (unique)
    "checker": RowTotalsChecker(),   # check(witness, constraints, *, body=None) -> VerificationVerdict
    "reproduction": "required",      # the only value v1 allows
})

api.register_task_type({
    "profile": "pdlt.task-type/1",
    "category": "ROW_TOTALS",
    "prompt": {
        "classification": {"criterion": "The task gives rows of numbers and asks for the total of each row."},
        "instructions": ["result_ir", "witness"],
    },
    "witness_forms": ["computed"],
    "deliverable": {"body": "text", "result_ir": "required"},
    "route": ["confirmed", "unconfirmed"],
    "operations": sorted(ROUTES["confirmed"].required | ROUTES["unconfirmed"].required),
    "verifier": "row-totals",
})
```

| Component | v1 values |
|---|---|
| `category` | The problem class, `^[A-Z][A-Z0-9_]{2,63}$`; `OTHER` is reserved |
| `prompt.classification` | `None`: no recipe; the type is reached only by pinning.<br>`{"criterion": text}`: 20 to 600 characters, asked of System 1 as "this category or OTHER".<br>`{"recipe": r, "selects": category}`: a System 1 recipe that may select only its own category, with `min_confidence` of at least 0.85. |
| `prompt.instructions` | Channels the host renders into EXECUTE: `result_ir`, `witness` |
| `witness_forms` | Accepted forms (ADR-0030): `computed`, `certificate`, `argued`, `negative`. May be empty. A witness of another form is a finding (`WITNESS_FORM_NOT_ACCEPTED`). |
| `deliverable` | `body: "text"`; `result_ir: "required"` or `"not_requested"` |
| `route` | Which fixed routes it runs on: `confirmed`, `unconfirmed` |
| `operations` | Every required operation of each declared route (`task_types.ROUTES`), plus `DRAFT_EXECUTE` if it wants the brief |
| `verifier` | A registered verifier name, or `"none"` |

**Invariants checked at registration:**
- The `result_ir` instruction matches the deliverable.
- The `witness` instruction, a non-empty `witness_forms` and a verifier come together or not at all.
- The witness travels in the Result IR.
- A bound verifier has a reproducible form (computed or certificate) to check.
- The operations cover each declared route.

**The default task type.** `register_task_type(declaration, default=True)` makes a type the default, which every unclassified request gets. It must be safe: no verifier, no witness forms, both routes, no recipe.

**Routing.**
1. A pinned type (`Session.open(task_type=...)`, or `--task-type` in the REPL) is used as given.
2. Otherwise each type with a recipe is asked in registration order. The first that chooses its own category at or above the floor is selected.
3. Anything else gets the default.

The boundary refusal (ADR-0020) and the budget refusal still apply to every type.

## Conformance-testing a task type

```python
from pdl_taskmaster.extensions.conformance import check_task_type

report = check_task_type(declaration, sample={"body": "```python\n...\n```", "result_ir": {...}})
assert report.ok, report
```

`check_task_type` registers the declaration for the duration of the check, then restores the registry. It also accepts a registered category's name. It runs offline: a scripted worker and a scripted System 1 drive real sessions. The checks are:

| Check | What it establishes |
|---|---|
| `profile` | The declaration conforms (every problem named) |
| `classification` | Its recipe selects it when sure, and not when unsure or undecided |
| `route:<route>` | On each declared route, the sample closes with a published result. Only declared operations run, no classification text reaches the solver, and the provenance names the category and claims no more than the binding allows. A witness-checking type's sample must be host-verified. |
| `unreproduced-witness` | For witness-checking types: a witness stated only in the Result IR is never host-verified |
| `sample` | A witness-checking type supplies a sample: a deliverable whose program prints a witness its verifier accepts |

A report prints as a checklist. Each failing check lists its problems, for example: `route:confirmed: the sample did not close with a published result: stage CLOSED_CANCELLED, ...`.

## Verifiers

A checker must be deterministic. It reads only the witness and the constraints it is given (the prompt and plan bodies, the requirements, the domain), and it must not solve the task. It judges a copy, and its verdict never establishes a result alone: the host must also have reproduced the witness (`reproduction: "required"`).

## Providers

```python
api.register_provider({"profile": "pdlt.provider/1", "name": "mine", "role": "worker",
                       "factory": lambda *, endpoint: MyWorker(endpoint), "settings": ["endpoint"]})
worker = api.create_worker("mine", endpoint="...")
```

- **Roles:** `worker` (`call(request) -> WorkerResult`) or `system1` (`is_configured`, and `call(request) -> (answer, milliseconds)`).
- **Settings:** `"any"`, or the names the factory takes. Unknown ones are refused before the factory runs.
- **Interface check:** whatever the factory makes is checked against its role before use.
- **From the REPL:** `pdlt` offers only the providers registered in its own process; there is no plugin discovery. To use yours from the REPL or a headless run, start `pdlt` from a launcher script that registers it first:

    ```python
    # my_pdlt.py
    from pdl_taskmaster import api
    from pdl_taskmaster.host.cli import main

    api.register_provider({"profile": "pdlt.provider/1", "name": "mine", "role": "worker",
                           "factory": lambda *, endpoint: MyWorker(endpoint), "settings": ["endpoint"]})
    raise SystemExit(main())
    ```

    Then `python my_pdlt.py --worker mine --provider-setting endpoint=...` takes every `pdlt` flag, and `--help` lists `mine` among the workers. Task types and verifiers registered the same way are available to `--task-type`.

## Interfaces

A new interface is a client of `Session`. It conforms when it passes the scenarios of `tests/test_interface_conformance.py`: confirmed success, stopping at a review, cancelling, host-verified, unverified, the unconfirmed route, a stray `/confirm`, and a direct reply. Each must end in the same state, with exit statuses from `api.exit_status`, and with the same provenance the MCP server serves.

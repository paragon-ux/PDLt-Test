# L120 batch B2: contract-based extension points (work list)

Ledger L124. Plan set by the user, 2026-10-16 (main chat). They declined the earlier recommendation to limit task types to the existing set, because that would keep the API monolithic.

## Fixed decisions (the user)
- **Profiles:** extension points are defined by versioned compatibility profiles (required components plus invariants). Registration validates against the profile. Built-ins register through the same path.
- **Order:** task types first, then providers and verifiers.
- **Stages** stay in the core and fixed. Task types attach behaviour at defined points; they cannot add or redefine stages.
- **Interfaces** (REPL, headless, MCP) are clients of Session: they get a conformance suite, not registration.
- **Execution modes** that affect review gates (`no_review`, standing confirmation) are not extensible in B2.
- **Versions:** profiles are versioned (task-type profile v1). The Python API stays v0 and unversioned.
- **Core invariants** no extension overrides: fail-closed behaviour, sandbox confinement, GUARD-01, the anti-overfitting rules, provenance honesty.
- **Out of scope:** extensible stages, workspace structure and execution modes; live or paid runs; freezing the Python API.
- **Process:** one check-in, at D1. Flag the two timing flakes separately; they do not block merges.

## Deliverables

| | Deliverable | Status |
|---|---|---|
| D1 | Task-type profile v1: schema, validation, routing design | done (summary sent 2026-10-16) |
| D2 | Built-ins migrated; offline parity (worker requests, stages, exit codes, provenance) | open |
| D3 | Invariants enforced at runtime; misbehaving-extension tests | open |
| D4 | Task-type conformance kit; built-ins and an external sample pass; a broken sample fails | open |
| D5 | Providers and verifiers on the same mechanism | open (verifier profile v1 built in D1) |
| D6 | Interface conformance suite: REPL, headless, MCP | open |
| D7 | Typed settings, System 1 as its own provider, direct reply inside the turn API | open |
| D8 | docs/api.md, docs/extensions.md, ledger, where-PDLt-stands note | open |

## D1 design (`src/pdl_taskmaster/extensions/`)

**Mechanism (`profiles.py`).**
- A `Profile` has a kind, a version (`pdlt.<kind>/<n>`), the required components and the invariants.
- A declaration is a mapping of components plus `profile`.
- `Registry.register` validates the declaration and raises `ProfileViolation`, naming every missing component, invalid component, unknown key and broken invariant. Invariants are checked only once every component conforms.
- A registered extension is built into a frozen object.

**Task-type profile v1 (`task_types.py`, `pdlt.task-type/1`).**

| Component | Values |
|---|---|
| `category` | The problem class, `^[A-Z][A-Z0-9_]{2,63}$`; `OTHER` is reserved |
| `prompt.classification` | `None` (no recipe), `{criterion: text}` (a core-owned System 1 question: the category or OTHER), or `{recipe, selects}` (a System 1 recipe; it may select only its own category, with `min_confidence` of at least 0.85) |
| `prompt.instructions` | Host-rendered channels EXECUTE receives: `result_ir`, `witness`. No free text reaches the solver. |
| `witness_forms` | A subset of computed, certificate, argued, negative (ADR-0030); may be empty |
| `deliverable` | `body: "text"`; `result_ir: "required"` or `"not_requested"` |
| `route` | A subset of the fixed routes `confirmed` and `unconfirmed`; at least one |
| `operations` | Contract operations: every required operation of each declared route, plus the optional `DRAFT_EXECUTE` |
| `verifier` | A registered verifier name, or `"none"` |

Invariants:
- **result-ir-channel:** the `result_ir` instruction is sent exactly when `deliverable.result_ir` is required.
- **witness-binding:** the `witness` instruction, a non-empty `witness_forms` and a verifier other than `"none"` come together or not at all.
- **witness-in-result-ir:** the `witness` instruction requires the `result_ir` instruction.
- **reproducible:** a bound verifier needs at least one reproducible form (computed or certificate) among the accepted forms.
- **operations-cover-routes:** the operations cover every declared route, and none belongs to an undeclared route.
- **Default:** the task type registered with `default=True` must be safe: no verifier, no witness forms, both routes, no recipe.

**Verifier profile v1 (`verifiers.py`, `pdlt.verifier/1`).**
- Components: `name`, `domain` (unique), `checker`, and `reproduction`, which only accepts `"required"`: a checker never establishes a result without the host reproducing the witness.
- Built-in: `witness-reproduction`, the FallbackChecker under domain `general`.

**Built-ins.**
- VERIFIED_EXECUTION: the ProblemClassRecipe selecting VERIFIED_EXECUTION; instructions result_ir and witness; all four forms; result_ir required; both routes; verifier `witness-reproduction`.
- STANDARD_EXECUTION: no recipe, no instructions, no forms, verifier `none`; it is the default.

**Routing (`select`).**
1. The boundary refusal (ADR-0020) runs first, unchanged, for every type.
2. A pinned task type is used as given. It must run on the turn's route; an unknown name is an error before any call.
3. Otherwise, every task type that has a recipe and runs on the turn's route is asked in registration order. The first whose recipe chooses its own category, passing the gate and the core floor (0.85), is selected.
4. Everything else gets the default task type:
   - no System 1;
   - a call that fails;
   - a verdict below the floor;
   - a verdict naming no registered category.
5. A category with no recipe is reachable only by pinning.
6. A turn recorded under a category this process does not register is not resumed under another category: the restore fails closed, and the host starts fresh protocol state with a notice.
7. Whatever is selected, the guardrails stay the core's:
   - the budget refusal for any witness-requiring type;
   - sandbox confinement;
   - provenance computed by the host and capped by the binding: `verifier: "none"` never yields more than contract_checked.

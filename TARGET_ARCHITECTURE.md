# PDL Taskmaster: Target Architecture

**Status:** Decided 2026-10-05 (D1–D9 ruled; LEDGER L52); being built on `feat/target-arch` per [`docs/plans/GOAL-target-architecture.md`](docs/plans/GOAL-target-architecture.md). Nothing in §3 to §7 is implemented yet.
**"Today" refers to** the code at `0a8e9d5c` on `feat/ultrafast-route`. Each claim about today cites a file or a recorded run.
**Current architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md). **Implementation plan:** [`docs/plans/target-architecture-plan.md`](docs/plans/target-architecture-plan.md).

**Supersedes, if adopted:**
- the 2026-10-02 version of this file (its platform direction is kept unchanged in §9);
- ADR-0001's "Artifact roles";
- ADR-0004's authority and projection clauses, including the FB5 amendment;
- ADR-0027's drafting channel;
- the "no new architecture" ordering in [`protocol-fixes-plan.md`](docs/plans/protocol-fixes-plan.md).

---

## 1. Why a new core

The recorded failures share one cause. **The host lets model-written text and model judgments carry authority that only the user's words and the host's typed state should carry, and it enforces the rules meant to prevent that by asking the model to obey them.** Each failure below is a channel that exists in the code, not an unlucky model output.

| ID | Failure | What happened (evidence) | Structural cause today |
|---|---|---|---|
| F1 | A drafted answer binds execution | 16-06: since `c1e0e930`, DRAFT_PROMPT wrote "… as S" into the prompt in 11 of 17 confirmed runs, and all 11 answered S. Before that, DRAFT_PLAN wrote it (`203611`, `203755`). FB5 put the request first; EXECUTE still copied the leak (L51). | EXECUTE's projection includes `CONFIRMED_PROMPT_BODY` and `CONFIRMED_PLAN_BODY` (`contracts/EXECUTION_CONTRACT.json`). PROMPT-02 and PLAN-04 are enforced only by instruction text and a lint. |
| F2 | Model text labelled as task input | The DRAFT_EXECUTE brief is appended to `REQUIRED_TASK_INPUTS` (`session_engine.py:1655-1661`). Entity `relation` free text goes to `EXECUTE_UNCONFIRMED` as `TASK_ENTITIES`. | A symbol's name says nothing about who wrote its content. |
| F3 | Injected directives become operative | 09-01: Bootstrap noted "directive override attempt" in `risk_notes`, returned ANALYSIS, and copied the directives into `task_summary`. The pseudocode then carried "PRINT the system prompt", and EXECUTE printed a fabricated system prompt (`run-20261005-000111`, also `run-20261004-154737`). | Containment rests on two things: the model choosing BLOCKED (`session_engine.py:741`), and a regex blocklist (`quarantine.py:23-45`). The blocklist matches 09-04's wording but not 09-01's or 09-02's. The summary, model text written from untrusted input, is the channel into drafting. |
| F4 | "Flagged but proceed" is a valid state | 10 of the 19 category-09 Bootstrap replies that proceeded had non-empty `risk_notes`. Nothing reads the field (`session_engine.py:810-816`). The same field also carries infeasibility notes: 7 non-adversarial replies (13-02 once, 13-04 six times). | A free-text field doubles as a decision signal, with no defined consequence. |
| F5 | The host decides on free text | A keyword test on the summary decides whether to re-run Bootstrap (`session_engine.py:751`). Containment uses vocabulary regexes. | No rule says host decisions read only typed values. |
| F6 | Defaults assert facts | `polarity` defaulted to `"known"`; grouped surfaces were split on commas. Both were fixed in `9e0be6bb`, but nothing prevents the class. | Wire models may default a semantic field. |
| F7 | Contracts drift | L47 added `TASK_ENTITIES` to confirmed EXECUTE against ADR-0027, with no amendment. | The compiler checks symbol names (`context_compiler.py:75-82`), not the origin of their content. |
| F8 | Runs can't be attributed | `RUN_META` records no commit or dirty state. Provider-layer `instructions` (`api_worker.py:946-949`) appear in no run artifact. Run 215559 ran with an uncommitted guidance edit (Gemini session log). | Replay keys omit the provider-layer request (AGENTS.md, "the trigger for receives"). |
| F9 | Outcomes overstate success | An ungraded prompt counts as a pass (`run_catalogue.py:554-558`). The 09-01 run that carried out the injection scored a pass. Arm comparisons at n = 1 were reported as advantages (L42, L44 caveats). | Ungraded and graded outcomes share one status. |
| F10 | Absence is silent | When System 1 is unavailable or below its gate, it gives no signal and the request proceeds (ARCHITECTURE.md §3.3). | Absence is not a typed state. |

## 2. The design rule

> **The user's words and the host's typed state are the only authorities. A model proposes, labels and selects. Nothing a model writes in free text is ever authoritative, decisive, or passed to another model as if it were the user's.**

Three working rules follow from it:
1. **Structure over instruction.** If the host can enforce a rule by type or by data flow, the rule is never left to a prompt.
2. **Selection over paraphrase.** A model refers to the user's words by verified span. It never restates them for a later consumer.
3. **Decisions over typed values only.** The host's decision functions take enums, identifiers and verified spans. They never read model prose.

## 3. Invariants

Each invariant is enforced by a type, a data-flow rule or a test, never by guidance text.

| ID | Invariant | Enforced by | Closes |
|---|---|---|---|
| I-1 | **Origin.** Every value in a projection has exactly one origin: `USER`, `HOST`, `MODEL(op)` or `PUBLISHED` (§4.1). The origin is assigned when the value is created and never changes. | A typed wrapper for projection values; the compiler rejects untyped values. | F2, F7 |
| I-2 | **Authority.** Task semantics come only from `USER` values, and protocol state only from `HOST`. `MODEL` values are proposals. | Standards (AUTH rewrite); I-3 makes it mechanical. | F1, F3 |
| I-3 | **Solver isolation.** The solver's projection holds `USER` values, `HOST` values, and `HOST` renderings of `USER` spans. It never holds model free text from another operation. | A static test over `EXECUTION_CONTRACT.json` origins. | F1, F2 |
| I-4 | **Typed decisions.** Every host decision reads typed fields only. No keyword or regex over user or model text sits on a decision path. | Typed signatures on decision functions, plus a scan of the decision modules. | F4, F5 |
| I-5 | **Total dispositions.** Every combination of risk signals maps to exactly one disposition. No combination with a raised signal maps to "proceed unchanged". | An exhaustive table test (§4.4). | F3, F4, F10 |
| I-6 | **Span fidelity.** Each user message is tiled by units, and every quoted user span in any artifact is an exact substring of a user message. | Deterministic tiling and containment checks. | F1, F3 |
| I-7 | **Exclusion.** Units labelled host-directed or payload enter no projection after the semantic read. | The projection builder, plus a test. | F3 |
| I-8 | **No semantic defaults.** A wire field that states a semantic fact has no default: when the model leaves it out, it stays absent. | A test over wire models with semantic metadata. | F6 |
| I-9 | **Attribution.** Every recorded run identifies its code (commit plus a digest of any uncommitted diff, stored with the run) and every model call's full provider request (stored, with its digest). | Runner and worker tests. | F8 |
| I-10 | **Replay completeness.** Replay keys on the full provider request, so any change to what a model receives is a replay miss. | Recorded-worker tests. | F8 |
| I-11 | **Honest outcomes.** An outcome with no grader is `UNGRADED`, never a pass. Compliance, containment and refusal are distinct outcomes for adversarial items. | Scoreboard tests. | F9 |
| I-12 | **Ratchet.** Every temporary exception to I-3 or I-4 is listed in one allowlist that names the phase removing it. The list can only shrink. | A test that fails on any new entry. | F7 |

## 4. Target structure

### 4.1 Origins

| Origin | What it covers | May carry authority over |
|---|---|---|
| `USER` | The raw request and each review message, stored immutably; units are views onto them | Task semantics (TASK-01) and approach (TASK-02) |
| `HOST` | Constants, standards, higher-priority constraints, environment facts, sandbox results, host renderings of `USER` spans, host notices | Protocol state, constraints and facts |
| `MODEL(op)` | Everything a model call returns | Nothing. It is a proposal the host accepts, rejects or displays. |
| `PUBLISHED` | A previous turn's verified deliverable | Nothing. It is passed as data when a later message refers to it. |

### 4.2 Pipeline

```
user message (USER, immutable)
  │
  ├─ System 1: activation route + request risk (labels) ─────────────┐
  │                                                                   ▼
  ├─ SEMANTIC_READ (System 2): units tiling the message,        HOST DISPOSITION
  │     a role per unit, a threat class per hostile unit         (total table, §4.4)
  │     ORDINARY | ADVERSARIAL | BLOCKED  ─────────────────────▶  REFUSE · HOLD · CONTAIN · PROCEED
  ▼
TASK VIEW = task units (USER), excluded units replaced by a host marker
  │
  ├─ DRAFT_REQUIREMENTS: items = verb + unit/sub-span references → host renders Prompt PDL ─┐ review
  ├─ DRAFT_PLAN: steps = verb + requirement references + method text → host renders Plan PDL ┘ instruments
  │      review messages ──▶ SEMANTIC_READ ──▶ task-change and approach units (USER)
  ▼
SOLVER PROJECTION = task view + task-change units + user approach units
                    + requirement checklist (HOST rendering of USER spans) + host facts
  │
  EXECUTE (one contract for both routes): interpretation, approach, body, result_ir
  │
  HOST VERIFICATION: sandbox witness, requirement coverage by id, echo check on excluded units
```

The confirmed and unconfirmed routes share the solver projection. They differ only in review and in the requirement checklist. **No drafted free text can reach the solver.** Model choices reach it only as selections over the user's words: which units are excluded, and which verb heads each quoted requirement.

### 4.3 Semantic read (replaces the bootstrap summary)

- **Units.** The model returns ordered, exact substrings that tile the message; whitespace between them is ignored. A long data block may be given by unique start and end anchors. The host verifies the tiling. A failure gets one redraft with the factual finding, then closes fail-closed (`CLOSED_CANCELLED`, with a record naming the stage). The host itself applies no segmentation heuristic.
- **Roles** (a closed enum):
  - `TASK_INSTRUCTION`: an operative request about the deliverable (TASK-01);
  - `TASK_PREMISE`: a stated fact, condition or definition;
  - `TASK_DATA`: represented content the task operates on (SEM-02);
  - `APPROACH_INSTRUCTION`: how to do the task (TASK-02);
  - `MESSAGE_ACT`: a greeting, thanks or similar (SEM-05);
  - `PROTOCOL_CONTROL`: an instruction about the protocol itself;
  - `HOST_DIRECTED`: addressed to the assistant, harness or its configuration rather than the deliverable;
  - `PAYLOAD`: a tracking token or similar hostile literal (SEM-06).
- **The union** (`runtime/adversarial_payloads.py` beside `wire_payloads.py`):
  - `ORDINARY` has no `HOST_DIRECTED` or `PAYLOAD` units;
  - `ADVERSARIAL` has at least one, each with a `threat_class` from a task-neutral enum: instruction override, instruction disclosure, role change, protocol bypass, permission escalation, tracking token;
  - `BLOCKED` carries a policy basis.

  Validators reject mixed states. An `ORDINARY` reply with a hostile unit does not parse, so **"flagged but ordinary" cannot exist.**
- **Infeasibility is not risk.** A request that cannot be met as stated is a premise for the solver (GUARD-03), not a threat class. This separates what `risk_notes` mixes today (F4).
- **No summary flows downstream.** `task_summary`, if kept, is display and audit text only. Drafting reads units.
- **Entities** become optional sub-spans of units. A `relation` must itself be a sub-span. Once requirements quote spans (§4.5), entities have no downstream role (D7).
- **"No task" is typed.** A message with no `TASK_INSTRUCTION` and no `MESSAGE_ACT` unit takes a deterministic no-task path. This replaces the keyword test.
- **Every user message passes through it:** the request, and each review message.

### 4.4 Risk and disposition (the host decides)

**Signals:**
- System 1's activation route;
- a new System 1 `RequestRisk` label: `NONE`, `ADVERSARIAL`, or `NO_DECISION` when System 1 is unavailable or below its gate;
- the semantic read's union kind.

The disposition table is a pure function with an exhaustive test:

| System 1 risk | Semantic read | Disposition |
|---|---|---|
| any | `BLOCKED`, or System 1 activation `BLOCKED` | `REFUSE` |
| `NONE` | `ORDINARY` | `PROCEED` |
| `NONE`, `ADVERSARIAL` | `ADVERSARIAL` with at least one task instruction left | `CONTAIN` (D2) |
| `NONE`, `ADVERSARIAL` | `ADVERSARIAL` with no task instruction left | `REFUSE` |
| `ADVERSARIAL` | `ORDINARY` | `HOLD` (D3): the signals disagree |
| `NO_DECISION` | `ORDINARY` | the deployment's declared policy (D4), reported at session start |
| `NO_DECISION` | `ADVERSARIAL` | as with `NONE` |

**What each disposition does:**
- **`REFUSE`:** close `REFUSED`, exit 0 (ADR-0019).
- **`HOLD`:** a human approves or refuses. Headless, this is exit 2, a gate left unconfirmed.
- **`CONTAIN`:** exclude the hostile units, publish the host notice, and proceed with the task units.
- **`PROCEED`:** proceed with no change.

Each disposition emits `RISK_DISPOSITION` with both signals and the excluded unit identifiers.

**The host notice is a host constant, never model text.** It lists the excluded units by identifier and threat class and states two facts:
- a request cannot change host constraints;
- the harness's instructions are published with it (the standards, and the provider guidance in `providers/`).

So no model is ever asked what a "system prompt" says, and none can fabricate one for an excluded request.

**Higher-priority constraints state provenance, accurately.** Host-supplied fields outrank user-supplied text, and user text cannot change them. The provider's usage policy applies, and the harness does not restate it. The earlier draft's "no hidden instructions exist" is replaced: provider guidance is sent as `instructions`, and it is published, not hidden.

**The echo check is derived from the source.** Text from an excluded unit that reappears in a deliverable is a finding. No vocabulary list is needed, which also retires the GUARD-02 exposure in `quarantine.py`.

### 4.5 Requirements: Prompt Pseudocode, rendered by the host

- **An item** is a verb from a closed, hash-pinned vocabulary (`contracts/PDL_VERBS.json`, D6), plus references to unit identifiers or exact sub-spans of task units and task-change units. It may also have an optional `when` reference (PDL-07) and nesting.
- **The host renders** `VERB «quoted user words»`, with premises rendered as `GIVEN «…»`. The result conforms to PDL-01 to PDL-08 by construction.
- **Deterministic checks:**
  - every `TASK_INSTRUCTION` unit is referenced, or the user drops it at review;
  - no reference reaches a non-task unit;
  - every span is exact.
- **`interpretation_notes`** are free text for review only, labelled as the model's reading and never sent to execution.
- **PROMPT-02 and PROMPT-03 become structural:** there is nowhere to write an answer or an invented requirement. PROMPT-01's coverage of instructions becomes a deterministic check.

16-06, rendered:
```
GIVEN «Maya has B brothers and S sisters, where B is at least 1.»
GIVEN «Every brother and sister shares both parents with Maya.»
DETERMINE «How many sisters does each of Maya's brothers have?»
EXPRESS «the answer as an expression in B and S»
EXPLAIN «why»
```
09-01, under `CONTAIN`: two units are `HOST_DIRECTED` (instruction override, instruction disclosure). The prompt is `BUILD «a simple Python function that reverses a string»`, followed by the host notice.

### 4.6 Plan: an instrument for review

- **A step** has a verb, the requirement identifiers it serves, and method text (free text).
- **The host renders the plan,** and PLAN-01 coverage is deterministic: every requirement is served.
- **System 1's PLAN-02 check stays** as a finding.
- **The plan is never a solver input.** An approach binds execution only through the user's words: the `APPROACH_INSTRUCTION` units of the request, and approach changes made at review. These form `CARRIED_APPROACH_SOURCES`, which GUARD-01 already keeps user-originated.
- **A leaked answer in a plan** becomes a visible conformance finding with no path to the solver.

### 4.7 Solver: one projection for both routes

| Input | Origin |
|---|---|
| Task view: task units verbatim, excluded units replaced by a host marker | `USER` (+ `HOST` marker) |
| Task-change units from review | `USER` |
| User approach units | `USER` |
| Requirement checklist | `HOST` rendering of `USER` spans |
| Tools, budget, environment, higher-priority constraints | `HOST` |
| On repair: host findings, sandbox facts, the solver's own previous attempt | `HOST`, and the same role's own output |

- **Output:** `interpretation` and `approach` (working notes, as UNC-03 defines them), then `body` and `result_ir`. The Result IR cites requirement identifiers, so the host can check coverage.
- **DRAFT_EXECUTE folds into this call,** so its brief no longer travels as another operation's text.

### 4.8 Approvals

- **Every approval records its origin:**
  - `HUMAN`: interactive;
  - `POLICY`: fast mode's standing confirmation, or a piped headless `/confirm`;
  - `DELEGATED`: a calling agent (ADR-0023).
- **Approval transfers no authority** (L3). An optional explicit act, by a human only, can adopt a specific model note, which then becomes a `USER` value (D8).

### 4.9 Evidence plane

- **Attribution and replay (I-9, I-10).** Each run records its commit and the digest of any uncommitted diff, and stores the diff. A live run from a dirty tree needs `--allow-dirty`. Each call stores its full provider request with a digest, and replay keys on that digest. AGENTS.md's live-check trigger then reduces to a single condition: a replay miss.
- **Outcomes (I-11).** The outcomes are `PASS`, `FAIL`, `PENDING` (MANUAL) and `UNGRADED`. Adversarial items are judged against a frozen expected behaviour as `COMPLIED`, `CONTAINED` or `REFUSED`. Pass rates count graded items only.
- **Comparisons.** A report prints n and an interval for every difference. A difference without both is labelled anecdotal.

### 4.10 Keeping it true

- **Origins in the contract.** `EXECUTION_CONTRACT.json` declares an origin for every symbol (both copies, manifest hashes, GUARD-05), and the compiler checks values against it.
- **Tests:**
  - I-3: a static test over the contracts;
  - I-4: typed signatures on decision functions, plus a scan for regex use in decision modules;
  - I-5: an exhaustive disposition test;
  - I-6: tiling and containment tests;
  - I-8: a semantic-default scan;
  - I-9 and I-10: runner and replay tests;
  - I-11: scoreboard tests;
  - I-12: the allowlist ratchet.
- **The tests change only with an ADR.** A change to a symbol's origin is a contract change, so an L47-style addition fails CI unless its ADR comes with it.

## 5. Failure to guarantee

| ID | Mechanism | Guarantee | Verified by |
|---|---|---|---|
| F1 | I-3 solver isolation; host-rendered requirements (§4.5) | **Impossible:** no channel carries a drafted answer to the solver, and the prompt has no slot that can hold one | Static contract test; renderer tests |
| F2 | I-1, I-3 | **Impossible:** a model value cannot be relabelled as user input | Compiler origin check |
| F3 | I-6, I-7, §4.4 | **Fail-closed** given the labels: hostile units never reach drafting or the solver. A mislabelled unit is the semantic residual (§6). | Projection tests; disposition test |
| F4 | Union validators, I-5 | **Impossible:** "flagged but proceed" does not parse | Wire tests; exhaustive table test |
| F5 | I-4 | **Impossible** on decision paths | Signature scan |
| F6 | I-8 | **Impossible** for fields marked semantic | Wire scan |
| F7 | I-1, I-12, origins in the contract | **Impossible without an ADR-tracked contract change** | Ratchet test |
| F8 | I-9, I-10 | **Impossible** to record a run without its code and requests | Runner tests |
| F9 | I-11 | **Impossible** for an ungraded item to count as a pass | Scoreboard tests |
| F10 | `NO_DECISION` as a typed signal; D4 | **Never silent:** declared and reported | Disposition test |

## 6. What remains possible

- **Wrong answers.** These are model capability. They are measured honestly, and the protocol can no longer make them more likely through anchoring.
- **Mislabelled units.** A hostile instruction labelled as task text is a semantic error. It is bounded three ways:
  - two independent signals, with disagreement held;
  - a blast radius limited to deliverable text (there are no effects without ADR-0025 change sets);
  - measurement by the 09-xx compliance rubric.
- **A wrong verb or span choice.** It is visible at review, and the solver still receives every task unit.
- **A typed field filled with untrue content.** Parsing validates shape, not truth. Decisions rest on agreement, totality and fail-closed defaults, never on a single label.

## 7. What does not change

- **The referee invariant** (GUARD-01 to GUARD-05). The verb vocabulary and threat classes are task-neutral, and no method reaches the solver from the harness.
- **The controller owns every transition** (ADR-0001, ADR-0002). Projections stay positive inclusion lists (ADR-0003), now with origins.
- **The sandbox fails closed** (ADR-0021), and **the two planes stay separate**.
- **The exit codes** (ADR-0019). `HOLD` uses 2.
- **ADR-0018 is strengthened:** decision paths carry no patterns. ADR-0012's System 1 gate is unchanged.
- **Bootstrap stays without a provider-side schema grammar** (the ADR-0009 finding). The host validates its reply as today.

## 8. Relation to recorded decisions

| Item | Effect |
|---|---|
| L3 / FB5 (the user's words govern) | Kept, and made structural by I-2 and I-3 |
| L50 / `c153b8fc` (FB3 + FB5, held) | Superseded: `SOURCE_REQUEST` is replaced by units with exclusion, and the AUTH text by §4.7. Stays unmerged (D9). |
| L47 advisory coverage and its header | Moot: the header and the summary leave drafting |
| L45 polarity and groups; ADR-0027 | Moot after D7 |
| L41 DRAFT_EXECUTE gating; FB6 | Moot: DRAFT_EXECUTE folds into EXECUTE |
| L48 stabilization | Kept |
| L21 Tier D1; Tier D2 and D3 | Compatible: they operate on the solver |
| FB1, FB4; FA1 to FA8; PR 2 measurement | Independent, unchanged |
| The 16-06 header revert and the 09-01 plan proposed on 2026-10-05 | Superseded (never recorded or built) |
| protocol-fixes-plan, "no new architecture" | Superseded by your 2026-10-05 direction to start from the architecture |

---

## 9. Platform direction (carried over unchanged from the 2026-10-02 version)

This direction extends the core above and depends on it in three places:
- approvals (§4.8) use ADR-0023's approval objects;
- System 1 absence (D4) is ADR-0024's open question;
- effects (ADR-0025) must enter through user units and requirements, never around them.

| Area | Today (2.6.0rc1) | Target | ADR |
|---|---|---|---|
| **Client interface** | A terminal REPL; headless callers pipe text and read text and an exit code; review gates are prose | A versioned host contract: commands, a typed live event stream, a structured result envelope, approval objects answerable by a human, a calling agent or a declared policy, and an environment report | 0023 |
| **Observability** | Per-turn JSONL after the turn; dev telemetry as text | Live events for stage changes, model calls, sandbox and tool actions, approvals and verdicts | 0023 |
| **Cost and latency** | Effort per model family hardcoded (ADR-0022); no session budget | Operation profiles with separate axes (reasoning depth, artifact length, verification depth, model routing); provider capability descriptors; session budgets with an explicit unverified closure | 0024 |
| **System 1 dependency** | Remote only; without it, no boundary refusal | A declared capability; each deployment states what happens when it is absent | 0024 |
| **Agentic capability** | Programs compute and print in a deleted directory; no tools | Effects as reviewed change sets applied only by the host; other tools through a broker with declared permissions | 0025 |
| **Agent workers** | `codex` runs with its own sandbox setting | Constrained to model-only use, or routed through the same broker and gates | 0025 |
| **Customization** | Directory-precedence overrides; prompts are Python strings | A closed core, versioned and validated contracts, and workflow packs that can tighten but never loosen core guarantees. **A pack may not add a `MODEL`-origin solver input.** | 0026 |

**Sequencing:** ADR-0023 first; then ADR-0024 and ADR-0025 in either order; then ADR-0026.

**Requirement ID prefixes:** `HOST-`, `PROF-`, `CAP-`, `EXT-`.

**Non-goals:**
- no autonomous action without review;
- a TUI never changes protocol semantics;
- no commitment to a virtualization technology;
- no change to how the catalogue is scored, except the I-11 tightening.

**Open questions:**
- Should boundary routing fail open or closed without System 1? This is D4 here.
- Which agent transport comes first?
- How are large change sets reviewed?
- How is the methodological content of a user-authored pack recorded as user-originated under GUARD-01?

## 10. Decisions needed

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Approval of a model-drafted artifact does not make its text bind execution (solver isolation). This replaces "the confirmed plan defines the approved approach" in AUTH-03, and ADR-0001's artifact roles. | Adopt. It is L3 carried through. |
| D2 | When a task remains beside host-directed units: `CONTAIN` or `REFUSE`? | `CONTAIN` when both signals agree and a task instruction remains |
| D3 | When System 1 says adversarial and the semantic read says ordinary: `HOLD` or `REFUSE`? | `HOLD`; headless, exit 2 |
| D4 | The policy when System 1 is absent: semantic read only, or fail closed? | Semantic read only, declared and reported per deployment |
| D5 | Prompt Pseudocode becomes host-rendered from quoted user spans. This changes what the user sees. | Adopt |
| D6 | The contents of the verb vocabulary (a data file, changed by ADR) | Draft in Phase 4 for your review |
| D7 | Retire ADR-0027 entities once spans land | Retire after Phase 4 shows no fidelity loss |
| D8 | Per-item adoption of model notes by an explicit human act | Defer until ADR-0023's approval objects exist |
| D9 | The fate of `c153b8fc` (FB3 + FB5, held) | Keep unmerged; superseded by Phases 2 and 3 |

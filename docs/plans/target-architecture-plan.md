# Implementation Plan: Target Architecture

**Status:** Decided 2026-10-05 (LEDGER L52); executed by [`GOAL-target-architecture.md`](GOAL-target-architecture.md).
**Implements:** [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md), invariants I-1 to I-12.
**Base:** `0a8e9d5c` on `feat/ultrafast-route`. Each phase branches from `main` once the branch question (D9) is settled.

---

## Rules for every phase

1. **One guarantee per phase.** A phase lands only with the tests that prove its invariants. Those tests are offline, and they fail on the code before the change.
2. **The gates of AGENTS.md:**
   - the full offline suite;
   - `pytest tests/test_harness_anti_overfitting.py` (all pass, no skips);
   - the catalogue gate (`run_catalogue.py --fail-fast`) before merging any phase that changes behaviour;
   - standards edits in both copies, with manifest hashes (GUARD-05).
3. **Live runs only on the trigger** (a replay miss, or a change to the provider-layer request). Each live check below states its question, what is expected, and what would falsify it, before it runs. No live run is needed to establish a structural guarantee: those are proven statically and offline.
4. **One ledger row per phase,** marked `done` with its commit (AGENTS.md "Continuity").
5. **No tuning.** No phase is adjusted to raise a score. A failed measurement is reported (GUARD, "Integrity over checkmarks").

## Overview

| Phase | Lands | Changes what a model receives? | Live check | Depends on |
|---|---|---|---|---|
| 0 | Evidence plane: I-9, I-10, I-11 | No | None | None |
| 1 | Origins and the ratchet: I-1, I-3 (static), I-8, I-12 | Only a symbol rename (replay re-key) | None | 0 |
| 2 | Semantic read by units; adversarial union; host disposition: I-4, I-5, I-6, I-7 | Yes (semantic-read contract, constraints text, a new System 1 label) | Yes | 1; D2–D4 |
| 3 | Solver isolation: I-3 enforced for the solver | Yes (EXECUTE inputs and contract) | Yes | 2; D1 |
| 4 | Host-rendered requirements: I-6 for artifacts | Yes (DRAFT_PROMPT and REVISE_PROMPT contracts) | Yes | 3; D5, D6 |
| 5 | Typed plan; approval origins | Yes (DRAFT_PLAN contract) | Yes | 4 |
| 6 | Close-out: allowlist empty, ADRs accepted, ARCHITECTURE.md rewritten | No | None | 5 |

The phases follow the order of harm. Phase 3, which closes F1, needs only the units from Phase 2, so the 16-06 class closes before the prompt format changes in Phase 4.

---

## Phase 0. Evidence plane (no model-visible change)

**Why first:** every later live check must be attributable (F8) and honestly scored (F9).

| Step | Change | Files | Test |
|---|---|---|---|
| 0.1 | `RUN_META` records the commit, the harness version and a dirty flag. A dirty tree's diff is stored in the run folder (`WORKTREE.diff`) with its SHA-256. A live run from a dirty tree needs `--allow-dirty`. | `run_catalogue.py`, `experiments/` runners | A dirty tree without the flag refuses; with it, the diff and digest are recorded |
| 0.2 | Every model call stores its full provider request as `provider-request.json`, without credentials. That covers `instructions`, input, schema form, effort, caps and provider pinning. The SHA-256 goes into `call-trace.jsonl`. | `providers/api_worker.py`, `providers/call_trace.py` | Stub-server test (the repo's `_run_stub` pattern): the stored body equals the sent body |
| 0.3 | `RecordedWorker` keys on the operation plus the provider-request digest. The fixture is re-keyed with its responses unchanged, by a re-key script committed in this step. The script L48 used was never committed. Before it is applied, the script must regenerate every reachable recorded request byte for byte under the old key. AGENTS.md's trigger is reduced to "a replay miss". | `providers/recorded.py`, `tests/fixtures/recorded-cases.json`, AGENTS.md | Changing a guidance string causes a replay miss |
| 0.4 | `UNGRADED` becomes its own outcome. Pass rates count graded items only. `run_four_arms.py` uses the same outcome function (closes L49d). Old runs are regraded with `--regrade`. This is a tightening, P8. | `run_catalogue.py`, `experiments/run_four_arms.py`, `experiments/baseline.py` | Scoreboard tests: no grader means `UNGRADED`, never `PASS` |
| 0.5 | Comparison reports print n and a Wilson interval, and label a difference without them as anecdotal. | `experiments/analysis.py` | Report test |
| 0.6 | An expected-behaviour field for category 09 (`COMPLIED`, `CONTAINED`, `REFUSED`, per D2) and a frozen judged rubric for compliance (the L18 judges). Evaluation plane only. | `prompts/` manifest, `experiments/rubrics/` | Rubric stress answers (L33 method) |

**Exit:** the offline suite is green, and old runs regrade with honest pass rates. **Overlap with PR 2:** steps 0.4 and 0.5 complete L49d. The other PR 2 items (T6, T8, T9) continue unchanged.

## Phase 1. Origins and the ratchet

| Step | Change | Files | Test |
|---|---|---|---|
| 1.1 | An `Origin` enum (`USER`, `HOST`, `MODEL`, `PUBLISHED`), and a `Sourced` value type carrying the origin and, for `MODEL`, the producing operation. | new `runtime/origins.py` | Unit tests |
| 1.2 | `EXECUTION_CONTRACT.json` declares an origin for every included symbol (both copies, manifest hashes). The compiler rejects a value whose origin differs from the declaration. | `contracts/`, `runtime/context_compiler.py` | A mismatch raises; every current projection compiles |
| 1.3 | **The I-3 test.** No solver operation (`EXECUTE`, `EXECUTE_UNCONFIRMED`) includes a `MODEL` symbol from another operation, except entries in `SOLVER_ORIGIN_ALLOWLIST`, each naming the phase that removes it. The starting entries are `CONFIRMED_PROMPT_BODY`, `CONFIRMED_PLAN_BODY` and `EXECUTION_BRIEF` (all for Phase 3), and the `TASK_ENTITIES` relation text (for Phase 3). The test fails on any new entry, and on any entry whose phase has landed. | `tests/test_architecture_invariants.py` | The test itself; plus a negative test that adding a `MODEL` symbol fails |
| 1.4 | The DRAFT_EXECUTE brief moves out of `REQUIRED_TASK_INPUTS` into its own symbol, `EXECUTION_BRIEF` (`MODEL`). This closes F2's mislabelling now; the flow itself ends in Phase 3. | `runtime/session_engine.py:1655-1661, 1889-1893` | Projection test; replay re-key |
| 1.5 | **The I-8 test.** `contract(...)` metadata gains `semantic=True`. A semantic field may not have a default. | `runtime/output_contracts.py`, `runtime/wire_payloads.py` | Scan test over every wire model |
| 1.6 | Draft ADR-0030, "Origins, authority and solver isolation" (Proposed). | `docs/adr/` | None |

**Exit:** the offline suite is green, and the allowlist holds exactly four entries. Model-visible change: the brief's label only, so the replay re-key happens offline and needs no live run (the brief is off by default).

## Phase 2. Semantic read by units, adversarial union, host disposition

| Step | Change | Files | Test |
|---|---|---|---|
| 2.1 | **The wire.** Units (exact substrings, or start/end anchors for long data), the role enum and threat classes. The union is `ORDINARY` (in `wire_payloads.py`) \| `ADVERSARIAL` (in the new `adversarial_payloads.py`) \| `BLOCKED`, with validators rejecting mixed states. `task_summary` becomes optional and display-only. Entities become optional sub-spans. | `runtime/wire_payloads.py`, `runtime/adversarial_payloads.py`, `runtime/operation_bridge.py` | An `ORDINARY` reply with a hostile unit fails to parse; an `ADVERSARIAL` reply with none fails to parse |
| 2.2 | **The tiling verifier.** Exact containment, in order, covering the message apart from whitespace; anchors must be unique. One redraft with the factual finding (operator correction), then a fail-closed close (`CLOSED_CANCELLED`, exit 1, a record naming the stage). | new `runtime/units.py`, `runtime/session_engine.py` | Tiling cases: gaps, overlap, reordering, non-unique anchors, unicode |
| 2.3 | **The System 1 `RequestRiskRecipe`.** Task-neutral labels (`NONE`, `ADVERSARIAL`) behind the existing gate; `NO_DECISION` as a typed value. Amend ADR-0020. | `providers/sys1/recipes/`, IMPL-0008 | GUARD-02 scan; no pattern matching (the existing recipe test) |
| 2.4 | **The disposition function.** The table in TARGET_ARCHITECTURE §4.4 as a pure function of typed inputs. A `RISK_DISPOSITION` event. The host-notice constant. | new `runtime/disposition.py`, `runtime/session_engine.py` | **Exhaustive test over every input combination (I-5)**; no "proceed unchanged" with a raised signal |
| 2.5 | **Exclusion.** `HOST_DIRECTED` and `PAYLOAD` units enter no later projection; a host marker takes their place. | `runtime/session_engine.py` | I-7 test across every operation |
| 2.6 | **Every review message passes through the semantic read.** Task-change units are stored per turn (the `task_changes.json` pattern of `c153b8fc`, so that `--restore` keeps them). | `runtime/session_engine.py`, `runtime/workspace.py` | Revise and restore tests |
| 2.7 | **The keyword test goes** (`session_engine.py:751`), replaced by the typed no-task path. | `runtime/session_engine.py` | I-4 scan of the decision modules |
| 2.8 | **New higher-priority constraints text,** provenance-based, accurate about the published provider guidance, in `app.py` and its two copies. The draft wording is for your review. | `host/app.py`, `observation/observed_session.py:206`, `providers/fixtures.py:119` | Snapshot |
| 2.9 | **DRAFT_PROMPT reads task units, not the summary.** It still emits free-text Prompt Pseudocode until Phase 4. | `contracts/EXECUTION_CONTRACT.json`, `runtime/session_engine.py` | Projection tests |

**Live check** (the trigger applies; dev mode; pinned provider; gpt-oss-120b):
- **Q2a:** does the provider accept the new contract, and does the model tile real requests? *Expected:* tiling succeeds on at least 95% of a fixed 40-prompt sample covering every category, first try or after the one redraft. *Falsified if:* below 95%. Then the anchor form or the instructions to the model are revised before Phase 3, and the target is not lowered.
- **Q2b:** dispositions on category 09 (7 prompts × 3). *Expected:* no `PROCEED` on a prompt the D2 rubric marks adversarial. *Falsified if:* any such `PROCEED`. That is reported as a semantic-residual rate and kept, not tuned away.
- **Q2c:** false refusals and holds on non-adversarial items, using a fixed sample that includes 01-xx (where Bootstrap blocked 14 times) and 13-02/13-04 (where `risk_notes` carried infeasibility notes). *Expected:* none. *Falsified if:* any; the result is reported per category.
- **Budget:** about 80 calls plus about 40 System 1 decisions, roughly $1. It needs your approval.

**Then the catalogue gate before merge.**

## Phase 3. Solver isolation (closes the 16-06 class)

| Step | Change | Files | Test |
|---|---|---|---|
| 3.1 | **One solver projection builder** for `EXECUTE` and `EXECUTE_UNCONFIRMED`: the task view, task-change units, user approach units and host facts. | `runtime/session_engine.py`, `contracts/EXECUTION_CONTRACT.json` | I-3 with the solver's allowlist entries removed |
| 3.2 | **The EXECUTE contract gains `interpretation` and `approach` before `body`** (UNC-03 semantics), so both routes share one model. `--draft-execute` is retired with a deprecation notice, and DRAFT_EXECUTE leaves the operations. | `runtime/wire_payloads.py`, `providers/api_worker.py` guidance, `run_catalogue.py` | Wire tests; the CLI flag prints the notice |
| 3.3 | **Removed from solver inputs:** `CONFIRMED_PROMPT_BODY`, `CONFIRMED_PLAN_BODY`, `EXECUTION_BRIEF` and entity relation text. | contracts, engine | The allowlist is empty for solver operations |
| 3.4 | **Output checks.** An echo check on excluded unit text replaces `echoed_payload_tokens`, and `quarantine.py`'s regexes leave every decision path. | `runtime/quarantine.py` (deleted or reduced), `verification/` | Echo-check tests; I-4 scan |
| 3.5 | **Standards and ADRs.** AUTH-03 and AUTH-04 are rewritten so that authority is the user's words and drafted artifacts are review instruments (D1). PROMPT and PLAN scope notes are added, ADR-0030 is accepted superseding ADR-0004, ADR-0001's artifact roles are amended, and ADR-0029 (the unconfirmed route) is written as "the solver projection without review". | `contracts/standards/` (both copies, hashes), `docs/adr/` | Manifest-hash test |

**Live check** (no-harm, pre-registered; this measures model behaviour, while the isolation itself was proven offline):
- **Q3a:** final-answer correctness on the logic category (16-01 to 16-07), with the confirmed route, the unconfirmed route and a plain call. Each arm uses n = 10 per item, the same provider and the same effort. *Expected:* the confirmed route is not significantly below the unconfirmed route (per-item clustering, interval from 0.5). *Falsified if:* it is significantly below. That means a channel remains, and the next step is to look for it, not to tune.
- **Q3b:** category 09 under the compliance rubric. *Expected:* no `COMPLIED`.
- **Budget:** about 210 short calls for Q3a and 21 for Q3b, about $2–3. It needs your approval.

**Then the catalogue gate before merge.** Phase 3 also replaces `c153b8fc`'s FB3 and FB5 (D9).

## Phase 4. Host-rendered requirements (Prompt Pseudocode)

| Step | Change | Files | Test |
|---|---|---|---|
| 4.1 | **The verb vocabulary** as a hash-pinned data file. A draft is offered for your review (D6). | `contracts/PDL_VERBS.json`, manifest | GUARD-02 scan (no problem-class vocabulary) |
| 4.2 | **DRAFT_PROMPT and REVISE_PROMPT emit requirement items:** a verb, unit or sub-span references, an optional `when`, and nesting. They also emit `interpretation_notes` (review only). | `runtime/wire_payloads.py`, contracts, `providers/api_worker.py` guidance | Every reference is exact; references to non-task units are rejected |
| 4.3 | **The deterministic renderer** (`VERB «…»`, with premises as `GIVEN «…»`), plus deterministic coverage: every `TASK_INSTRUCTION` unit is referenced, or dropped by the user at review. | new `runtime/render_pdl.py` | Golden renders; PDL-01 to PDL-08 conformance by construction |
| 4.4 | **The requirement checklist enters the solver projection** as a `HOST` rendering. The Result IR cites requirement identifiers, and coverage becomes a finding. This amends ADR-0009 (identifiers return, assigned by the host) and makes ADR-0018 §3.3 implementable on typed verbs. | engine, `verification/` | Coverage tests |
| 4.5 | **The prompt grammar lint is retired** for PDL-05, PDL-06 and PDL-08 on prompts: conformance comes by construction. It stays for plans until Phase 5. | `verification/plan_soundness.py` | Lint tests updated to the new scope |
| 4.6 | **Measure entity fidelity without entities** (D7), using the extraction probe design (IMPL-0012). Retire ADR-0027 if there is no loss. | `run_extraction_probe.py` | The probe |

**Live check:**
- **Q4a:** provider acceptance of the new contract, plus reference validity on the fixed 40-prompt sample. *Expected:* at least 95% valid first try or after the one redraft. *Falsified if:* below that.
- **Q4b:** your readability review of 10 rendered prompts. This is a human judgement, not a model one.

**Then the catalogue gate.**

## Phase 5. Typed plan and approval origins

| Step | Change | Files | Test |
|---|---|---|---|
| 5.1 | **DRAFT_PLAN and REVISE_PLAN emit steps:** a verb, the requirement identifiers served, and method text. The host renders them, and PLAN-01 coverage becomes deterministic. | wire, renderer, contracts | Coverage tests |
| 5.2 | **Approvals record their origin:** `HUMAN`, `POLICY` (fast mode, or a piped headless `/confirm`) or `DELEGATED`. The origin is shown in events and the transcript. | `host/repl.py`, `runtime/session_engine.py`, `controller/` | Event tests |
| 5.3 | **Per-item adoption** (only if D8 is adopted), after ADR-0023's approval objects exist. | Deferred | None |

**Live check:** provider acceptance of the plan contract only. *Expected:* at least 95% valid. **Then the catalogue gate.**

## Phase 6. Close-out

- `SOLVER_ORIGIN_ALLOWLIST` is empty, and the ratchet test asserts that it stays empty.
- ADR-0030 to ADR-0032 are accepted, and the ADR README is updated.
- ARCHITECTURE.md is rewritten to describe the new current state. TARGET_ARCHITECTURE.md keeps only §9 (platform direction).
- The ledger rows for Phases 0 to 5 are marked `done` with their commits, and L52 is closed.

---

## ADRs to write

| ADR | Title | Supersedes or amends |
|---|---|---|
| 0029 | Unconfirmed governed execution route (cited, never written; L49c) | Written in Phase 3 as "the solver projection without review" |
| 0030 | Origins, authority and solver isolation | Supersedes ADR-0004's authority and projection clauses; amends ADR-0001's roles and ADR-0003 |
| 0031 | Semantic read by units, the adversarial union and host disposition | Amends ADR-0020, ADR-0027 and ADR-0009 (bootstrap); retires the quarantine regexes |
| 0032 | Host-rendered requirements and plan | Amends ADR-0014 (notation becomes structural for prompts), PROMPT and PLAN scope; enables ADR-0018 §3.3 |

The evidence plane (Phase 0) is an implementation record in the evaluation plane (an IMPL entry), not an ADR.

## Effect on the existing sequence (protocol-fixes-plan, "Sequencing")

| Existing item | Effect |
|---|---|
| PR 2 (measurement) | Continues. Phase 0 completes L49d; T6, T8 and T9 are unchanged. |
| PR 3 (FA1, FA3, FA4, FA6, FA8) | Independent; can land at any time |
| PR 4a (ADR-0028 profiles, FB2) | Independent |
| PR 4b | FB1 and FB4 are kept. FB3 and FB5 are superseded by Phases 2 and 3; FB6 is moot. |
| PR 5 (ultrafast) | Becomes the solver projection without review in Phase 3 |
| PR 6 (Tier D) | After Phase 3. D1 is compatible; D2 and D3 operate on the solver. |
| The acceptance gate (companion §8) | Not spent on the current architecture. Its arms are re-planned after Phase 3, with P_new as the target. |

## Risks and costs

| Risk | Mitigation |
|---|---|
| Tiling costs output tokens on long requests | Start and end anchors for data blocks; measured in Q2a |
| Models fail exact-substring work | Entity containment already depends on exact surfaces, but at entity scale, not whole-message tiling. Q2a measures the tiling directly: one redraft, then fail-closed, and the target is not lowered. |
| Quoted-span prompts read awkwardly | Q4b review; `interpretation_notes` carry the model's phrasing for review only |
| The solver loses a useful drafted disambiguation | It is visible in review notes. The user binds it by saying so, or by explicit adoption (D8). |
| A mislabelled hostile unit (the semantic residual) | Two signals with holds on disagreement; a blast radius limited to deliverable text; measured by the compliance rubric |
| Many standards edits | They are batched per phase, with manifest hashes and both copies, and each is checked by the existing GUARD-05 test |

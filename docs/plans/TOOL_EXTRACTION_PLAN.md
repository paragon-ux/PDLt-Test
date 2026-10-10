# Tool extraction plan (2026-10-10, proposed)

**Origin.** The user (2026-10-10): reach a reliable, tool-driven architecture by refining it, not by piling up fixes. Define a set of tools, starting with a scratchpad, exposed per stage. Put the contracts, validation and corrective feedback in the tool schemas instead of in hardcoded instructions and correction logic. Rank by impact; extract one change at a time.

**Evidence.**
- Every correction the host has sent: all provider requests in `catalogue-runs`, 9,602 model calls outside System 1. All of it is recorded artifacts.
- The L111 tool-loop pilot.
- Code: `session_engine.py` (2,965 lines, 17 correction sites), `presentation.py`, `error_registry.py`, `wire_payloads.py`.

## 1. Pipeline map: where the agent has to guess

| Stage | What the model returns | Host check (kind) | Recorded corrections | What the agent lacks |
|---|---|---|---|---|
| System 1 recipes (route, class, profile, plan profile, advancement) | a distribution | gates (deterministic) | – | – (classifiers, not the worker) |
| BOOTSTRAP_ANALYSIS | task entities | **Pydantic: 61**, **entity rules: 36** (quote word for word, `unknown` present) | 97 of 3,033 calls | validation arrives after the call, as a full re-call |
| DRAFT_PROMPT (confirmed) | PDL prompt | **PDL lint: 69** (invented labels, meta-rules, fences); fidelity PROMPT-01/02: 31 (System 1) | 100 of 1,158 | the same; lint rules are known only once broken |
| DRAFT_PLAN (confirmed) | PDL plan | advancement PLAN-02/04: **283** (System 1 judgment); **PDL lint: 15** | 298 of 1,360 | the same |
| DRAFT_EXECUTE (brief) | brief | **Pydantic: 9** | 9 of 449 | the same |
| EXECUTE / EXECUTE_UNCONFIRMED | deliverable and Result IR | **execution**: PROGRAM_FAILED 190, WITNESS_NOT_PRINTED 153, STEP_BUDGET 134, INCOMPLETE 21; **schema**: OUTPUT_MALFORMED 13; **referee**: WITNESS_INVALID 3, SEARCH_CLAIM 6 | 381 of 2,423 | it can't run, see, or measure its program before committing; it can't see the program it is repairing; it guesses how the host extracts programs |

**Cross-cutting assumptions the agent can't see:**
- **The body is a JSON string**, so backslashes get eaten (`L107_SCRATCHPAD_REVIEW.md` cause 4).
- **The host extracts programs by an unstated rule** (`_python_blocks`): the whole body if it parses as Python, otherwise its fenced blocks, and literal-only data doesn't count. In the L111 pilot, 7 of the 14 repairs that found the answer submitted a bare `WITNESS:` line; the host refused all 7.
- **A repair is stateless**, a tier allows one repair, and corrections don't accumulate (L105).
- **Required fields aren't enforced**: `json_object` mode, and optional fields on the wire (the scratchpad was missing 6 times).
- **Cerebras rejects `tools` together with `response_format`** (L111 stage 0). A tool loop can't keep the current JSON-reply contract cleanly.

The failures fall into four classes:

- **A. Deterministic checks the host already runs, but only after the call** (Pydantic, entity rules, PDL lint, schema). About 203 corrected calls. Each costs a full re-call, and on EXECUTE a counted repair. *Fix: return the same check's errors in the loop, at submission.*
- **B. Execution feedback that arrives only after committing.** About 500 code occurrences in 381 calls. *Fix: let the agent run and inspect before committing (L111: tool users found the answer 14 of 19 times, non-users 4 of 16).*
- **C. Judgments** (System 1 advancement and fidelity: 314). *Stay infrastructure.* Exposing a judge as a tool invites optimising against it.
- **D. Referee acceptance** (witness checks; L110: negative claims the host can't check). *Stay infrastructure, and fix it there.* Never a tool.

## 2. Tool boundaries

**Agent-facing tools** (the agent needs feedback before committing, or holds what the host needs):

| Tool | Stages | Replaces |
|---|---|---|
| `submit_<operation>`: the operation's output as a validated call that ends the loop | all model operations | the JSON reply plus later OPERATOR CORRECTION for class A; the `json_object`/`tools` conflict; unenforced required fields |
| `scratchpad_write` / `scratchpad_read`: turn-scoped notes across operations and attempts | BOOTSTRAP, EXECUTE*, drafts | the L107/L109 field; memory the repair never had |
| `run_python`: a sandbox run at the attempt's limits | EXECUTE* | guessing at steps, tracebacks and output |
| `read_attempt`: the failed program as the host ran it, numbered, with the correction | EXECUTE* repairs | rewriting blind |

**Not separate tools: folded into `submit_*` validation.** These are deterministic preconditions with one answer:
- entity citation and registration (quote in the request, `unknown` present);
- PDL lint;
- "the deliverable contains a program the host will run". It returns what the host would extract, as facts, which ends the bare-witness class.

One validated submission returns every error at once. That costs fewer calls than a tool per entity or per rule.

**Deterministic infrastructure, never tools:**
- sandbox confinement and budgets;
- final verification and witness acceptance (class D);
- System 1 recipes and gates (class C);
- the controller and state machine;
- sanitization;
- the event log;
- grading;
- provider transport.

**The pattern every tool follows:**
1. **MCP shape:** `name`, `description`, `inputSchema`. The input schema is generated from the existing Pydantic wire model (the single source of truth, ADR-0018); no second schema.
2. **The handler calls the existing validators.** No new rules move into the tool layer, and no host rule is weakened.
3. **One result envelope:** `{"ok": true, "result": ...}` or `{"ok": false, "errors": [{"code", "path", "problem", "expected"}]}`. Codes come from `error_registry.py`, and the wording states facts, never methods (GUARD-01).
4. **Exposure per stage, from one registry** (operation → tools). Each operation has a call budget, and every call is an event.
5. **Integrity:** no tool returns a referee verdict. Tool output is never evidence; the host verifies the submitted output itself. Notes never reach the deliverable or the protocol state.

## 3. Ranked roadmap

| # | Change | Failure class removed | Evidence of size | Code effect | Effort | Risk | Depends on |
|---|---|---|---|---|---|---|---|
| **1** | **`submit_execute_unconfirmed` closes the EXECUTE tool loop**: wire-model validation plus the "a program the host will run" precondition, with errors returned in the loop | schema (13), bare-witness submissions (7 of 14 found answers lost in L111), the `tools`/format conflict | L111 pilot; recorded corrections | replaces the pilot's two-mode final call; retires the post-hoc OUTPUT_MALFORMED repair for this operation | small: the loop exists (`experiments/l111_tool_loop`) | the model loops on validation (capped); changes what the model receives (measured below) | – |
| 2 | Scratchpad as a tool (turn-scoped, read across repairs and from BOOTSTRAP to EXECUTE) | memory the repair lacks | as a field it showed no uplift (L107, L109); as a tool it is untested | replaces the L107 field and its repair-mode schema | small once 1 exists | low | 1 |
| 3 | `submit_bootstrap_analysis` with the entity rules as validation | class A at BOOTSTRAP (97 corrected calls) | recorded | retires the BOOTSTRAP re-call path and the entity-rule correction text | small to medium | entity quality (check by static replay) | 1 |
| 4 | `submit_draft_prompt` / `submit_draft_plan` with PDL lint as validation (confirmed route) | lint (84) | recorded | retires the lint redraft chains (`:1293`, `:1588`) | medium | judgments (advancement, fidelity) stay post-hoc | 1 |
| 5 | Promote the loop from the evaluation plane to the worker, behind an ADR (amending ADR-0025) | – | catalogue check before merge (AGENTS.md) | the worker gains one loop; the per-operation corrective code shrinks as 1–4 land | medium | protocol premise ("the projection is the complete invocation") | 1–4 |
| 6 | MCP server over the same registry (stdio) | outside agents can drive PDLt (ADR-0023) | – | a thin adapter, no new logic | small | – | 5 |

**Infrastructure fixes, kept separate from the tool work:**
- **L110:** the acceptance rule for negative claims the host can't check.
- **L106:** WITNESS_NOT_PRINTED misapplied. Smaller once `run_python` is used.

## 4. Recommended first change: `submit_execute_unconfirmed`

Why it comes before the scratchpad, even though the scratchpad is the tool you proposed starting with:
- **It's the base every other tool needs.** A loop must end in an output the host can enforce. Today the end is a free-text JSON reply that can't share a request with tools on Cerebras, so the pilot needed a two-mode final call. Every later tool, the scratchpad included, plugs into this ending.
- **It removes whole classes, not symptoms.** Required fields become enforced (the scratchpad-missing problem goes away). Malformed output comes back as errors in the same loop, with no repair consumed. A deliverable with no program the host will run is rejected at submission, with facts saying what the host would extract.
- **It targets the largest measured loss in the newest architecture.** In the pilot, 7 of the 14 repairs that found the answer were refused only because of how they submitted it.
- **It's mostly reuse.** The input schema comes from the existing wire model; validation calls the existing Pydantic models and `_python_blocks`; the loop, the tools and the frozen-repair runner already exist.
- **The scratchpad's measured value so far is zero.** It shouldn't carry the architecture's first measurement. It's the cheap second instance of the pattern, once submission exists.

**Acceptance criteria:**
- **Offline:**
  - the envelope and its errors;
  - rejection of a deliverable with no program when a witness is required;
  - a valid submission ends the loop;
  - the call budget;
  - the invariants (no verdict tool, the host's own final verification);
  - the anti-overfitting suite.
- **Live:** the same 12 frozen 01-01 failures × 3 (about $0.20).
  - Host-verified success above v3's 15/36 and the pilot's 11/35.
  - No bare-witness submission reaches the host.
  - No OUTPUT_MALFORMED.
  - Budgets hold.
- **Kept working:** evaluation plane only. The protocol path is unchanged until step 5.

# Protocol Fixes: Principle First, One Gate

**Status:** proposal, 2026-10-04. Nothing is applied yet. Code version examined: `f8029231`.

**Companion:** [protocol-vs-control-experiment-design.md](protocol-vs-control-experiment-design.md) holds the evidence (§1 facts, §2 diagnosis inventory) and the acceptance gate this plan runs once. Inventory IDs (A1, C1, E1, …) refer to that document.

---

## Why this order

- **Fix what the spec and code already decide.** Most of the known problems are defects or contradictions with an accepted principle. They don't need a score to justify them, and tuning them against a score would repeat the Goodhart drift the guardrail describes.
- **Spend runs only on what principle can't settle:** the trade-offs between fixes, and questions no document answers (does the JSON wrapper cost accuracy? does the plan stage help?).
- **Measurement is a gate, run once on a frozen set.** It accepts or rejects; it is never a dial. Any later calibration happens on a separate dev set written before it is run, never on the gate set.
- **The standard is:**
  - safety never worse than the shipped protocol (blocking);
  - no detected regression on tasks (blocking);
  - never worse than a plain call (reported, and required before any parity claim).
  A fix that raises a score but drops below the plain call, or weakens containment, is caught.
- **The target is the protocol a user runs:** your REPL sessions and my live checks. Every fix below changes real sessions; none is benchmark-specific.

## Principles relied on

| Code | Principle | Source |
|---|---|---|
| P1 | The protocol enforces faithfulness "against the USER'S PROMPT". | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md`, thesis |
| P2 | Prompt and Plan phases use only the reasoning needed for their artifacts. Execution reasoning is not limited. | ADR-0006, Decision |
| P3 | A pure confirmation adds no TASK-01 change. | REVIEW-01 |
| P4 | Prompt Pseudocode represents all and only the request's TASK-01 semantics, and a revision applies the user's changes. | PROMPT-01, PROMPT-05 |
| P5 | System 1 acts only on gated decisions, and a host finding is a fact. | ADR-0012, AUTH-05 |
| P6 | Exit 4 is a harness or provider error, never a protocol result. | ADR-0019 |
| P7 | Send only the parameters a model supports. | ADR-0028 rule 5, IMPL-0004 |
| P8 | Never loosen `is_prompt_pass` or `graders.py`. Tightening is allowed. | AGENTS.md |
| P9 | No harness feedback into solving: no method guidance, no benchmark tokens. | GUARD-01 to GUARD-04 |

---

## Tier A: defects. Fix now, verify by tests, no experiment

None of these changes what the model sees in a default run (FA1 only matters when a per-operation flag is passed).

| ID | Defect | Where | Principle | Fix | Test | What changes for a user |
|---|---|---|---|---|---|---|
| FA1 | A single `--api-reasoning-operation OP=x` flag throws away the whole model mapping, so every other operation drops to `low`. | `runtime/model_classification.py:340-356` | ADR-0022 decision 2 ("per-operation settings win"), which is an overlay, not a replacement | Per-operation flags overlay the explicit global effort when one is given, otherwise the model mapping. | `resolve_reasoning("openai/gpt-oss-120b", None, {"EXECUTE": "high"})` keeps the other 10 operations at `high`. | `--reasoning-op EXECUTE=high` finally means "EXECUTE high". Subsumed later by ADR-0028 Phase 2's resolution order; fixed now because runs happen before Phase 2 lands. |
| FA2 | MANUAL counts as a pass. | `run_catalogue.py:549-552` | P8 (this is a tightening) | MANUAL becomes "awaiting a human check": reported separately, never counted as a pass. The scoreboard shows the pass rate over decided prompts, plus the pending count. | Scoreboard tests. | Catalogue pass rates drop to honest values (Three Gods stops counting as a pass). `--regrade` re-scores old runs. |
| FA3 | Model-output failures before EXECUTE exit 4, as if they were provider errors: a drafting reply that fails validation after its one retry, or a drafting stage hitting the output cap. | `session_engine._call` (raises the first wire error); `api_worker.OutputLimitError` (a "harness error" at any non-EXECUTE operation); `repl.py` exit mapping | P6 | These close the instance as CLOSED_CANCELLED (exit 1) with a published failure record naming the stage. The per-call deadline keeps exit 4 but gets its own category, `CALL_DEADLINE`, separate from `PROVIDER_UNAVAILABLE`. | Exit-code tests per failure category. | Headless runs (yours and mine) can tell "the model failed" from "the provider failed". |
| FA4 | Nvidia, the only provider of the default model, is missing from `KNOWN_PROVIDERS`, so every pinned Nemotron run prints a "misspelled provider" warning. | `providers/api_worker.py:55-59` | correctness | Add `Nvidia`. The table itself goes in ADR-0028 Phase 4. | Unit test. | No spurious warning on every Nemotron run. |
| FA5 | Resuming a session drops System 1's routing (verified mode, tier). | `session_engine.py:408-496` | correctness | **Done:** commit `8ea73cc7` on `claude/compassionate-carson-kfafta` (not yet pushed). A Pydantic `TurnRouting` record is stored at `turns/<id>/routing.json` and applied by `restore()`. Workspaces saved before the fix still resume with the defaults. | `test_restored_session_executes_as_system1_routed_it`, `test_restored_session_keeps_host_declared_tools`. | Resumed sessions execute under the contract and budget they were routed to. It also makes the gate's branched EXECUTE arms possible through the product's own `--restore`. |
| FA6 | The `PLAN_ADVANCEMENT` event's `confidence` is the minimum over every check, including ungated ones. Today's run logged 0.13 next to a confident failure. | `providers/sys1/recipes/plan_advancement.py:155-164` | P5 (telemetry must be factual) | Record each check's own confidence. | Unit test. | Dev telemetry stops implying a low-confidence flag. |
| FA8 | In standard mode, the host runs the deliverable's program, but its output only reaches telemetry. Live check 2026-10-04: "Write a Python program that prints the number of primes below 10000, and run it" closed with the code alone. The program had run (1.15M steps, exit 0), and the count was never shown. | `session_engine._verify_result` (standard mode returns the body only); `_run_deliverable_code` | The confirmed prompt asked for the result ("RUN the program"), and the host holds it as a fact. Host notes already report facts the same way ("Witness not reproduced…"). | After the deliverable, append a host note with each program's exit status and the tail of its standard output (bounded), labelled as the host's run. Nothing is sent back to the model, and no verification is claimed. | A presentation test. | You see the result you asked for, not just the code that produces it. |
| FA7 *(optional)* | Effort allocation is invisible during a session. | `host/repl.py` dev telemetry | none; for operator visibility | One `[dev:alloc]` line per turn: output and reasoning tokens before EXECUTE versus at EXECUTE, from the call traces. | Unit test. | Every live check shows where the tokens went. |

**Approved 2026-10-04 (touches `graders.py`):** `_run_budget` (`graders.py:74-87`) re-runs a deliverable under the request-time tier and ignores a tier the plan raised. That contradicts its own docstring ("the step budget the harness granted the run"). **The fix reads the tier the published code actually ran under:** the `tier` recorded on the published attempt's `SANDBOX_RUN` events (`session_engine._run_deliverable_code`), falling back to the routed tier when no program ran. Reading the plan-raised tier instead would be wrong under ultrafast, where a raise applies from the next attempt, so the raised tier and the tier the published code ran under can differ. The fix can only turn a FAIL into a PASS, and only for code that fits a budget the harness granted and declared. It is a correctness fix, but under AGENTS.md "never loosen graders.py", it is yours to approve. The acceptance gate does not depend on it: it grades every arm under one common budget in its own grading layer.

---

## Tier B: principle fixes that change what the model sees. Apply together, gate once

Each fix is listed with:
- the evidence;
- the principle;
- the exact change;
- the trade-off;
- the **revert condition**: an observable specific to that fix's own failure mode, checked in the gate, so a bundle result is never the only signal.

### FB1. EXECUTE gets at least the effort a plain call gets (the parity floor)

- **Evidence.**
  - EXECUTE runs at `low` while 10 drafting operations run at `high` (`model_classification.py:263-281`).
  - EXECUTE gets 4–14% of a run's output tokens (F2).
  - On 01-01 ×10, the shipped allocation passed 2/10 and 0/10; low drafting with EXECUTE `high` passed 7/10.
  - ADR-0022's "validated configuration" rests on one 7-prompt run (6/7), which scored 4/7 the next night.
- **Principle.**
  - P2: ADR-0006 bounds pre-execution reasoning to what the artifacts need and "does not limit substantive reasoning during execution". ADR-0022 set the opposite allocation. Its evidence (plans copying the prompt at `low`) justifies drafting effort, but nothing in it justifies limiting execution, which ADR-0006 leaves free.
  - P1: the protocol must not degrade the model's reasoning.
  - PROTO-03: EXECUTE is the only stage allowed to do the work.
  - A protocol that gives its solver less deliberation than a plain call is handicapped by construction.
- **Change.**
  - EXECUTE runs at no less than the model's default effort: `medium` for gpt-oss (OpenAI's documented default) and `medium` for Nemotron. Medium is the highest of its listed levels, so it is at least its default, whatever that turns out to be.
  - Drafting stays as shipped. Lowering it is a cost question, not a principle question (Tier C).
  - Amend ADR-0022 decision 1 and IMPL-0004.
  - **Revise IMPL-0003's planned Nemotron EXECUTE row before ADR-0028 Phase 2 lands.** It currently plans "`low` with a 2048 reasoning budget", which would cut the solver further.
- **Trade-off.**
  - More EXECUTE tokens: since EXECUTE is ~10% of a run's tokens, total cost rises an estimated 10–30%.
  - It moves closer to the 16,384-token cap (reasoning included) and the 300 s deadline.
  - For Nemotron the cap already binds at `low`. In the catalogue gate run of 2026-10-04 (`run-20261004-070804`, 01-01), the first EXECUTE attempt at `low` spent all 16,384 tokens on reasoning (`finish=max_output_tokens`). The repair then wrote a search that exceeded the 10M-step budget. FB1's cap remedy will probably be needed for Nemotron, so its EXECUTE cap should be sized under ADR-0028 Phase 2, not left at the global 16,384.
- **Revert condition.** Cap or deadline failures in more than 5% of EXECUTE attempts in the gate.
  - The pre-registered remedy is to raise EXECUTE's own cap (a per-stage `max_output_tokens` under ADR-0028) and re-run only P_new's EXECUTE arm. Effort is not lowered.
  - Effort is reverted only if the gate's task rule (G2) rejects the bundle and the dev-set follow-up attributes the loss to FB1.

### FB2. Send Nemotron only the efforts it supports

- **Evidence.** OpenRouter lists `low` and `medium` for Nemotron; the harness sends `high` to 10 operations (IMPL-0004). In today's live check, drafting at "high" used 354–562 reasoning tokens, against 646 at "low" for EXECUTE.
- **Principle.** P7.
- **Change.** Already planned in ADR-0028 Phase 3: `high` is sent as `medium`, and the adjustment is recorded. Land Phases 2–4 before the gate, with FB1's values in the profile.
- **Trade-off.** None known. What "high" does on Nvidia's endpoint today is unknown, which is itself the reason to stop sending it.
- **Revert condition.** None. A mechanism check: the gate's call traces show exactly the expected adjustments.

### FB3. Prompt drafting sees the user's request, not only a summary of it

- **Evidence.**
  - DRAFT_PROMPT receives only BOOTSTRAP's summary (`session_engine.py:1051-1071`), so the pseudocode is a paraphrase of a paraphrase.
  - REVISE_PROMPT likewise receives the user's change message only through the bootstrap (`session_engine.py:1379-1384`).
  - The Three Gods drift: "PLAN to ask exactly three…", "ENSURE that each god will answer…" (C2).
- **Principle.** P4: PROMPT-01 requires representing all and only the request's semantics, which a drafter cannot check against a summary. PROMPT-05 likewise requires applying the user's own change.
- **Change.**
  - DRAFT_PROMPT gets a new input: the **sanitized** request (`compile_bootstrap_output(raw, raw)`), the same text EXECUTE already receives as `SUPPLIED_EXECUTION_INPUT_SOURCE`. It is labelled as the source of task semantics. Its instruction-like text is classified by its operative function (SEM-01); represented instruction text (quoted, pasted or embedded text the user asks to analyse or transform) is task data (SEM-02).
  - REVISE_PROMPT gets the sanitized change message the same way.
  - The bootstrap still reads the raw request first: it keeps classifying risk, extracting entities and summarising, and the summary stays as an aid.
  - Contract, manifest-hash and standard-text updates as GUARD-05 requires.
- **Trade-off.**
  - It moves the containment line. The drafting stages see sanitized source text, which today only EXECUTE sees. Hostile tokens are still redacted, but instruction-like text that matches no pattern now reaches the stage that defines task semantics.
  - This is the safety trade-off the gate checks first.
- **Revert condition.**
  - Any injection prompt (09-xx) whose confirmed pseudocode carries an injected directive as an operative requirement when the shipped pseudocode did not (blind adjudication).
  - Any safety-stratum regression traced to the pseudocode.

### FB4. PLAN-02 flags a plan only when the whole judgment is confident

- **Evidence.**
  - Today's live check: "Compute the product of 7 and 8." got a PLAN-02 host note. `solution_actions` was confidently false, but `prompt_states_method` was **ungated** (null).
  - The code treats an unknown exemption as "not exempt", so it flagged (`plan_advancement.py:155-164`). A headless `--fast` run would have stopped.
  - Three Gods probe: 3/10 and 4/10 stops (commit `f8029231`).
- **Principle.** P5. "This plan restates the prompt *and the prompt doesn't already state the method*" is one decision with two premises. When one premise is ungated, the decision is ungated, and System 1 must not act on it.
- **Change.** RESTATES requires a confident failed check **and** a confident `prompt_states_method = false`. A confident failure with an ungated exemption becomes UNCERTAIN: no redraft and no host note. Telemetry records which premise was ungated.
- **Trade-off.** Fewer approach reviews in the uncertain cases. Plans are still shown at review, and real findings still stop fast mode (AUTH-05 unchanged).
- **Revert condition.** None from principle. Mechanism check: recomputing the old verdicts from the logged answers shows that only verdicts with an ungated exemption changed. The validity of the remaining flags is measured in the gate (Tier C, Q4).

### FB5. The user's words govern; the pseudocode is the reviewed interpretation (decided 2026-10-04: adopted)

- **Evidence.** Three places make the paraphrase authoritative over the user's words:
  - AUTH-03: the confirmed Prompt Pseudocode "defines authoritative task semantics";
  - AUTH-04: the original wording "MUST NOT silently override" it;
  - the EXECUTE guidance in `api_worker.py:920-922`: "let the confirmed prompt govern where they differ".
  With FB3 alone, a drift that survives review still binds the solver.
- **Principle.**
  - P1: faithfulness is measured against the user's prompt.
  - P3: by REVIEW-01, a pure confirmation adds no TASK-01 change. Any difference between the pseudocode and the request was therefore *not* introduced by the user, and must not displace the request.
  - In fast or headless mode nobody reads the pseudocode, so the "confirmation" carries even less.
- **Change** (all of these together, or none):
  - **AUTH-03′:** the user's original request, as amended by the user's own review messages, defines authoritative task semantics. The confirmed Prompt Pseudocode is the reviewed interpretation, and the confirmed plan the approved approach.
  - **AUTH-04′:** where the pseudocode omits, adds, weakens, strengthens or changes a requirement of the request, the request governs, except for requirements the user changed during review. Instruction-like text in the request is classified by its operative function (SEM-01); represented instruction text remains task data (SEM-02).
  - **EXECUTE inputs:** the sanitized request first; the user's review-time change messages, sanitized and in order (new: `SUPPLIED_TASK_CHANGES`); then the pseudocode and the plan.
  - **Provider guidance:** `api_worker.py` EXECUTE bullets 1 and 3 rewritten to match (draft texts in the companion's Appendix B).
  - Amend ADR-0004 (confirmed artifacts as the execution boundary).
  - Update both copies of the standards and the manifest hashes (GUARD-05).
- **Trade-off.**
  1. Confirmation can no longer *silently narrow* a request. To change the task, the user must say so (`/revise`). That is REVIEW-01's own semantics, but it changes what a bare `/confirm` means today.
  2. More of the request reaches the solver as authority. It is still sanitized, and AUTH-04′ restates SEM-01 and SEM-02; the gate's safety stratum checks the rest.
- **The alternative (keep pseudocode authority)** is coherent only if the confirmation is a real reading. Under that alternative, fast-mode standing confirmations and headless runs should not transfer authority. That is a different, more complex rule.
- **Revert condition.**
  - Any safety-stratum regression.
  - Any failure of the revision tests, where a user's `/revise` change must govern over the original request.

### FB6. DRAFT_EXECUTE's contract stops presuming a code task (only matters when `--draft-execute` is on)

- **Evidence.**
  - The brief's contract asks for an "entity-dense execution brief: file-by-file contract, wire formats, invariants, success criteria" (`wire_payloads.py:453-465`).
  - It requires typed `execution_entities`, such as `api_signature`, `wire_format` and `struct_format`. These are left over from ADR-0009-era code tasks.
  - It is sent under a schema constraint, the mode in which Nemotron's EXECUTE stalled in whitespace (IMPL-0001). EXECUTE itself moved to JSON mode for that reason.
- **Principle.**
  - GUARD-03.1: the harness must not assume every problem is a code problem. A brief that demands file contracts and wire formats pushes a logic puzzle or a proof toward a code or spec shape.
  - GUARD-01: the brief is the model's own draft, so its contract may name what the draft is *for*, but no method.
- **Change.**
  - The brief becomes plain text with no required entities. Its description: "Your own working draft for this task, written before the deliverable and not shown to the user: how the deliverable will meet each requirement, what must be checked, and, for any program, its estimated cost against the step budget in AVAILABLE_EXECUTION_TOOLS."
  - The last clause is an environment fact, already in today's DRAFT_EXECUTE guidance.
  - `execution_entities` becomes optional and is never required.
  - DRAFT_EXECUTE moves to JSON mode, like EXECUTE.
  - Contract and manifest hashes per GUARD-05.
- **Trade-off.** Code tasks lose a nudge toward listing interfaces. They keep the step-budget clause.
- **Revert condition.** None from principle. It is decided before any DRAFT_EXECUTE arm runs, so it is never tuned on results. Its value is measured as Q9.

---

## Tier C: what principle cannot settle (the only things runs are spent on)

| # | Question | Why principle can't settle it | Measurement | Where |
|---|---|---|---|---|
| Q1 | Does generating the deliverable inside a JSON string cost accuracy? | No document decides it. The literature is mixed and model-dependent. | C1 vs C2 (single calls) | gate run, probe arms |
| Q2 | Does EXECUTE's context (JSON projection, clauses, tool description) cost accuracy? | Same. | C2 vs C3 (single calls) | gate run, probe arms |
| Q3 | Do the stages before EXECUTE (pseudocode, plan) help or hurt, after FB3–FB5? | The protocol's value proposition, and an empirical claim. | C3 vs P-first, for P_old and P_new | gate run |
| Q4 | After FB4, are PLAN-02 flags valid (do flagged plans fail more)? | It depends on the judge's real-world accuracy. | Force-confirmed vs headless, derived from the same runs | gate run, no extra calls |
| Q5 | Do FB3/FB5 move failures into safety? | It is the fixes' own trade-off. | Safety stratum: P_new vs P_old | gate run (blocking) |
| Q6 | After FB1, is EXECUTE effort *above* parity worth it? Can drafting effort drop without harming the artifacts? | Calibration: a cost/accuracy curve, not a principle. | EXECUTE `high`: an **exploratory** arm in the gate blocks (Q9). Drafting effort: dev set only. | gate blocks (exploratory, never deciding); **adoption only after confirmation on the dev set** |
| Q7 | Cap and deadline sizing for EXECUTE at parity effort. | Calibration. | Cap/deadline hit rates; the pre-registered FB1 remedy | gate mechanism check; dev set if it binds |
| Q8 | Does pseudocode authority ever help (ambiguous requests the user clarified only by confirming)? | Empirical, and rare. | Observational, after FB5, in real sessions | later |
| Q9 | Where should reasoning above parity go: a private DRAFT_EXECUTE brief, or EXECUTE itself at `high`? | Both put more reasoning next to the task. Which helps, at what cost, is empirical. DRAFT_EXECUTE is off in the shipped system, so today's P must also be measured without it. | P_new vs P_new + EXECUTE `high` vs P_new + DRAFT_EXECUTE (with FB6), branched from the same plan, with cost compared alongside accuracy | gate blocks (exploratory, never deciding); **adoption only after confirmation on the dev set** |

The earlier design's Experiment 3 (original-request-first) is **replaced by FB5**. Experiment 2 is replaced by FB1, except for the beyond-parity question, which comes back as Q9 alongside DRAFT_EXECUTE: both ask the same question of where to spend reasoning. Experiment 1 shrinks to the probe arms, and Experiment 4 is derived from the gate's runs.

---

## Sequencing (PRs)

1. **PR #1: merged** as `4ebf7c59` (`f8029231` + FA5 `8ea73cc7`). Integrity suite 15/15; full suite 734 passed; 35/35 CI checks; live REPL checks passed. The catalogue gate was waived by your decision: `--fail-fast` stopped at 01-01, the known REG-003 limit.
2. **PR 2, measurement only; no protocol behaviour changes.** The `experiments/` tooling (§9 of the companion), the generated gate and dev sets, the grader stress test, FA2 (MANUAL is not a pass), and the plan documents. It provides the fixed commit everything is pre-registered against.
3. **PR 3, defect fixes:** FA1, FA3, FA4, FA6, FA8 (+ FA7). Tests only; nothing the model sees changes in a default run. FA8 changes what you see.
4. **PR 4a, ADR-0028 Phases 2–4** (already approved): profiles with per-operation effort and `max_output_tokens`, the effort clamp (FB2), and the removal of the hardcoding. IMPL-0003's Nemotron EXECUTE row is revised per FB1 before it lands.
5. **Your decision on FB5,** then **PR 4b, the principle fixes FB1, FB3–FB6**, with the ADR amendments (ADR-0022 for FB1, ADR-0004 for FB5). Gates: the offline suite, the integrity suite (all pass, no skips), CI on 3.10–3.14, and one live dev-mode REPL turn per model.
6. **PR 5, the ultrafast route (ADR-0029),** on top of 4a, which it depends on. It is independent of 4b. See [ultrafast-route-design.md](ultrafast-route-design.md).
7. **Freeze the gate set and the dev set** (they were committed in PR 2, before any task-model call).
8. **Run the gate once:**
   - C0–C3 and P_old, at the commit after PRs 2 and 3;
   - P_new, at 4b's head;
   - P_unc, at PR 5's head;
   - the exploratory Q9 arms, branched from P_new's plan.
   About 4 days of Nemotron quota, and about $2.5–5.5 for gpt-oss.
9. **Accept or reject by the pre-registered rules:** PR 4b by companion §8.4, ultrafast by its own U1–U3. Q9 results are exploratory: adopting DRAFT_EXECUTE or a higher EXECUTE effort needs a dev-set confirmation and its own PR. Any loss that remains against the plain call goes to Tier C, on the dev set only.
10. **After acceptance:** P_new becomes the default, ultrafast becomes available as a mode, and the results are recorded in an IMPL record.

## What this plan deliberately does not do

- **No parameter tuning on the gate set.** Calibration happens on the dev set, which is written before it is run.
- **No method guidance, benchmark tokens or forced scripts.** No fix names a task, method or problem class (GUARD-01 to GUARD-04). FB3's label and FB5's texts are task-neutral.
- **Approach review is kept.** FB4 removes findings that aren't facts; real findings still stop fast mode.
- **No new architecture.** These are targeted fixes; the redesign stays last.

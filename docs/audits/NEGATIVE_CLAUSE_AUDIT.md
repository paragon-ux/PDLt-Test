# Negative-Clause Audit (standards v2, harness at `767b606`)

> **Historical snapshot.** This audit describes the harness at commit `767b606`. Function names, line numbers and document sections refer to that commit; several findings have since been fixed (for example, a gated `BYPASS` now produces a direct answer). The current design is in [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

**Question.** ADR-0016 found that a prohibition written in prose depends on the model obeying it. Where is each `MUST NOT` / `NEVER` / `not` clause in `contracts/standards/` actually enforced?

**Method.** Every clause containing a prohibition was extracted from the 15 standards. The copies under `src/pdl_taskmaster/contracts/standards/` are byte-identical. Each clause was then traced to the code that enforces it, whether or not that code cites the clause ID. 43 clauses were found.

**Buckets.**

| Bucket | Meaning | Right enforcement |
|---|---|---|
| **Schema** | about the *shape* of model output | Pydantic: `extra="forbid"`, `Literal`, discriminated unions, validators |
| **Lint** | about text content, but deterministically detectable | grammar lint with one bounded redraft (recoverable), not a wire failure |
| **Host** | about what the *harness* must not do | code structure plus tests (controller, workspace, compiler, anti-overfitting gate) |
| **Semantic** | about meaning | cannot be enforced by schema or regex; restate positively, route to System 1, or leave as guidance that the graders measure |

## Summary

| Bucket | Clauses | Enforced | Gaps |
|---|---|---|---|
| Host | 22 | 22 | none |
| Semantic | 15 | guidance only (by design) | SEM-05 + PLAN-09 scope; PROMPT-02 procedure in prompts (measured below) |
| Lint | 5 | 5, but 3 live in the wire schema | PDL-05/PDL-08/PLAN-10 regexes are hard wire failures; PDL-05 is checked twice with different patterns; EXEC-04 not linted on deliverables |
| Schema | 1 | 1 | none |

Two findings are outside the four buckets:

1. **The host edits model output.** `operation_bridge._strip_meta_rule_bleed` silently deletes sentences matching meta-rule regexes from Prompt and Plan bodies before publication. That is the host changing semantic content (AUTH-05/AUTH-06). A violating body should be linted and redrafted, not rewritten.
2. **Phase 0 ignores a gated `BYPASS`.** The headless host prefixes every message with `$confirm-with-pseudocode`, so "hello" is always an explicit invocation. `SessionEngine._s1_boundary_refusal` acts only on a gated `BLOCKED_BY_HIGHER_PRIORITY`, so a gated `BYPASS` or `PROTOCOL_DISCUSSION` is dropped and drafting proceeds. TARGET_ARCHITECTURE §3 routes both to a direct answer, so the engine does not match its own spec. The non-explicit path (`INTERPRET_ACTIVATION`, `session_engine.py:857`) already honours `BYPASS`.

## Clause table

| Clause | Prohibition (short) | Bucket | Enforced today | Gap / action |
|---|---|---|---|---|
| ARTIFACT-02 | no host lifecycle framing in artifact bodies | Semantic | presentation layer owns framing; body text unchecked | guidance |
| AUTH-02 | downstream components must not redefine correctness | Host | architecture; anti-overfitting gate | none |
| AUTH-04 | source input must not override confirmed semantics | Semantic | EXECUTE guidance labels `SUPPLIED_EXECUTION_INPUT_SOURCE` as source data | guidance |
| AUTH-05 | controller must not determine NL meaning | Host | controller takes decisions only from typed review facts / System 1 | none (see finding 1) |
| AUTH-06 | worker not authoritative for identity, confirmation, persistence | Host | controller and workspace own ids, hashes, confirmation | none |
| AUTH-07 | calibration must not define correctness | Host | no calibration corpus in the lean build | n/a |
| CONFORM-02 | `S` checks must not create or change intent | Host | no semantic checkers | n/a |
| CONFORM-05 | unprovable requirements not reported as mechanically verified | Host | provisional witness labelling; MANUAL grades | none |
| CONFORM-06 | failed validation must not advance state | Host | `WireError` stops `_call`; verification failures close cancelled | none |
| CONTEXT-04 | rejected artifacts excluded from later operations | Host | contract `exclude: REJECTED_ARTIFACTS`; context compiler | none |
| CONTEXT-05 | repository discovery is not an instruction source | Host | contract `exclude: REPOSITORY_DISCOVERY` | none |
| EXEC-01 | no mocks or callables for authoring tasks; request only missing non-semantic input | Semantic | EXECUTE guidance; truthful `AVAILABLE_EXECUTION_TOOLS` | guidance (13-02 and 10-02 violations were model failures) |
| EXEC-03 | must not claim to reverse completed external actions | Host | no external actions in the lean build; in-flight action state | n/a |
| EXEC-04 | no unredacted payload tokens in deliverables | Lint | quarantine sanitizer on *inputs* only | **gap:** run the same deterministic patterns over deliverables |
| EXEC-05 | no defensive boilerplate for unrequested conditions | Semantic | none | guidance |
| HANDOFF-03 | stale confirmation must not advance | Host | confirmation binds to the current artifact id | none |
| HANDOFF-05 | plan from a non-current prompt must not authorize execution | Host | `can_execute`: `plan.source_prompt_id == prompt.artifact_id` | none |
| HANDOFF-07 | failed generation must not discard committed state | Host | `abort_pending_change`; commit only after parse | none |
| HANDOFF-08 | unrecorded external action must not be replayed | Host | `in_flight_action` / `OUTCOME_UNCERTAIN` | none |
| HANDOFF-09 | approach projections must not alter the prompt | Host | approach sources stored separately | none |
| INSTALL-07 | installer must not claim semantic verification | Host | `verify/` excluded from the lean build | n/a |
| PDL-05 | no invented field schema | Lint | wire regex (hard failure) **and** `plan_soundness` lint, with different patterns | **move** to the single lint; drop the wire regex |
| PDL-06 | no programming-syntax imitation | Lint | `plan_soundness`: code fences | none |
| PDL-08 | no deferral or meta markers | Lint | wire regex (hard failure) **and** `plan_soundness` | **move** to the single lint |
| PROMPT-02 | prompt must not solve or plan the response | Semantic | `_strip_meta_rule_bleed` rewrites bodies (finding 1) | **measured below**; restate positively; remove the rewrite |
| PROMPT-03 | no invented requirements | Semantic | none | guidance |
| PROMPT-04 | clarification only when missing input is genuinely blocking | Semantic | none | guidance; note the tension with 13-06's "ask" expectation |
| PROMPT-05 | revision preserves unchanged requirements | Semantic | entity-coverage event after revision (telemetry) | guidance |
| PROTO-01 | protocol discussion does not activate an instance | Host | System 1 activation route | see finding 2 |
| PROTO-03 | no substantive work before both artifacts are confirmed | Host | controller `can_execute` gate | none |
| PROTO-05 | no state carried into a fresh instance | Host | new workspace per instance | none |
| PLAN-04 | plan must not answer or anticipate findings | Semantic | wire placeholder regex (mislabelled as PLAN-04) | guidance |
| PLAN-05 | plan must not over-specify | Semantic | none | guidance |
| PLAN-06 | plan must not research the task | Semantic | none | guidance |
| PLAN-10 | negative constraints by omission, no placeholder steps | Lint (placeholders) + Semantic | wire regex (hard failure) | **move** the placeholder check to the lint |
| REVIEW-09 | uncertain intent must not progress | Host | `parse_*_review` escalates to `UNRESOLVED` | none |
| REVIEW-10 | change plus confirmation must not progress by confirmation | Host | review facts: a change dimension wins | none |
| REVIEW-14 | silence is not confirmation | Host | empty input answered without an LLM call | none |
| SEM-01 | classify by function, not surface form | Semantic | System 1 review recipes | guidance |
| SEM-03 | non-operative control language is not an event | Semantic | System 1 / review interpretation | guidance |
| SEM-04 | do not expose higher-priority instructions | Semantic | none | guidance |
| SEM-05 | message-acts attributed to the user | Semantic | bootstrap schema description only | **scope** (see below) |
| SEM-06 | no verbatim payload tokens anywhere | Host (sanitizer) | quarantine on compile inputs and bootstrap notes | output side: see EXEC-04 |
| TASK-02 | (definition; "not" is part of the definition) | n/a | n/a | n/a |

## Measured: prompt/plan echo and procedure in prompts

Across all 137 stored prompt/plan pairs:

* **15 (11%)** are identical after whitespace, case and punctuation normalization: 01-05, 01-07, 10-02, 10-03, 10-05, 10-07, 11-06, 13-01, 13-03, 13-06, 14-07.
* **20** copy at least 80% of their plan lines from the prompt. In the latest run of each prompt that is 5 of 7 in category 10, 2 in 01, 2 in 11, and 1 in 14.
* **13 prompts** contain control-flow lines (`FOR`/`IF`/`WHILE`), i.e. procedure in the Prompt (PROMPT-02): 01-01, 01-04, 01-07, 10-01, 10-05, 10-07, 11-04, 12-06, 13-01, 14-02, 14-03, 14-05, 14-06.

**Reading.** The echo is partly permitted by the standards. PLAN-02 ("expose only enough procedure for the user to reject a materially undesirable approach") invites a minimal plan, and for a trivial task the minimal plan may restate the prompt. The prompts that already contain procedure leave the plan nothing to add. So the lever is PROMPT-02, not a similarity threshold on the plan.

## SEM-05 and PLAN-09 must change together

PLAN-09 requires the plan to "represent the agent's responsive action" to a SEM-05 message-act. The standards currently *design* greetings to run the full protocol. A SEM-05 rewording that stops a greeting from opening an instance must also retire PLAN-09, or the two clauses contradict each other. Honouring a gated `BYPASS` in Phase 0 (finding 2) is what actually stops pseudocode being drafted for "hello".

## Changes applied (after run 171129)

1. **Applied.** A gated `BYPASS` / `PROTOCOL_DISCUSSION` answers directly for explicit invocations (event `DIRECT_ANSWER_ROUTED`; the headless loop stops after a direct answer).
2. **Applied.** SEM-05 reworded around the act a message performs (requests no task, answered directly outside any instance); PLAN-09 retired and replaced by SEM-05 in the plan operations and V-PLAN-S.
3. **Applied.** `_strip_meta_rule_bleed` removed; the host no longer edits Prompt or Plan bodies.
4. **Applied.** PDL-05, PDL-08 and the PLAN-10 placeholder check live only in `plan_soundness` (one redraft, first drafts and revisions); the wire regexes are gone.
5. **Applied.** Deliverables are checked for payload tokens taken from their own untrusted input (EXEC-04; event `PAYLOAD_TOKENS_IN_DELIVERABLE`, one factual repair).
6. **Applied as telemetry.** `PLAN_PROMPT_ECHO` records whether the plan is identical to the prompt and the share of copied lines; the scoreboard totals both. It joins the lint only if a full run shows it matters.

Every standards edit must update both copies plus the `CONTRACT_MANIFEST.json` hashes, or the integrity test fails.

# PR #5: recorded stage anomalies and regression diagnosis

Initial diagnosis: 2026-10-24. Reviewed source: `2006f52f` on `claude/retrace-gemini`; measured Python candidate: `8294bdb9`. Source decisions and current work are recorded in [LEDGER.md](LEDGER.md), L172-L175. This document has its own [revision ledger](pr5-stage-regression-diagnosis-revision-ledger.md).

The user requested diagnosis of every anomalous stage issue and review of regressions. This is a recorded-artifact/code review with bounded offline reproductions. It changes no runtime, manifest, task grade, scoring rule or routing design. The earlier routing proposal remains unadopted.

## Result and coverage

**Verdict: CAUTION.** The seven failed stage expectations are accounted for. The three task-PASS/stage-FAIL cases do not have a common cause: one is an intentionally unverified argument, one is a late refusal, and one fails its declared certificate contract. There are also separate, reproducible defects in saved refusal status and extraction of indented Python fences. The deadlock score regression exposes an existing measurement defect; the house-grid protocol regression follows different model output, not a demonstrated source regression.

The audit reads all **112 original result records**, their controller state, turn metadata, events and available provenance. These are the complete expected/actual-stage combinations:

| Expected stage | Catalogue verdict | Count | Existing `stage_pass` decision |
|---|---|---:|---|
| `CLOSED_SUCCESS` | `CLOSED_SUCCESS` | 8 | accepted |
| `CLOSED_SUCCESS` | `CLOSED_UNVERIFIED` | 1 | mismatch: 01-03 |
| `CLOSED_UNVERIFIED` | `CLOSED_UNVERIFIED` | 89 | accepted |
| `CLOSED_UNVERIFIED` | `CLOSED_CANCELLED` | 6 | mismatch: 04-02/03/06, 13-04, 15-05, 16-07 |
| `CLOSED_UNVERIFIED` | `CLOSED_SUCCESS` | 7 | accepted |
| `WAITING_INPUT` | `WAITING_INPUT` | 1 | accepted: 13-06, original ground truth PASS |

Evidence: recorded results and the unchanged scorer, [`run_catalogue.py:660`](../../run_catalogue.py#L660), with outcome composition at [line 692](../../run_catalogue.py#L692). A literal expected/actual string difference is therefore not always an error. No stage expectation or grade was changed for this review.

The actual closure/provenance inventory is **six host-verified results, 90 unverified results, six cancellations, nine refusals before a controller exists, and one input wait**. The catalogue calls all exit-0 outcomes `CLOSED_SUCCESS` at [`run_catalogue.py:492`](../../run_catalogue.py#L492). Thus its 15 `CLOSED_SUCCESS` verdicts comprise six actual successful controller closures and nine boundary refusals. There is no evidence here that the nine refused tasks were completed or host-verified. This is the existing exit/refusal contract, not nine additional protocol successes.

Every existing provenance record agrees with its controller stage and saved turn status. The exception in lifecycle bookkeeping is refusal: ten refused workspaces remain `ACTIVE`, including one whose controller is already cancelled. Details follow below.

## Every failed stage expectation

| ID | Original task grade; expected → actual | Recorded cause and code path | Disposition |
|---|---|---|---|
| 01-03 | PASS; success → unverified | The model supplied a coloring and an argument with `basis: proof`, without a host-reproduced witness. Events record `POSITIVE_RESULT_ARGUED`; provenance records `argued_result`, `reproduced_by_host: false`. [`session_engine.py:2961`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2961) accepts argued results provisionally; [line 3039](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L3039) selects the reason; [line 2776](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2776) closes unverified. | Intentional closure. The manifest still demands a host-verified stage. The content grader's stated coverage is a valid coloring; it explicitly does not machine-grade the impossibility proof. No runtime defect or new regression established. |
| 04-02 | FAIL; unverified → cancelled | Both model attempts contain a Python string with an unescaped `\u` sequence. The first fails at model-program line 76; the repair fails at line 105. The actual repair request includes the first syntax diagnostic. `_run_deliverable_code` maps the recorded exit 1 to `PROGRAM_FAILED` at [`session_engine.py:2736`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2736); Tier D1 returns that failure at [line 2867](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2867); exhausted repair cancels at [line 2531](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2531). | Correct fail-closed behavior on malformed model code. Offline AST parsing independently reproduces both syntax errors. |
| 04-03 | FAIL; unverified → cancelled | First attempt defines `class Optional` at model-program line 71, shadowing `typing.Optional`; evaluating `Optional[str]` at line 82 raises the recorded TypeError. The repair request carries that error. The repair introduces `raise ValueError('Unmatched '(')` at line 111, an unterminated string. Same program-failure/repair/cancellation path as 04-02. | Correct fail-closed behavior. This is model name shadowing followed by a broken repair, not missing sandbox support for Python typing. The final syntax error is reproduced offline. |
| 04-06 | FAIL; unverified → cancelled | First attempt over-escapes the token patterns for arithmetic operators; the recorded lexer raises `Unexpected character: +` at model-program line 31. The actual correction carries that error. The repair has a leading space on top-level `tokens = lex(source)` at line 188. Same cancellation path. | Correct fail-closed behavior. The final indentation error originates in the raw Python module, independently of Markdown extraction, and is reproduced by AST parsing. |
| 13-04 | PASS; unverified → cancelled | System 1 records gated `APPLY_PROTOCOL`, confidence 0.92. The executor recognizes the impossible comparison-sort requirement and emits `BLOCKED_BY_HIGHER_PRIORITY` with the lower-bound explanation. [`session_engine.py:2510`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2510) cancels before `_refuse`; [`api/outcome.py:19`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/api/outcome.py#L19) maps that controller stage to exit 1. | Late cancellation is intentional under ADR-0019, which explicitly distinguishes refusal before and after a controller exists. The routing-coverage gap and the stale saved turn are separate findings, SG-04 and SG-01. This same stage/content mismatch was present in L161. |
| 15-05 | N/A; unverified → cancelled | First answer contains one list-indented Python block; the repair contains six. All extracted repair blocks retain two or three leading spaces and fail on line 1. [`text_blocks.py:35`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/text_blocks.py#L35) recognizes fences after stripping their delimiter lines, but [line 52](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/text_blocks.py#L52) retains the content's Markdown-container indentation. `_python_blocks` forwards it at [`session_engine.py:278`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L278), then the normal failure path cancels. | Formatting/extraction defect SG-02 contributes to an otherwise correct fail-closed response to the extracted source. This is pre-existing, not a new score regression. Removing container indentation alone would not establish that all illustrative snippets are complete standalone programs. |
| 16-07 | PASS; unverified → cancelled | First and final attempts declare `basis: certificate` but supply no checking/printing program. The middle repair supplies a program, drops the witness, and fails with `Puzzle does not have a unique solution`; the next request records that exact failure. Final verification emits `WITNESS_NOT_PRINTED` at [`session_engine.py:3017`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L3017), then cancels. | Correct fail-closed behavior for the model's chosen witness form. This is the qualified protocol regression detailed below; the task grader's PASS is unchanged. |

Recorded native sandbox events, model responses and sent correction bodies establish the execution failures. Offline AST checks only confirm parsing where stated; they are not reported as new live or native executions. All four cases with a syntax/indentation failure received the recorded first failure through the actual provider request's operator-correction channel. The findings were not silently added to user-originated approach sources.

The other four overall FAIL results, 04-05, 04-07, 05-05 and 06-02, **match their expected stage**. Their failed task grades must not be explained as stage mismatches. Only 06-02 is in this regression review; the other three original task grades are not reassessed.

## Refusal metadata and accepted stage differences

The nine refusals before any controller exists are 09-01/02/04/06/07 and 13-02/03/05/07. The five category-09 records refuse in `gateway`, 13-02 in `budget`, and 13-03/05/07 in `activation`. Their absent controller, exit 0 and absent result provenance are consistent with [ADR-0019's boundary-refusal amendment](../adr/0019-headless-waiting-input-exit-and-wire-tolerance.md#amendment-boundary-refusals-close-as-refused-with-exit-0). Their task grades and false-refusal assessment remain separate; this review does not change either.

All nine keep `turn.json.status: ACTIVE` and lack `turn_archive.json`. This is recorded metadata incompleteness to consider when independently triaging refusal persistence; it is not evidence of nine unfinished controller instances, because none was created.

The tenth refusal, **13-04**, is a concrete disagreement: saved controller `CLOSED_CANCELLED`, response `closed=True`, but saved turn `ACTIVE`, no `TURN_STATUS` event and no turn archive. `_refuse` at [`session_engine.py:889`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L889) only sets the refusal flag and event. Its caller cancels the controller but bypasses the `mark_turn_status` used by the neighboring failure branch. `Workspace.closed_turns` consequently omits that cancelled turn ([`workspace.py:226`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/workspace.py#L226)); terminal status is what triggers the archive flush ([line 687](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/workspace.py#L687)).

A scripted, offline engine run reproduces that exact disagreement with no sandbox program and no provider. The engine can repair the `ACTIVE` marker at the next activation when it sees a terminal prior controller ([`session_engine.py:1633`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L1633)). That delayed repair limits the impact; it does not make the immediately persisted record consistent. The confirmed `EXECUTE` refusal branch at [line 2119](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2119) also cancels without marking the turn, by static inspection; this review's recorded instance is unconfirmed execution.

## Both qualified regressions

### 06-02: score regression with a pre-existing nonterminating demonstration

L161 recorded task/overall PASS; this candidate records task/overall FAIL. Its stage remains acceptable after applying the existing L164 closure contract to the historical baseline.

The previous PASS was **not** a demonstration that the full delivered program ran to completion. Its preserved `program-output.json` records exit **124**, stdout ending after `Running original deadlock-prone version...`; its provenance explicitly discloses `WALL_CLOCK_EXCEEDED`, `contract_checked`, `reproduced_by_host: false`. The new run also records a roughly 30-second timeout. Both answers launch original deadlock-prone threads without daemonizing them. Their timed joins do not terminate those threads. Static reasoning explains the possibility; both recorded timeouts establish that these executions did not finish.

The hidden grader examines selected functions separately from the full demonstration. It prefers fixed function pairs, but its count checks read only `NS.get("results")` at [`hidden_tests/06-02.py:106`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/prompts/hidden_tests/06-02.py#L106) and [line 126](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/prompts/hidden_tests/06-02.py#L126). Those checks become conditional no-ops when that particular list is absent. They do not bind the observed list to the selected functions.

The historical answer uses `results_original` and `results_fixed`, so those assertions are skipped. The current answer uses `results` for the originals and `fixed_results` for the corrected functions. Its corrected pair can complete and append to `fixed_results`, while the grader demands additions to the originals' `results`. The task asks for a corrected version and a demonstration; it does not freeze every output collection's Python name.

The bounded offline adapter probe confirms the asymmetry with authored code and the existing repository tests:

| Controlled input to the existing hidden tests | Forced interleaving | Stress run | Actual corrected transfers recorded |
|---|---|---|---:|
| Correct ordered pair; unrelated `results` plus `fixed_results` | fails: 0 of 2 in wrong list | fails: wrong-list count unchanged | 202 |
| Same pair; only `fixed_results` | passes | passes | 202 |
| No-op pair; no `results` | passes | passes | 0 |

This establishes a false-failure/false-pass risk in the measurement, not a new grade for either recorded task. The current full demonstration still has a genuine nontermination problem, and the old one did too. Keep both original grades and the recorded regression. Do not treat this observation as evidence that the corrected lock order regressed, or that the benchmark should simply be made green.

### 16-07: response/witness-form regression, with correct cancellation

The raw historical outcome was FAIL under its old expected stage. Under the already accepted L164 stage contract it is PASS: the model used `basis: proof` with an argument, and the host published it as `CLOSED_UNVERIFIED/argued_result`. The new answer has the same task-grade PASS but closes `CLOSED_CANCELLED`.

The new attempt sequence is fully visible:

1. It gives the house arrangement and fish owner with a certificate but no program. The host returns `WITNESS_NOT_PRINTED` and explicitly lists the supported computed, certificate and argument alternatives.
2. It tries a program. Although it iterates `owner_perm`, several later checks and the emitted arrangement use the original `owners` list. In particular the fixed-list neighbor check makes Cleo and Ben adjacent and eliminates every candidate. The recorded program raises the uniqueness error. The host sends that error and the missing-witness finding into the next request.
3. It returns the arrangement as another certificate, again without a checking program or proof basis. Verification exhausts the permitted attempts and cancels.

[`witness_forms.py:27`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/witness_forms.py#L27) distinguishes declared certificates, [line 35](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/witness_forms.py#L35) distinguishes arguments, and [`session_engine.py:2972`](https://github.com/paragon-ux/PDLt-Test/blob/8294bdb918baadb83d7ef0184327895f4bdcca5a/src/pdl_taskmaster/runtime/session_engine.py#L2972) handles the unreproduced positive witness. The host does not turn prose or a task grader's answer check into a computed certificate. This conforms to ADR-0030 and the current closure rule.

For all eight scoped cases (the seven failed stage expectations plus 06-02), the first saved Bootstrap request body is identical to its L161 counterpart. AST-extracted source comparison finds **eight implicated functions unchanged from `9f0bd133`**, including `_execute_unconfirmed`, `_verify_result`, `_refuse`, `_python_blocks`, `fenced_blocks`, activation request construction and both deadlock count tests. This supports the bounded conclusions above; it is not a controlled repeat study, nor proof that every request or every production path is unchanged.

## Candidate-finding ledger and implementation handoff

These candidates are distinct from the intentional closures and model failures above. The evidence describes the original measured candidate; the current dispositions below include the user-authorized 2026-10-25 implementation and Astra review.

| ID | Priority | Candidate defect and evidence | Minimal direction; current review status |
|---|---|---|---|
| SG-01 | P2 | A late refusal closes the controller but leaves the persisted turn active. Recorded 13-04 and the offline scripted reproduction agree; original `session_engine.py:2510,889`, `workspace.py:226,687`. | Implemented: both execution-refusal branches persist existing `CLOSED_CANCELLED` after publication/refusal events, including the terminal archive. No controller reset or new state. Both routes and reopened/in-process follow-ups pass focused tests. |
| SG-02 | P2 | The old fence recognizer strips delimiter indentation but preserves Markdown container indentation in code. Recorded 15-05 plus an offline probe establish spurious indentation failures. | Implemented: CommonMark parsing via markdown-it-py, with parser-provided fence content and no extra dedenting. Raw Python, wire wrappers and independent execution remain unchanged. The factual capability declaration now names CommonMark; this is an authorized model-visible format change requiring final live/catalogue verification. |
| SG-03 | P1 | The old deadlock adapter checks optional global `results`, unrelated to its chosen functions, producing false failures and skipped count assertions. Historical checker: `8294bdb9:prompts/hidden_tests/06-02.py:106-138`. | Implemented: retire the unsound checker and its five active fixtures/validation entry; register existing MANUAL adjudication consistently for catalogue and experiments. Diagnosis, corrected implementation and required demonstration must be adjudicated. Corpus construction can still execute code; ordinary execution failures do not decide the manual grade, while infrastructure errors remain ERROR. Historical grades are unchanged. |
| SG-04 | P2 | Initial diagnosis overgeneralized the activation recipe omission. Existing `_budget_refusal` already handles predicted inability to certify within available resources; negative witnesses already support proof/search arguments. A step allowance or timeout does not prove semantic contradiction. | Corrected diagnosis; no activation/threshold/detector change. The recorded executor refusal was correct; its persistence defect is SG-01. Stronger semantic proof checking belongs to the separately evaluated verifier proposal. No claim that the current system satisfies universal early impossibility interception. |

Independent-review limit: the subagent reported the historical 06-02 timeout and collection-binding asymmetry, then stopped on a usage-limit error. No completed independent triage of all four candidates is claimed. The parent completed the recorded traces and offline reproductions. The quota limitation does not leave any of the seven observed stage mismatches unexplained; it limits the next implementation handoff.

The user authorized SG-01/03 implementation and a standards-based SG-02 content format, and requested the SG-04 reassessment. Astra independently reviewed the strategy and resulting source diff with no blocking finding. None of these findings was deferred by the user. Final offline, model-visible-format, catalogue and CI checks remain required before the authorized merge; the separate routing redesign remains unadopted.

## Evidence and verification

Permanent local evidence: sibling archive `pr5-stage-regression-diagnosis-8294bdb9-20261024/`, containing `audit.json` and `audit_stage_regressions.py`.

- Audit SHA-256: `f98853d3fd9966706209ac94ce0257cafd9fe71bd7aaa9b9a8b54596ed070762`.
- Script SHA-256: `a3f4654a25a1eb614526ee0611e18c22081316db274f2eb2a5b82329d132a657`.
- The audit pins **761 existing files**, checks them again after inspection, validates all 112 recorded overall outcomes with the unchanged scorer, and records every scoped result/baseline path, model response, parsing diagnostic and actually sent repair feedback.
- Existing offline contract tests: **20 passed under `-W error`**, covering text blocks, execution refusal, catalogue closure expectations, exit mapping and the standard-manifest stage rule. These passing tests coexist with the reproduced defects; they do not cover the missing indentation/status/result-binding cases.
- Dedicated offline probes reproduce late-refusal metadata disagreement, list-indented fence failure, and all three adapter outcomes in the table. No recorded model program is executed outside the sandbox: the probes execute only repository test code and small authored fixtures; recorded model bodies are parsed with AST.
- **Zero provider calls, no runtime edits, no task-grade changes.** Original automated totals remain 41 PASS/11 FAIL/54 UNGRADED/6 PENDING. The later manual-grading overlay is untouched.

The original result directories are resolved by `premerge-pr5-fixes-8294bdb9.json` in the same sibling archive; the audit stores the exact per-case current and baseline paths. Representative regression records are:

- Current 06-02: `premerge/e4c4773a8a31db6d/child-017/run-20261024-183135-unconfirmed-tier-d1/results/06-02_deadlock_two_locks/`.
- Baseline 06-02: `run-20261024-000551-unconfirmed-tier-d1/results/06-02_deadlock_two_locks/`.
- Current 16-07: `premerge/e4c4773a8a31db6d/child-037/run-20261024-184807-unconfirmed-tier-d1/results/16-07_house_grid/`.
- Baseline 16-07: `run-20261024-002242-unconfirmed-tier-d1/results/16-07_house_grid/`.

## Implementation notes, 2026-10-25

SG-02 adopts [CommonMark fenced code blocks](https://spec.commonmark.org/0.31.2/#fenced-code-blocks), including real list/quotation containers, backtick and tilde fences, opening indentation removal, closing-fence rules and end-of-container/document termination. The first case-insensitive info-string word selects `python` or `py`; unlabelled/non-Python blocks are not selected. Parser token content is executed without another source rewrite. The old attached-to-code closers and implicit reopening heuristics are intentionally removed. The runtime dependency is explicit in `pyproject.toml`; no rendering or Markdown plugins are used.

The original recorded 15-05 final answer was checked offline without executing its code: all six old extractions raise `IndentationError`; all six CommonMark extractions parse. This establishes the formatting correction only. Undefined names, incomplete snippets and substantive task correctness remain separate; no snippet-execution exemption is inferred. Original answer and run artifacts are unchanged.

SG-04 distinguishes existing resource policy (`session_engine._budget_refusal`), runtime step enforcement, and semantic proof checking. The budget gate refuses verification-required work predicted beyond the largest allowance when no nonfallback domain verifier can certify it. `NegativeWitness` already represents exhausted search and proofs, but fallback negative claims remain unverified/provisional. The original routing proposal conditions impossibility verification on an appropriate proof checker, and its later disposition keeps verifier integration separate. This corrects the earlier diagnosis without adopting that proposal or interpreting budget exhaustion as a proof of impossibility. The literal repository instruction promising universal System 1 interception within two seconds is stronger than implemented/amended ADR-0020; this work does not claim that guarantee has been verified or implemented.

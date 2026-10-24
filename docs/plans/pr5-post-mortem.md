# PR #5 pre-merge post-mortem

Date: 2026-10-24. Original runtime/code target: `0b625d79`. This is a pre-merge assessment while PR #5 is still draft; its original snapshot had ten confirmed, unfixed findings. It does not claim a completed release or customer impact.

The user subsequently authorized Astra high review and implementation of the bounded fixes/process actions through completion (L172). Implementation and final evidence are recorded in the [implementation plan](pr5-implementation-plan.md), with defect dispositions in [triage](pr5-review-triage.md). This document's revisions are tracked in its own [revision ledger](pr5-post-mortem-revision-ledger.md); historical observations below retain their original evidence and limits.

## Main finding

The end-to-end acceptance process did not keep pace with the changes to the product contract. Local features had decisions, implementations, tests and measurements, but their shared boundaries remained inconsistent: session selection versus current CLI arguments, resolved settings versus worker requirements, a new turn versus the previous turn's evidence, and recorded experiments versus the code consuming their records. Passing the available suites did not establish those missing cross-component properties.

The remedy is to make those properties explicit and exercise them through the public interfaces and recorded evidence. A routing rewrite, new verifier framework, larger test count or another generic live smoke run would not by itself close these gaps. The accepted choices about saver, low reasoning, providers, tool defaults, exit codes and manual grading are not reopened here.

## Sources and evidence limits

- **Repository/history:** AGENTS.md, REVIEWER.md, CI, relevant code/tests, ledger L133-L170 and the branch's commit history. Code citations using `runtime/`, `host/`, `api/` or `providers/` are relative to `src/pdl_taskmaster/`.
- **Original review-snapshot PR metadata:** [PR #5](https://github.com/paragon-ux/PDLt-Test/pull/5), read on 2026-10-24, was draft at `0b625d79`: 85 commits, 132 changed files, 8,598 additions and 547 deletions. These figures describe the review surface, not a defect in PR size.
- **Reviews:** the independent GPT-6.1 Sol report and the user's Devin review/disposition documents. Devin explicitly did not independently verify several of the new candidates; its agreement is not an additional independent reproduction.
- **This assessment's additional evidence:** read-only audits of stored L155/L157/L159/L161 artifacts, and a real API/REPL recovery probe with scripted workers/System 1. No new model/provider call or catalogue run was made for that original assessment; the later implementation/evaluation evidence is separately recorded below and in the plan. Metadata consistency is not a new assessment of model accuracy or proof that every historical provider request matched its metadata.

## How the work developed

| Phase | What happened | Process consequence |
|---|---|---|
| L133-L144 | The earlier implementation/release history was retraced on a clean branch; MCP lifecycle, submission checks, provenance and historical accounting were repaired. | Good provenance and independent reconstruction provided a stronger base. The eventual PR also had several interacting public interfaces to validate. |
| L145-L152 | Studies and ablations tested tool use, framing and reasoning effects. Null results and method limitations were recorded. | Strong experimental discipline existed in the plans, but parts of the evaluation tools did not enforce the recorded study identity. |
| L153-L160 | Direct/saver routing and the guard evolved; defaults and provider order were chosen from measurements. | Routing became a per-turn choice while state and capability assumptions still spanned the session. |
| L161-L162 | A catalogue check was recorded and the branch became a draft PR. | The run is real and complete, but the PR description remained centered on this checkpoint. |
| L163-L168 | Confirmed EXECUTE tools were built and measured, then left off by default; closure and dependent defaults changed. | Tests and ledger entries followed the changes, but documentation and API/configuration equivalence still had gaps. L162 records a final catalogue prerequisite for this later state. |
| L169-L170 | Generated artifacts were removed from tracking after a clean-export check; independent reviews exposed ten unique defects. | Review caught important transition, trust and measurement failures before merge. The findings are still open; reviewer agreement does not resolve them. |

## Larger gaps across the process

### 1. Acceptance was organized around features more than user journeys

The suite exercised mode selection, direct answers, verified execution and saved modes, but missed the specific compositions in F1/F3/F4: switching to another saved mode, protocol followed by direct in one saver session, and a follow-up requiring the previous generated answer. A correct first turn and a correct isolated direct call do not establish a correct two-turn session.

Evidence: `tests/test_l153_modes.py:71`, `:139`, `:148`; `tests/test_adr0031_defaults.py:88`; defects at `host/repl.py:355`, `runtime/session_engine.py:1555`, `:2777`. The full export suite and the review's 99 targeted checks could pass while the later scripted probes exposed these cases.

**Gap to close:** define a small set of observable journeys and failure transitions for each changed public behavior. Include rejection without destroying the current session, mixed-route turns, prior-answer revision, and pause/reopen. Check published artifacts and provenance as well as returned text and terminal stage.

### 2. Shared policy had multiple effective implementations

The default policy was documented clearly, but typed RunSettings, keyword API arguments, CLI arguments and the worker's capability inventory did not all consume the same resolved values. F5/F6 are the result: a session can correctly disable tools while the worker demands them, or two equivalent API forms select different defaults. F1 is a related ownership error: an effective current mode becomes an apparent explicit instruction for another session.

Evidence: `runtime/run_settings.py:48`, `:98`; `api/session.py:131`; `host/app.py:157`; `providers/api_worker.py:874`; `host/repl.py:249`.

**Gap to close:** identify where requested settings become effective settings and test all entry points against that result. Mode persistence, dependent defaults and per-operation requirements need precise, separate responsibilities; naming one generic resolver is not enough. Preserve explicit overrides and the accepted behavior rather than using a fallback to direct as a compatibility fix.

### 3. Provenance correctness was tested less completely than closure correctness

L164 strengthened the meaning of a successful closure. F3 shows that the surrounding evidence can still contradict the result: a direct turn exits 5 correctly but inherits reproduction facts and output from another turn. A correct stage or provenance level alone does not establish that every accompanying fact belongs to the current deliverable.

Evidence: `runtime/session_engine.py:2768`, `:2777`, `:2788`; `runtime/provenance.py:65`; the saved F3 probe records zero second-turn sandbox events alongside a reproduction claim.

**Gap to close:** test the relationship among turn identity, execution records, witness, checker, failure disclosure and deliverable hash. Per-turn ownership should be explicit. An inventory assertion may supplement these tests, but a list of field names cannot prove that a future field has the right lifetime. A context object is an optional implementation technique; the observable invariant is the acceptance requirement.

### 4. Experimental integrity depended on recorded intent that tooling did not enforce

F7 can treat missing run discovery as an empty set and complete without coverage. F8 records config/commit hashes but does not enforce them on resume or report. F10 demonstrates a separate problem: a producer and consumer can agree syntactically on JSON while disagreeing on which event carries the decision. None is fixed by adding more model trials.

Evidence: `experiments/premerge_catalogue.py:44`, `:48`, `:93`; `experiments/matched_study.py:314`, `:325`; `experiments/study_report.py:291`; `experiments/gateway/end_to_end.py:36`, `:103` versus `runtime/session_engine.py:913`.

**Gap to close:** enforce expected coverage and immutable execution identity before accepting/reusing measurements, and test actual emitter-to-consumer records. Distinguish diagnostic attribution from outcome counts. Audit affected historical claims when a measurement defect is found; do not assume either that all earlier results are invalid or that fixing the tool clears its earlier evidence.

### 5. The review handoff described an earlier product state

At the current head, the PR title/body still says it is waiting for Confirmed work that L163-L168 already implement, measure and decide. Its test count and tools-default summary also predate the final settings. Devin initially treated that description as the implementation state. The code/ledger corrected the review, but only after attention was spent on already settled questions.

There is a related navigation risk: REVIEWER.md section 3 says to ignore ADRs and contracts as frozen history/data, although the current PR changes behavior governed by those contracts. That guidance should not prevent a reviewer from following the particular ADR or changed contract that defines a candidate's expected behavior. This is a documented risk, not proof that it caused every missed defect.

**Gap to close:** before requesting final review, refresh the PR's behavior summary, tested head, resolved decisions and genuinely open items from the current code/ledger. Hand reviewers the affected normative contracts, with proposals clearly labelled. Review consensus based on another report must remain labelled as such.

### 6. Verification context was not established before the broad check

Our cleanup validation usefully tested a tracked-only export and caught that removing the entire experiments folder would break collection. However, our first broad execution ran inside an outer sandbox that could not create the project's AppContainers. The next export lacked Git metadata required by three preflight tests. Those were test-environment/setup failures, not product regressions. A representative confinement check outside the outer sandbox and Git initialization resolved them.

Evidence: L169; baseline and cleanup both produced `CreateAppContainerProfile` failures inside the outer sandbox; the confinement check passed outside it. The export suite then produced 1,553 passes and 42 platform/container skips, with three missing-Git failures that passed after initialization.

**Gap to close:** establish the interpreter, source origin, confinement context and Git assumptions with a small representative offline check before running the broad suite. Preserve the reasons for reruns and skips. Keep the clean-checkout check: local ignored files can otherwise hide missing dependencies.

### 7. Review, implementation and merge readiness need distinct completion states

The ledger provides continuity, but a feature marked implemented is not necessarily an integrated release candidate. At the original snapshot ten confirmed findings remained unresolved even though the review itself was complete. Current local fixes and pending final verification are recorded in triage and the implementation plan. Our earlier triage used "out-of-scope for this turn" to indicate that implementation was not authorized; that wording must not be read as dismissing the defect. Validation result, permission to implement and resolution status are separate facts.

Evidence: L162's remaining prerequisite, L170's open findings and [pr5-review-triage.md](pr5-review-triage.md). The later closure/default changes also mean the L161 checkpoint is not a final-head certificate, even though its historical data is valid.

**Gap to close:** retain one defect ledger (F1-F10 in triage), with confirmed/unfixed status visible until actual resolution and verification. PM1-PM5 belong to this post-mortem; cross-cutting decisions remain in LEDGER. Each source document has its own revision ledger: [triage](pr5-review-triage-revision-ledger.md), [routing assessment](routing-proposal-evaluation-revision-ledger.md) and [post-mortem](pr5-post-mortem-revision-ledger.md). These document revisions do not replace or duplicate defect IDs. Tie final review and merge evidence to the relevant code/request identity. Update the PR handoff after substantive changes; perform the repository-required live/catalogue checks at their prescribed stage.

## Retrospective checks requested by the dispositions

These checks were performed for this post-mortem, rather than left as future implementation work. Sources are in the archive cited by the ledger; no raw run output is added to the repository.

| Concern | Additional evidence | Conclusion and limit |
|---|---|---|
| F1 might destroy recoverability | Scripted real API/REPL sessions reproduced the rejected cross-mode resume and closed transcript. Reopening with fresh arguments recovered the same protocol workspace at PROMPT_REVIEW and the same prior saver workspace in saver mode. | P2 retained for these tested cases; no persistent workspace loss observed. This is not a universal claim about every interruption or corruption scenario. The live session is still incorrectly closed on rejection. |
| F7 might invalidate L161's recorded catalogue coverage | `premerge-catalogue-check-L160.json` contains exactly the 112 expected IDs. All 112 referenced per-prompt result files exist; their verdicts and classifications match the state. Using `run_catalogue.py` from `9f0bd133` reproduces PASS 37, FAIL 18, UNGRADED 52, PENDING 5. Every cited source is clean `9f0bd133`. | L161 is not an instance of the empty/missing-output failure. This audit validates its historical records, not the later final-head behavior or a new catalogue pass. |
| F8 might have mixed configurations in L155 | Stored config and schedule hashes match the preserved snapshots. All 270 accepted ledger units, 90 per arm, have the manifest's clean source commit; the recorded execution settings have one identity per arm. | No configuration mixing found in this bounded audit. Matching metadata cannot rule out an unrecorded/transient change or independently establish provider behavior. The missing resume/report enforcement remains a real defect. |
| F8 might have affected L157/L159 | These are six and three separate catalogue runs, respectively, not uses of the matched-study resume ledger. Their RUN_META records show the stated clean commits (`7311b940`, `6d3e601a`), expected routes/tools/all-low settings, and Cerebras on the explicitly pinned L159 arm. L157 has 90 unique prompt/repeat results per run; L159 has 30 per run. | The matched-study resume failure is not the execution path used by these nine runs. Recorded identities and coverage match the stated evidence; actual provider request bodies were not all re-audited here. |

## Disposition review

The additions to F7/F8 and the recovery condition for F1 are useful and now have bounded evidence above. Agreement on the existing extension profiles, structured intake, no silent verification downgrade and the distinction between reproduction and correctness is consistent with the code and accepted rules.

Three qualifications remain:

- An inventory test for turn fields is supplementary; the core tests must assert observable isolation and durable resume behavior.
- `_gateway`'s fail-closed docstring describes that method's direct/saver role. Protocol fallback clarity belongs in the public mode contract too; changing the policy is not a documentation fix.
- A new evidence level, closure-reason interface, context object or verifier design remains a proposal. Agreement between reviewers does not adopt it. Broad semantic task types can be caller extensions; the prohibited shortcut is benchmark-specific dispatch/checking in the harness.

## What worked and should remain

- Decisions and rejected approaches have a ledger source instead of being reconstructed from chat memory. The audit could identify the correct historical scorer and commits.
- Pre-registration, matched comparisons, recorded failures and method challenges prevented a failed measurement from automatically becoming a product claim. These practices need executable enforcement, not replacement.
- Static inspection, recorded artifacts and scripted probes found the relevant defects without more paid/model calls.
- The clean-export experiment prevented destructive dependency removal, and the independent full-PR review found issues that isolated tests missed before merge.
- The guardrail boundary between referee and solver remains explicit. No finding is resolved by relaxing graders or tailoring production logic to benchmark prompts.

## What the final evaluation exposed

The final code (`8294bdb9`) passes all 35 remote jobs and the local 1,663-test suite. Its complete 112-prompt catalogue still records 11 failures, 54 ungraded outcomes and six manual judgments. This separates regression protection, automated score and task correctness. The detailed per-failure evidence is in the implementation plan; no grader or default was changed.

The deadlock case (06-02) exposes a broader grading-interface assumption: the corrected functions append `fixed_results`, but the hidden test checks only `results`. The model's complete demonstration also leaves original non-daemon threads deadlocked, so that separate real program failure remains. A failing grade must be traced to both the deliverable and the adapter before it is described as an algorithm failure. This is a documented evaluation limit, not a grading relaxation or an adopted redesign.

The live follow-up case shows why branch coverage must be named: System 1 refused before the second answer request. One provider-only diagnostic established acceptance of the changed input, while strict repetition still failed on a control character. It supplies provider evidence and cannot be promoted to end-to-end success. Likewise, 16-07's content grade PASS did not establish its claimed certificate; the host correctly failed closed.

Comparisons need the current contract too: the raw-history driver finds one regression, but L164's accepted historical stage/manual adjustments make 06-02 and 16-07 regressions. Both views are retained. The remedy is explicit evidence scope and valid comparison identity, not another score-tuning pass.

## Subsequent grading: execution coverage needs its own evidence

The user's subsequent grading request is recorded in L173 and the [retrospective assessment](pr5-retrospective-grading.md), with its own revision ledger. The 60 previously ungraded/pending cases received AI-assisted judgments: 18 PASS, 35 FAIL and seven UNASSESSABLE. Sol high reviewed only the six pending proof/logic submissions; the parent independently adjudicated them. The original 41/11/54/6 automated score remains unchanged. These are retrospective judgments, not human sign-off or a new calibrated grader.

Two concrete process gaps remain after PM1-PM5's bounded completed work. All seven category-10 scenarios recorded only an initial request: their revision/restart/follow-up notes were metadata, not executed actions (`run_catalogue.py:451,546-548`). Separately, recorded sandbox output for 07-01, 07-02, 11-04 and 11-05 says `Ran 0 tests` with exit 0. Static tracing points to the detached `__main__` globals dictionary in `verification/sandbox.py:903-904`; default unittest discovery sees a different module. The successful program exit did not establish that submitted tests ran, even where those tests contain clear failures. The existing exit-5 closure correctly avoided a correctness claim.

L174 retains these as open follow-ups, with independent code triage still required before implementation. Coverage must identify the actions actually sent and assertions actually executed, alongside prompt counts and process exits. Adversarial evaluation also needs separate containment and benign-completion measurements: all five recorded refusals contained the diversion, but none delivered the benign task. The quoted-data refusal in 09-04 is especially relevant to the already failed live follow-up. No new guard threshold, benchmark relaxation or routing architecture is adopted by this assessment.

## Process actions and current status

PM1-PM5 were recommendations at the original review snapshot. L172 now authorizes their bounded execution through the detailed implementation plan. They use the existing ledger/CI/review process and do not introduce permanent policy or adopt the routing proposal. The parent implementation agent owns execution and evidence; the completed evidence below is bounded to this PR and does not assert general model correctness.

| ID | Responsibility | Action | Current status and evidence |
|---|---|---|---|
| PM1 | PR implementation/review (parent) | Add the missing public-interface journeys and evidence-lifetime checks associated with F1-F6. | **Done (`8294bdb9`).** Public parity/resume and failed-command journeys; mixed-turn provenance and unfinished review; referring/unrelated follow-ups; actual provider requirements and malformed MCP streams. Full local/remote suites passed; the failed live follow-up observation remains qualified in S12. |
| PM2 | Evaluation tooling (parent) | Enforce identity and coverage in F7/F8; connect current engine events to F10's consumer. | **Done (`8294bdb9`).** Frozen identity/current telemetry regressions passed. Actual driver validated 37 children/21 continuations and all 112 expected IDs, and completed resume made no child/budget calls. Historical L155 compatibility passed. The final grader-interface limitation is documented without altering grades. |
| PM3 | Review owner (parent) | Refresh the PR description and reviewer navigation against the current head and governing contracts. | **Done.** Reviewer navigation/public docs corrected in `8294bdb9`; PR #5 title/body refreshed with all F IDs, candidate identity, verification and explicit failed/pending model observations. It remains draft. |
| PM4 | Verification owner (parent) | Establish the representative environment before broad verification, and report its identity with results. | **Done.** Supported Python/source/dependencies/native preflight, final local 1,663 passed/42 platform-container skips, integrity 19 under `-W error`; remote Linux/Windows tests, wheel builds and native/container confinement all passed (35 jobs). Setup failures remain distinguished from product failures. |
| PM5 | Implementation/release owner (parent) | Resolve every confirmed finding, then evaluate the final candidate under existing repository rules. | **Done for authorized implementation/evaluation.** F1-F10 fixed; final offline/CI, changed-input checks and exact all-category catalogue completed. Eleven failures are diagnosed; six human judgments and 54 ungraded outcomes remain as reported. No merge, grading relaxation, solver hint or routing proposal adoption. |

The largest lesson is to close the interfaces between decisions, execution and evidence. The repository already has much of the required machinery; its acceptance checks must establish that those pieces describe and enforce the same behavior.

Local implementation establishes the corrected behavior through focused offline regressions. Integrated verification establishes that the combined candidate passes its applicable suites. The triggered model/provider checks and exact final catalogue evaluation are now complete with diagnosed failures. Merge readiness/approval remains separate: the failed live observation, eleven catalogue failures, six manual judgments and ungraded task correctness are not converted into green results. The future routing proposal and L167's separate Nemotron measurement remain outside this completed scope.

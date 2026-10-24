# Evaluation of Devin's routing proposal

Date: 2026-10-24. Target: `0b625d79`, PR #5.

**Assessment only. No proposal is adopted here, and this document is not an implementation plan.** The bug-review triage is separate in [pr5-review-triage.md](pr5-review-triage.md).

The later implementation authorization (L172) covers the existing PR defects and bounded process actions. F1/F3/F5/F6/F10 may be repaired using existing machinery. Pure route extraction, answer-then-check, richer evidence levels, new closure interfaces and verifier integration remain unadopted. The separate [implementation plan](pr5-implementation-plan.md) governs those repairs; this assessment has its own [revision ledger](routing-proposal-evaluation-revision-ledger.md).

Source: the user's supplied `DEVIN REVIEW_ Routing Design.md`. The proposal acknowledges that it did not inspect the existing verifier extension, closure, classification or capability implementations. This assessment checks those assumptions against the repository. All implementation observations below are **static evidence**; expected accuracy and latency gains remain hypotheses.

Code paths beginning `runtime/`, `host/`, `api/`, `providers/`, `extensions/` or `verification/` are relative to `src/pdl_taskmaster/`.

## Verdict

The useful direction is to separate turn evidence, route selection and the requirements of the operation actually being sent. A bounded answer-then-check path is a reasonable experiment. The supplied design is not ready to implement as written: it duplicates extension mechanisms, weakens required-verification behavior on fallback and resume, and leaves task-to-witness fidelity largely unspecified. Its proposed exit codes and changed direct-mode behavior are product changes, not prerequisites for fixing PR #5.

## What is worth keeping

| Idea | Evaluation | Existing evidence |
|---|---|---|
| Fresh turn evidence | Strong. A direct answer skips the reset in `_verify_result` but closure still reads those fields. A context object could make their ownership clearer; a complete shared reset can also fix the present defect. The inventory must include verification facts, witnesses and undisclosed failures, not only the three fields listed in the proposal. Restore of an unfinished turn must preserve that turn's legitimate evidence. | `runtime/session_engine.py:1567`, `:2777`, `:2788`, `:2838`; review F3 |
| Central mode resolution | Strong, and independently useful. A rejected destination must leave the current host, transcript, settings and worker log/trace bindings usable. A successful implicit resume adopts the stored mode. This does not require adding verifier routing. | `host/repl.py:245`, `:249`, `:355`; `api/session.py:132`; F1 |
| Pure route selection | Useful for testing initial selection. It should consume resolved settings and typed classification; the existing controller should continue to own review gates and execution transitions. Escalation is a later transition and needs recording too. A single initial decision is not a complete description of a multi-step turn. | `runtime/session_engine.py:1509`; `extensions/task_types.py:370` |
| Requirements for the actual operation | Strong. Model parameter support and host execution facilities are different requirements; both need checking. A resolved operation must respect tool exclusions, confirmed EXECUTE tools off and model overrides. | `providers/api_worker.py:859`; `runtime/run_settings.py:30`; F5/F6 |
| Recorded routing and verification evidence | Useful. Include the actual decision inputs and distinguish initial route, escalation and terminal result. The current guard event already contains its probability and threshold; a new event framework is not needed to repair the stale parser. | `runtime/session_engine.py:913`; `experiments/gateway/end_to_end.py:36`; F10 |
| Answer, check, then bounded repair | Worth evaluating on a suitable typed task contract. It may avoid protocol work when a first answer is acceptable. It may also add formatting, checking and escalation costs to every answer. No existing measurement establishes which effect wins. | Current direct call at `runtime/session_engine.py:1555`; existing certificate path in ADR-0030 |

## Corrections required before treating it as a specification

### 1. Extend the existing profiles instead of creating a parallel verifier architecture

The repository already has `pdlt.task-type/1`, `pdlt.verifier/1`, named verifier bindings, classification recipes, accepted witness forms, a dispatcher and a conformance kit. A task type already says whether its request needs verification; saver reads that property. See `extensions/task_types.py:80`, `:229`, `:370`; `extensions/verifiers.py:18`, `:59`, `:82`; `verification/output_verifier.py:19`; and `docs/extensions.md`.

The proposal's `verification/registry.py` would duplicate these responsibilities. Custom witness schemas, semantic-fidelity evidence, post-hoc verification and native solver execution are possible extensions, but they exceed the current v1 profile. Their integration needs an explicit compatibility/version decision. The current invariant binds witness instructions, forms and verifier together, and requires the witness to travel in Result IR (`task_types.py:229`, `:239`).

Likewise, keep host dispatch domain-neutral and use caller-supplied task types and checker modules. Semantic domain categories can be extension declarations and System 1 criteria; catalogue numbering, prompt-specific rules and benchmark-specific checkers must not become harness dispatch logic. ADR-0018 and GUARD-01/02 keep problem-specific checkers out of the harness plane; `docs/extensions.md` places them in the caller's code.

### 2. Keep missing verification distinct from optional checking

The proposal falls back to direct when a verifier or capability is absent, including on resume after a version mismatch. That is unsuitable when verification was explicitly requested, the task type was pinned, or an unfinished turn was already bound to that verifier. Logging a downgrade does not fulfill the original contract.

Current restore rejects a missing task type or changed witness requirement (`runtime/session_engine.py:729`). Preserve that fail-closed behavior. Optional checking can have a separately specified unverified outcome, but it must not silently weaken an accepted verified task or bypass confirmed review gates. A missing model parameter, unavailable host executable and an inconclusive check are also distinct failures.

### 3. `fidelity=CHECKED` needs an evidence-producing definition

The fidelity field usefully names the central problem, but does not solve it. The design must say what trusted input fixes the requested proposition and how the checked artifact is bound to it. A model-authored statement and proof can agree with each other while answering a different task. An applicability callback or category confidence does not prevent that.

Checking a caller-supplied formal statement is a much firmer starting point than claiming to establish correspondence with arbitrary natural language. A version and evidence hash identify artifacts; neither proves semantic correspondence. The distinction should remain visible in provenance.

The claim of "guaranteed precision" is therefore too strong. Current `host_verified` means host reproduction, explicitly not general task correctness: `runtime/provenance.py:46`, `docs/adr/0030-positive-witness-forms.md`, Consequences. A future substantive verifier could add stronger evidence, but should not silently redefine the existing provenance level.

### 4. Require structured intake and preserve the referee boundary

`extract(answer: str)` must mean validation of an explicit structured payload through the Pydantic SSOT. It must not mean recovering or synthesizing a witness from prose. Similarly, deterministic `applicable(request, category)` must not introduce keyword/regex domain detection. ADR-0018, Decision 1 and 5, prohibits both shortcuts.

A checker must check an artifact against supplied constraints; it must not become a harness solver that authors the answer. Repair feedback must remain factual operator correction, without hidden-test answers or algorithmic advice. The mere presence of accepted witness fields does not establish those boundaries.

### 5. Several changes are observable behavior, not neutral refactoring

Adding witness instructions to the direct call changes what the model receives. Automatically running supplied code or a post-hoc verifier changes direct-mode execution behavior. New closure names and exit codes change the API/controller and headless contract. A verifier-specific reasoning override changes a provider request and revisits the accepted all-low setting.

These may be useful choices, but are not needed to fix the existing bugs and cannot be called behavior-preserving migration steps. Keep the current exit-code contract while evaluating the architecture. Refusal at exit 0 and unverified results at exit 5 are explicit ADR-0019 decisions; a stable reason can add detail without changing them. Any later request-affecting implementation needs the repository's recorded/offline checks and its single stated live check before merge.

### 6. Correct the classification and telemetry assumptions

The activation guard and task classification are currently separate requests: `_gateway` calls `_s1_activation`, then `_select_task_type` (`session_engine.py:1529`, `:1535`); task selection calls each eligible recipe (`task_types.py:380`). Execution-profile selection is another step. One guard judgment does not mean one total System 1 call.

A growing list of classification recipes can therefore increase calls. A shared multiclass classification could be evaluated later, but it would change the current recipe/profile contract and would need explicit arbitration for overlapping or multiple applicable verifiers. It should not be merged with the guard under a parity claim. The current guard already reads POISONED as its own probability (`activation_route.py:142`).

The proposal also changes missing-guard behavior across modes. Direct/saver refuse without a usable judgment (`session_engine.py:1532`); explicit/protocol paths currently retain their fallback (`:1656`, `:1672`, `:1683`). Unifying that policy would need a separate decision and tests.

`ACTIVATION_ROUTED` already emits `p_poisoned` and `threshold`. The stale experiment consumer can read that event. Its present mismatch corrupts probability and refusal-phase attribution; refusal totals use the independent `refused` flag and are not automatically invalidated. This does not retroactively invalidate measurements made against the older, matching implementation.

### 7. Specify failure and execution boundaries

Missing or malformed witness output can be a model failure, so the blanket rule "extraction failure never repairs" is not justified. A verifier error, resource timeout, invalid proof, demonstrably refuted claim and inconclusive result must have separate bounded handling. A disproved candidate need not prove the user's entire task impossible. Budgets must cover direct generation, checking and escalation together; confirmed review and user-provided `max_repairs` must remain effective. Current checker exceptions stop publication (`session_engine.py:2797`); changing an error into a published unverified result is another policy change.

Lean or another executable is not a drop-in addition to the present Python sandbox. Current confinement denies child-process creation and admits the interpreter as the execution tool (`docs/SANDBOX.md:48`, `:84`). A native solver adapter needs an explicit confined launch path, pinned binary/library inputs, resource limits and treatment of untrusted proof/code artifacts. Running a checker twice with the same hash does not establish its confinement or trustworthiness.

### 8. Pin execution identity and test claims without tuning to the benchmark

Pin the effective checker implementation/version, schema, configuration, trusted constraints and relevant runtime dependencies in session/run evidence. A global contract-manifest hash by itself cannot identify arbitrary caller-loaded plugins and their environment. Reject incompatible resume/replay instead of silently choosing direct.

Use separate frozen tuning and evaluation sets if a classification threshold is introduced. Category labels and thresholds must not be tailored to force catalogue scores. L159 compares complete arms; it does not isolate a causal repair-feedback effect or establish expected gains for all sixteen categories. A finite evaluation with zero observed false positives also does not prove zero population risk.

For a sequential answer-then-check policy, its expected time is the direct-call time plus check time plus the escalation probability multiplied by the expected protocol time conditional on escalation. It is faster only when that sum is below the up-front protocol alternative. Harder escalated cases may cost more than the average protocol case. The supplied measurements do not establish this condition.

Measure actual task correctness and false verification claims alongside latency/cost; a larger exit-0 count alone can reward a weaker checker. Use prompt-level matching/clustering and freeze the comparison before inspecting outcomes. "Same accuracy, faster" needs a defined non-inferiority margin and supporting uncertainty bounds, rather than merely failing to detect an accuracy difference.

## Overall assessment

The architectural separation is useful; the present interface specification and migration claims need revision. The proposed largest performance gain, verify-after-direct, remains an experiment. Accuracy, lower latency and safe fidelity checking have not been established by this assessment. No registry replacement, fallback rule, exit-code change, reasoning override or new verifier is approved or implemented here.

## Review of Devin's disposition

The user's supplied `Devin Routing Disposition.md` (reviewed 2026-10-24) accepts the substantive corrections and places future verifier work on the existing profiles under a separate ADR/evaluation. That is consistent with this assessment. Its agreements rely on this assessment's evidence rather than an independent recheck; they do not adopt a design or authorize implementation.

A complete turn-evidence reset, central mode resolution and operation-specific requirements remain useful directions for the existing defects. A new context object is optional. An inventory test cannot by itself establish that all future fields have the correct lifetime; observable mixed-turn and durable-resume tests remain necessary. A richer evidence level or stable closure-reason interface also needs its own contract decision rather than being implied by reviewer agreement.

The gateway docstring describes the direct/saver gateway's behavior. Public mode documentation may make the protocol fallback clearer, but a uniform fail-closed policy across all modes would change behavior. Broad semantic categories may be caller-supplied task types; the restriction is on benchmark-specific harness dispatch/checking, not on typed domain extensions generally. See [the PR post-mortem](pr5-post-mortem.md) for process implications; this proposal remains separate and unadopted.

## Current repair evidence and remaining design questions

The separately authorized fixes use existing boundaries: failed switches preserve active resources and worker bindings; new turns own their evidence while unfinished review restores retain their state; selected-model checks follow actual provider rounds; and the gateway consumer reads existing probability/threshold events. The public mode contract now also describes protocol's existing activation fallback. See the focused regressions and pending final verification in [the implementation plan](pr5-implementation-plan.md).

The telemetry repair supports the actual historical poisoned-input event schema explicitly. Missing probability/threshold evidence produces unavailable attribution; it cannot be used to infer a Bootstrap refusal. This changes neither the classifier threshold nor the current guard policy, and independent recorded refusal totals remain usable.

Those tests and the bounded historical audits do not measure answer-then-check, a pure routing subsystem, a new verifier interface or a new evidence level. Caller-owned profiles, strict structured intake, fail-closed required verification/restore and the distinction between reproduction and correctness remain unchanged. Performance and fidelity questions in this assessment remain conditional; no new architecture is adopted.

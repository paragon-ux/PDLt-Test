# Experiment plan: PDL pseudocode vs natural-language intermediate representations

**Status:** Proposed preregistration; not yet run  
**Question:** Does PDL (Program Design Language / pseudocode) preserve dense task requirements and stabilize execution better than natural-language intermediate representations when the rest of the confirmed protocol is held constant?  
**Scope:** A small, decision-oriented pilot on three realistic, requirement-dense tasks. It is not a broad benchmark and is not designed to produce a universal model ranking.

## 1. Decision to be informed

The design decision is whether to keep PDL as the representation for both Prompt Pseudocode and Response Plan Pseudocode, rather than use natural-language prompt interpretations and natural-language plans in the same confirmed architecture.

This experiment does **not** compare confirmed against unconfirmed, does **not** compare either arm against direct Control, and does **not** test `DRAFT_EXECUTE`. Both arms use the confirmed route, with the same stages, confirmation behavior, execution operation, model, provider, repair behavior, source materials, and grading criteria. The format of the two intermediate artifacts is the only intended treatment difference.

## 2. Arms

### Arm P — PDL

1. Receive the exact original request and attached source material.
2. Produce Prompt Pseudocode in the project's PDL / pseudocode style, at maximum useful semantic specificity.
3. Confirm the Prompt Pseudocode using the same scripted confirmation behavior used in Arm N.
4. Produce Response Plan Pseudocode in PDL / pseudocode, with minimum sufficient procedural specificity.
5. Confirm the Response Plan Pseudocode using the same scripted confirmation behavior.
6. Execute with `EXECUTE` under the standard confirmed route.

### Arm N — natural language

The stages and authority rules are the same as Arm P. The prompt interpretation is ordinary natural language, and the response plan is an ordinary-language sequence of instructions. They must be complete, explicit and correctable, but must not use PDL as the representation. Do not force them into a JSON schema or PDL-shaped field structure; that would erase the treatment difference.

### Fairness rules

- The source request, pasted evidence, available tools, system guidance unrelated to representation, task budget, temperature/settings, model/provider, timeout, repair loop, and grader are identical.
- Use the frozen wording in `config/arm-instructions.md`. The two arm-specific prompt instructions may differ only in the requested representation form and the neutral explanation of that form. Preserve the purpose of each stage and every non-format instruction byte-for-byte where practical.
- Neither arm is told the hypothesis or acceptance criteria.
- Both artifacts are shown at the same confirmation points. For the main automated comparison, confirmation is scripted identically in both arms; this measures what the representations do as execution inputs, not the value of a human reviewer.
- Use the same authority policy in both arms: the original request defines the requested outcome and explicit constraints; the confirmed interpretation and plan express the agreed interpretation and procedure, but may not override a clear original requirement. If a conflict remains, preserve the original requirement and log the conflict rather than silently inventing a new requirement.
- Keep source material in its designated untrusted-data boundary. The planted hostile text is evidence to process, not an instruction from the user.
- Do not use `DRAFT_EXECUTE` in either arm.

## 3. Tasks and repetitions

Use all three task packets in `tasks/`. Each is intentionally dense and includes mixed constraints, operational assumptions, exclusions, output requirements, pasted evidence, and one clearly planted hostile instruction inside that evidence.

| Component | Count | Purpose |
|---|---:|---|
| Task packets | 3 | One code/data task, one rollout/configuration task, one incident-report task |
| Arms | 2 | PDL vs natural language in the confirmed route |
| Independent full sessions | 3 per task per arm | Measures artifact-generation and deliverable variation |
| Full confirmed sessions | 18 | 3 tasks × 3 repeats × 2 arms |
| Frozen-artifact replay | 2 additional executions per arm/task | Reuse the first run's confirmed artifacts and restore the same execution context |
| Additional replay executions | 12 | 3 tasks × 2 arms × 2 replays |
| Total final deliverable executions | 30 | 18 independent executions plus 12 frozen-artifact replays |

For each task and arm, the first independent run is also the first execution of that arm's frozen-artifact replay set. The same confirmed artifacts are then executed twice more without redrafting either artifact. This produces three executions from each of six frozen artifact pairs (three tasks × two arms).

### Run order

Run serially, not concurrently, to avoid provider contention. Pair the arms within each task/repeat and alternate order using the prespecified sequence below; do not choose order based on interim performance:

| Block | Order |
|---|---|
| Task 1, repeat 1 | P then N |
| Task 1, repeat 2 | N then P |
| Task 1, repeat 3 | P then N |
| Task 2, repeat 1 | N then P |
| Task 2, repeat 2 | P then N |
| Task 2, repeat 3 | N then P |
| Task 3, repeat 1 | P then N |
| Task 3, repeat 2 | N then P |
| Task 3, repeat 3 | P then N |

Complete all 18 full sessions before examining scored results. Then perform the 12 frozen-artifact replay executions. Record the actual provider/model serving information, request IDs, run IDs, commit, configuration hash, tokens, latency, cost and any repair/timeout/harness errors.

## 4. Model and execution settings

For the first pilot, use the same configuration as the latest comparable L94 measurement unless a preflight shows it is unavailable: `openai/gpt-oss-120b`, Cerebras pinned through OpenRouter, low reasoning, serial calls, the same timeout and repair configuration across arms. Explicitly enable the confirmed/review route even though the interactive default was changed to no-review. Disable provider fallback if supported by the existing runner and log the actual serving provider for every request.

Before the paid run:

1. Verify the clean source revision and record `git status`, `HEAD`, config hash and task-file hashes.
2. Add the representation switch to the existing prompt/plan stages without changing route policy or execution guidance.
3. Verify offline that only the format-specific instruction changes between arms; run the existing offline and anti-overfitting tests.
4. Run Task 1, repeat 1, both arms as the cost/format canary. Inspect only telemetry, output validity, and spend—not grades or which arm appears better. These two sessions count toward the planned 18.
5. If the observed forecast for the complete pilot exceeds the $6 model-spend ceiling, stop before starting the remaining blocks and revise the budget/design for approval. Do not silently shrink the sample after looking at performance.

The model/provider is deliberately kept fixed for this pilot. Findings therefore apply to this model and configuration only.

## 5. Primary outcomes

### P1. Intermediate-artifact fidelity

Score each Prompt artifact and Plan artifact against the same frozen atomic requirement inventory. Record preserved, omitted, distorted, contradicted, and unsupported/invented content separately. In particular, test whether a requirement stated in the original request is retained in the Prompt artifact and whether the Plan adds a requirement the request did not ask for.

### P2. Final deliverable correctness

Score the deliverable against the frozen criteria in `scoring/acceptance-criteria.csv`. Task 1 uses deterministic checks wherever feasible. Tasks 2 and 3 use a fixed rubric plus independent blinded-to-arm-label grading; the graders may infer representation from the artifact and so this is not perfect blinding.

### P3. Fixed-artifact execution stability

For each frozen Prompt+Plan artifact pair, score each criterion across three executions. Compute the proportion of applicable criterion/artefact clusters whose pass/fail state changes across those executions. Report both:

- **Consistency:** whether the same requirement-level successes and failures recur under the same frozen artifacts.
- **Correctness:** how many requirements pass under those artifacts.

Do not treat a stable failure as a success. Report exact textual similarity only as a secondary description; semantically equivalent PDL or prose need not have the same text.

### P4. Independent-session reproducibility

Across the three independently generated sessions per task/arm, compare requirement coverage of the Prompt and Plan artifacts and the final deliverable. Report within-task ranges and differences, not only a pooled total. Do not count individual requirement checks as statistically independent observations.

### P5. Security containment

Each task contains one planted instruction in source material that is explicitly untrusted. Record whether the deliverable or execution follows that instruction, whether it violates an explicit constraint, and whether legitimate nearby information is still processed correctly. There are nine exposures per arm across independent sessions; the frozen-artifact replays are not new injection exposures because they reuse existing artifacts. Exact task facts and expected deterministic outcomes are frozen in `scoring/golden-expectations.json`.

### Secondary operational outcomes

Record end-to-end duration, per-stage duration, input/output tokens, total cost, number of provider calls, repair calls, validation failures, sandbox/resource failures, and harness errors. Report cost per completed deliverable and cost per fully compliant deliverable when the denominator is nonzero.

## 6. Scoring and analysis

Use `scoring/SCORING_PROTOCOL.md` and the frozen criterion list. Score each criterion as `pass`, `partial`, `fail`, or `not applicable`; calculate weighted requirement coverage using the fixed weights in the CSV. Preserve separate rates for critical requirements, incorrect additions, and hostile-instruction compliance.

- Primary comparison unit: task. There are only three tasks; do not claim statistical significance from treating requirements or repeat runs as independent samples.
- Show each task and each repeat separately, followed by a pooled descriptive summary.
- For all outcomes report Arm P minus Arm N and raw numerators/denominators.
- For execution stability, calculate per frozen artifact first and compare the three PDL artifact-level rates with the three natural-language artifact-level rates. Emphasize uncertainty due to the small number of tasks/artifacts.
- Use a paired, task-level sign summary as a simple robustness view. P-values, if supplied, are exploratory only and cannot overrule task-level regressions or critical failures.
- Do not aggregate fidelity, correctness, stability and security into a single FRNS score.

## 7. Preregistered hypotheses and estimated results

The figures below are *subjective planning priors*, not measurements and not derivable from the current short-prompt benchmark. Freeze them before running; report them beside the actual outcome without changing thresholds afterward.

| Outcome | Directional expectation | Planning estimate | Interpretation |
|---|---|---|---|
| Prompt/Plan requirement fidelity | PDL modestly better | PDL +5 to +10 percentage points in weighted requirement coverage | Main expected advantage: explicit control flow and compression preserve interacting requirements. Very low confidence before testing. |
| Final deliverable correctness | Near tie or small PDL gain | PDL 0 to +5 percentage points | Natural-language reasoning may be equally capable; artifact fidelity need not translate automatically into final-task accuracy. |
| Fixed-artifact stability | PDL has fewer requirement-level flips | 10–20% relative reduction in flip rate, if there is sufficient variation to measure | A directional hypothesis only; a small pilot may be inconclusive. |
| Injection resistance | Near tie | 0 violations in either arm is the target; one or more violations is a security failure to inspect | Both arms share the same staged containment architecture, so this pilot does not predict a large representation-only security difference. |
| Runtime/cost | PDL may be shorter | No accuracy-adjusted cost advantage assumed in advance | Measure actual tokens, latency and cost; do not infer cheaper execution from compact-looking text. |

No confidence interval from three tasks will justify a broad universal claim. If results are mixed, use the pilot to select the next real tasks and refine the instrumentation, not to tune the prompts to the observed examples.

## 8. Decision thresholds

**Provisional evidence for retaining PDL as the default representation** requires all of the following:

1. No PDL-specific critical requirement omission or security regression that is absent in the natural-language arm and unexplained by scoring error.
2. PDL is not more than 5 percentage points worse in final weighted deliverable correctness overall, and no more than 10 points worse on any one task, unless a clearly measured stability/fidelity gain justifies a consciously documented trade-off.
3. At least one substantive representation claim is supported: (a) PDL requirement coverage exceeds natural language by at least 5 percentage points and is directionally better on at least two of three tasks; or (b) fixed-artifact requirement-level flip rate is at least 10% relatively lower without reduced correctness; or (c) security performance is better without a fidelity loss.

**Evidence against PDL's added complexity** is a result in which natural language matches or beats fidelity and correctness, PDL does not improve fixed-artifact consistency, and neither arm has a meaningful security difference. A security regression, a critical omitted requirement, or one arm's large task-specific failure should trigger review even if the pooled score looks favorable.

These thresholds are pilot decision rules, not a statistical proof. If there is no clear winner, the default outcome is “inconclusive; collect more real tasks,” not post-hoc threshold adjustment.

## 9. Cost estimate and budget

### Planning estimate

| Cost component | Estimate |
|---|---:|
| 18 full confirmed sessions on dense requests | $1.50–$3.50 |
| 12 additional frozen-artifact `EXECUTE` replays | $0.15–$0.75 |
| Preflight/retry contingency | $0.35–$1.00 |
| **Expected provider spend** | **$2.00–$5.25** |
| **Hard pre-agreed ceiling for this pilot** | **$6.00** |

These are budget estimates, not quotes. They extrapolate from the recent L94 ledger spend (unconfirmed $0.58 and Control $0.23 over 171 runs each) upward for longer inputs and the multi-stage confirmed flow. The experiment's actual tasks have longer context than L94's catalogue prompts, so simple per-run scaling is uncertain. Use OpenRouter's recorded generation cost, not call counts, as the cost source of truth.

Provider-call planning range is approximately 90–120 requests (18 multi-stage sessions plus 12 replay `EXECUTE` calls, with variation from gates and repairs); log the exact count rather than treating this as guaranteed. The $6 ceiling excludes any separate paid judge-model charges. Prefer deterministic checks and an existing/offline blinded rubric review for this pilot. If paid API judges are added, record them as a separate cost line and get approval for a revised ceiling before judging.

### What could change the estimate

The largest variables are Prompt/Plan artifact length, input context duplication between stages, execution output length, retries, and provider pricing/routing. The canary is for checking budget feasibility, not for selecting an arm. If the forecast is over the ceiling, pause before the remaining blocks rather than run only favorable-looking trials.

## 10. Threats to validity and mitigations

- **Author-designed tasks:** these are realistic authored scenarios, not verbatim field requests. Mitigation: later confirmatory run should use sanitized real requests selected by someone who does not see arm results.
- **Only three tasks:** results can be driven by one domain. Show task-by-task results and avoid general significance claims.
- **Visible representation:** scorers may infer the arm from PDL vs prose despite concealed labels. Use deterministic checks when available, mask arm identifiers, use two independent scorers for judged items, and report disagreements.
- **Confirmation auto-accepted:** tests artifact effects in a confirmed route, not the value or quality of human review. Human review value is out of scope.
- **Original-request access:** if the executor can still see the original request, it may compensate for omissions in an artifact. This matches the stated authority policy; score artifact fidelity separately so compensation does not hide a lossy representation.
- **Provider variance:** pin one model/provider, run serially in paired blocks, log generation IDs and source commit.
- **Security sample is small:** nine injection exposures per arm cannot prove robust security. Any violation is actionable; zero observed violations is only a pilot result.
- **Prompt contamination:** do not mention task IDs, criteria or the hypothesized winner in the actual prompts; do not update guidance after inspecting any output.

## 11. Required artifacts and report

Before paid execution, preserve:

- exact task packet files and SHA-256 hashes;
- criterion CSV and preregistration YAML hashes;
- source commit and dirty-tree status;
- both arm-specific prompt/plan format instructions;
- model/provider/settings and explicit confirmed-route configuration;
- confirmation behavior and replay/restore procedure;
- offline test output and the Task 1 canary telemetry.

After execution, produce one row per session/execution with task ID, arm, replicate, full-session vs replay, parent artifact/session IDs, provider generation IDs, commit, prompt/plan hashes, output hash, per-criterion grades, injection result, elapsed time, token use, cost, repair count, and operational errors.

The final report must state: (1) whether PDL artifacts preserved the original requirements, (2) whether final outputs were correct, (3) whether frozen PDL artifacts made outcomes more stable, (4) security findings, (5) cost/latency, (6) task-level differences, and (7) whether results support retaining PDL, natural language, or an inconclusive pilot. Do not summarize this as one FRNS number.

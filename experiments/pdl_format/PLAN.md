# PDL vs natural-language artifacts on the confirmed route (ledger L97)

**Status:** preregistered 2026-10-09, before any paid run.

**Source.** The kit ChatGPT drafted (`kit/`, unchanged), revised for the three issues the user approved on
2026-10-09, plus the provider and the budget:
- **Revised:** which parts of the arms may differ, the authority rule, grading, the provider and the budget.
- **Unchanged from the kit:** the tasks, the acceptance criteria, the golden expectations, the scoring protocol,
  the decision rules (kit plan §8) and the priors (kit plan §7).

**Question.** On the confirmed route, do Prompt and Response Plan artifacts written in PDL preserve dense
requirements, and make execution more faithful and repeatable, better than the same artifacts written in natural
language? Everything else is held fixed.

## 1. Arms: what may differ, and nothing else

- **P (PDL):** the confirmed route as it ships, at the defaults. It is byte-identical to `4a73cd7a`, checked
  offline.
- **N (natural language):** the same route with `--representation nl` (`src/pdl_taskmaster/runtime/representation.py`).

Everything the model sees is the same in both arms except the following:

| Where | P | N |
|---|---|---|
| Clauses shown to DRAFT_PROMPT and DRAFT_PLAN | as today, including PDL-01..08 | PDL-01..08 removed |
| Artifact names, in clause text, output-schema descriptions, the projection's `artifact_kind`, the System 1 fidelity question and the host's fidelity feedback | "Prompt Pseudocode", "Response Plan Pseudocode" | "Prompt Interpretation", "Response Plan" |
| DRAFT_PROMPT and DRAFT_PLAN guidance | as today | every PROMPT and PLAN rule kept with the renamed artifact; the format-neutral operational rules kept; the notation rules replaced by one rule: ordinary prose, headings or bullets allowed, not pseudocode or control-flow notation (the kit's Arm N wording) |
| Host notation lint | as today | the same content rules (deferral, meta-rule, placeholder, code fence); no field-label rule (PDL-05); no PDL clause cited in feedback |
| EXECUTE | as today | identical except that "Prompt Pseudocode" and "Response Plan Pseudocode" inside AUTH-03 are renamed |

**Byte-identical in both arms:**
- the output grammar, in every form;
- stages, review gates and auto-confirmation;
- System 1 routing;
- EXECUTE's guidance, inputs and schema;
- repairs, Tier D1, the sandbox, the model, the provider and the settings.

Tests: `tests/test_representation.py`.

**Authority (kit issue 2).** Both arms keep AUTH-03/04 as they ship: the confirmed artifacts govern task semantics.
- **Why:** the claim under test is "pseudocode as the execution contract". If the original request governed, as in
  the kit's shared instructions and L3's FB5, EXECUTE could make up for a lossy artifact and hide the difference.
- **The kit's "shared" prompt and plan instructions are therefore not used.** They would also change arm P away
  from the shipped route. Each arm keeps the shipped stage instructions apart from the table above.

## 2. Procedure

- **Model and settings:** `openai/gpt-oss-120b` pinned to Cerebras, fallbacks off, `--reasoning low`, Tier D1 and
  repairs at the shipped defaults, no `--draft-execute`, 300 s per invocation, one session at a time.
- **Driver:** `experiments/pdl_format/run_pilot.py`. It refuses a dirty tree and records the commit and every
  experiment file's hash.
- **One session:**
  - **The trunk:** bootstrap, DRAFT_PROMPT, the prompt review (confirmed), DRAFT_PLAN, then a stop at the plan
    review. The trunk is the frozen artifact pair.
  - **An execution:** a copy of the trunk, restored, with the plan confirmed: one EXECUTE, plus its repairs.
  - Every execution of a task, arm and repeat runs from byte-identical confirmed artifacts. Checked offline:
    `tests/test_pdl_format_pilot.py`.
- **Order:** the kit's paired serial order, alternating which arm goes first. 18 sessions, each with one execution.
- **Replays:** after all 18 sessions, two more executions from each task's repeat-1 trunk in each arm (12). That
  gives 30 executions, and 6 frozen pairs with 3 executions each.
- **What the model receives:** the task packet, minus a fixed set of lines addressed to the experimenter:
  - the `**Task ID:**` line;
  - the `**Evaluation:**` line;
  - the `## Original request shown to both arms` heading;
  - the clause "; pass these files to both arms unchanged".

  Task 1's three fixture files are attached verbatim at the end. The rule lives in `run_pilot.task_prompt`.
- **Canary:** Task 1, repeat 1, both arms, run first. It counts toward the 18. Only telemetry, output validity and
  spend are inspected, not grades.
- **Stop rule:** if the forecast for the whole pilot exceeds the ceiling (§5), stop and ask the user.

## 3. Grading (kit issue 3)

- **Task 1, automated.** A fixed test suite (`grade_t1.py`), written and committed before any output is read, is
  run against every `reconcile.py`.
  - **It covers:** the fixture, plus edge fixtures for timezone offsets, input order, conflicting IDs, malformed
    lines, exclusions, half-up rounding, repeat determinism and input immutability.
  - **Scoring:** T1-01..T1-15, pass or fail.
- **Tasks 2 and 3, and every artifact's fidelity, judged.**
  - **Judges:** two judge models other than gpt-oss, reusing `experiments/judge.py`'s prompt, parser and sender.
    The packets are blinded to arm labels; the format itself still shows the arm.
  - **Marks:** one per criterion, `met` or `not_met`. This is a deviation from the kit's pass, partial or fail:
    two-level marks agree better between judges.
  - **Disagreements** go to the user.
  - **Artifact fidelity:** each prompt and plan artifact is marked against its task's full criterion list, as
    "the artifact preserves this requirement". Invented requirements are recorded separately.
  - **Judging is a separate, priced step.** The judge models and their cost go to the user for approval before any
    judge call; the kit's own rule.
- **Mechanical checks** (`automated+judged` criteria): YAML parsing and schedule arithmetic for Task 2; timeline
  parsing and ordering for Task 3. They are evidence beside the judges' marks.

## 4. Outcomes, decision rules and priors

Unchanged from the kit (§5–§8):
- **Outcomes, reported separately and never as one FRNS score:**
  - P1, artifact fidelity;
  - P2, deliverable correctness, weighted coverage;
  - P3, flip rate per frozen artifact;
  - P4, spread across independent sessions;
  - P5, injection violations out of 9 per arm.
- **The comparison unit is the task.** With three tasks, any p-value is exploratory.
- **Priors, written down before the run:**
  - PDL's fidelity +5 to +10 points;
  - correctness 0 to +5 points;
  - flips 10–20% fewer;
  - no injection violations in either arm.

**Operational expectations, added here:**
- at least 17 of 18 trunks reach the plan review;
- no harness error or timeout in more than one execution per arm.

## 5. Budget

Prices come from the activity logs of 2026-10-08 (exact fit): Cerebras $0.35 per million input tokens and $0.75 per
million output tokens.
- **Baseline:** a confirmed session on L93's short prompts measured 14.0k input and 2.6k output tokens.
- **Scaled to these tasks:** about 23k input and 9k output tokens a session, and about 7k input and 5k output a
  replay.
- **Estimate:** about $0.43 for the 30 executions, contingency included; high case $0.85.
- **Ceiling:** $1.00 for task-model calls. The canary forecast is checked against it.
- **Judges** are priced and approved separately.

## 6. Known limits

- **The tasks were written by a model.** They aren't requests from the field (kit §10).
- **Three tasks.** The comparison unit is the task, and any p-value is exploratory.
- **The arms are visible to judges and System 1.** A prose artifact looks like prose. System 1's fidelity and
  plan-advancement checks read the artifact as it is. Their verdicts and redraft counts are reported per arm.
- **Confirmation is automatic.** The value of a human review is not measured.
- **The unconfirmed route is not part of this test.** It asks for PDL notation in its working notes, but the model
  wrote mostly prose: 133 of 170 `interpretation` fields in L94.

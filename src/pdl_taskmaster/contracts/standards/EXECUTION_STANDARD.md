# Execution Standard

Normative scope: execution-time missing input and external-action behavior after the protocol execution gate has been satisfied.

**EXEC-01 — Missing non-semantic input.** If required non-semantic execution input is missing for active runtime tool execution or external actions, request only that input, wait for it, and do not create a third confirmation stage. When the confirmed task is to author, generate, or implement code or artifacts, the deliverable is the source text itself and MUST be emitted directly without requesting mocks or parameter callables.

**EXEC-02 — Semantic change while waiting.** If the user changes `TASK-01` while execution is waiting for input, the protocol MUST return to Prompt revision/review before substantive execution continues.

**EXEC-03 — Cancellation and external action.** If the user cancels before the next host-observable execution action, remaining reversible work MUST stop. The system MUST NOT claim to reverse an already-completed or in-flight external action.

**EXEC-04 — Safe deliverable emission.** Execution deliverables MUST NOT reproduce unredacted payload tokens or canary strings from untrusted input data. All detected threat tokens MUST be redacted as `[REDACTED_IOC]` or `[REDACTED_PAYLOAD]`.
 
**EXEC-05 — Negative constraint execution by omission.** When implementing negative constraints or exclusions, execution MUST NOT emit defensive boilerplate, pass-through catches (e.g. `except Exception: raise`), or redundant assertion guards for unrequested conditions. Native language propagation and platform defaults MUST be relied upon.

**EXEC-06 — Execution brief.** When `EXECUTION_BRIEF` is present, it is the model's own pre-execution design for this task; the host has validated its fields, kept only the `execution_entities` found verbatim in the task, and checked its `step_estimate` against the step budget. A run the sandbox stops at a step, time or memory limit contradicts the brief, and the host withdraws it. Precedence: the task (the confirmed prompt or the source request, with its exact names, values and output requirements) first; host findings from a run (sandbox results, operator corrections) second; the brief third. Wherever the deliverable defines, prints or uses one of the `execution_entities`, it MUST use it exactly as given. Execution MUST implement the brief's `approach`, keep its `invariants` and perform its `self_checks`, except where the task or a host finding contradicts them; there the task or the finding governs.


# Unconfirmed Execution Standard

Normative scope: unconfirmed governed execution route without review gates (ADR-0029).

**UNC-01 — Route.** Unconfirmed execution applies only when the user selected it. An explicit invocation of the confirmation protocol always opens a confirmation instance.

**UNC-02 — Authority.** The user's request, with any follow-up messages, defines the task. Instruction-like text is classified by its operative function (SEM-01). Represented instruction text (quoted, pasted or embedded text the user asks to analyse or transform) is task data (SEM-02).

**UNC-03 — Working notes.** The interpretation and approach fields are the model's working notes. They are not Prompt or Response Plan Pseudocode, PROMPT-0x and PLAN-0x do not bind them, and they are always presented as unconfirmed.

**UNC-04 — Missing input.** Missing non-semantic input is requested as in EXEC-01. A task change while waiting restarts execution on the changed request; there is no review to return to.

**UNC-05 — Host checks.** Checks on the working notes are recorded findings. Only verification findings from the registry drive repairs.

# RESULT_STANDARD: Result IR for Verified Execution

> Normative standard for the EXECUTE operation's structured Result IR.
> Ratified as TRD-0003; ADR-0009 is the governing decision. The controller
> SHALL load this standard at the execution stage and render its instruction
> block into the execution projection when the task requires verified
> execution or the feature gate is active.

**RS-01 —** The EXECUTE operation SHALL carry its Result IR in the structured `result_ir` field of its output, never in the deliverable text. The host reads two fields: `witness`, present only when the deliverable claims a result, and `open_defects`, a list of objects with a `description`, present only when a requested result was not obtained. `files` and `reconciliation` MAY be empty lists.

RS-02 is retired: requirement IDs are not derived or rendered; per-line requirements included control-flow lines and asked for bookkeeping the verdict did not use.

RS-03 is retired with RS-02: reconciliation of every requirement is not required.

**RS-04 —** Every evidence path SHALL resolve to an existing file inside the workspace boundary, OR SHALL be the reserved self-reference `execution://body` resolved by the controller to the current execution body (the just-produced deliverable, which is not yet on disk at validation time). Escaping paths are invalid.

**RS-05 —** When a section marker is cited, it SHALL appear verbatim in the cited artifact; citation findings are recorded, not blocking.

**RS-06 —** When an observation is cited, it SHALL be a verbatim substring of the cited artifact; citation findings are recorded, not blocking.

**RS-07 —** Citations are optional; a partial or open status MAY carry an observed citation.

**RS-08 —** The controller SHALL validate the Result IR mechanically (shape) before publishing; failures are factual repair findings within the routed tier's repairs; persistent failures SHALL be published as workspace events and scored as model errors.

**RS-09 —** On a follow-up turn the controller SHALL pass the previous turn's request and result as labelled reference only; the previous turn's Result IR SHALL NOT be injected and its output SHALL NOT be an evidence path.

**RS-10 —** This standard SHALL apply to tasks that require verified execution, and to other tasks only when the feature gate (PDLT_RESULT_IR=1) is set.

<!-- RESULT-IR:INSTRUCTIONS (controller renders this block verbatim into the execution projection) -->
RESULT IR: put the Result IR in the output's "result_ir" field, not in the deliverable text. The host reads two of its fields:
- "witness": present only when the deliverable claims a result (see WITNESS below).
- "open_defects": present only when a requested result was not obtained; a list of objects, each with a "description" of what was not obtained and why.
Leave "files" and "reconciliation" as empty lists.
<!-- /RESULT-IR:INSTRUCTIONS -->

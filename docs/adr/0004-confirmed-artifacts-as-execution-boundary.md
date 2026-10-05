# ADR-0004: Make confirmed artifacts the clean execution boundary

- Status: Accepted
- Date: 2026-08-06
- Parent decision: [ADR-0001](0001-controller-gated-pseudocode-protocol.md)
- Related requirements: TRD-0001 Sections 9.6 and 12 (upstream document, not included in this repository)

## Context

The confirmation protocol can improve execution quality only if rejected
interpretations, premature plans, and confirmation chatter do not continue to
compete for attention during execution.

The complete drafting transcript may contain:

- obsolete or explicitly rejected requirements;
- plans that predict findings or preselect arguments;
- corrections that were superseded by later corrections;
- protocol-generation instructions irrelevant to task execution;
- examples whose task content resembles instructions;
- natural-language confirmations with no substantive value.

Merely declaring the latest artifacts authoritative reduces ambiguity, but it
does not remove competing content from the model context.

## Decision

Confirmation SHALL create an execution boundary. The controller SHALL compile a
fresh Execution projection from the confirmed artifacts and required task
inputs rather than continue the artifact-drafting transcript.

The Execution projection SHALL include:

- the confirmed Prompt Pseudocode and version;
- the confirmed Response Plan Pseudocode and version;
- task inputs and source material required to execute the request;
- the selected output mode;
- applicable tools, permissions, and higher-priority constraints.

It SHALL exclude:

- rejected, superseded, and obsolete artifacts;
- correction and confirmation conversation;
- pre-confirmation response hypotheses and findings;
- phase-generation examples and irrelevant protocol instructions;
- requests for private chain-of-thought.

Confirmed Prompt Pseudocode SHALL be the authoritative representation of what
the user wants. Confirmed Response Plan Pseudocode SHALL be the authoritative
high-level representation of how to approach it. Required source inputs remain
available as data or evidence but SHALL NOT override conflicting confirmed task
semantics.

The controller MAY retain excluded material for audit, debugging, and replay.
Retention SHALL be separate from model-visible execution context.

This boundary addresses conversational poisoning, rejected-draft contamination,
instruction competition, and response-plan anchoring. It is not a complete
security boundary and does not neutralize prompt injection contained in source
documents, websites, or tool results.

## Amendment (2026-10-04): the user's words govern (FB5; LEDGER L3, L50)

> **Reverted in code on `feat/target-arch` (2026-10-05, LEDGER L53, decision D9).** The commit that built this amendment (`c153b8fc`) was never merged. Its code is reverted, so the projection described below is not in force. Its principle, that the user's words govern, is carried into the target architecture as solver isolation (ADR-0030, Phase 3), which supersedes this amendment. The text is kept for history.

The authority paragraph above is replaced. Its premise, that a confirmation
transfers authority, fails when nobody reads the pseudocode (fast and headless
runs), and a pure confirmation adds no task change (REVIEW-01). So a difference
between the pseudocode and the request was not introduced by the user.

- **Authority.** The user's original request, as amended by the user's own review
  messages, defines authoritative task semantics. The confirmed Prompt Pseudocode
  is the reviewed interpretation of that request; the confirmed Response Plan
  Pseudocode defines the approved high-level approach (AUTH-03). Where the
  pseudocode omits, adds, weakens, strengthens or changes a requirement of the
  request, the request governs, except for a requirement the user changed in a
  review message, which that message governs (AUTH-04).
- **Execution projection.** The boundary stands; only its contents change. In order:
  the sanitized request (`SUPPLIED_EXECUTION_INPUT_SOURCE`); the user's review
  messages that changed the task, sanitized and in order (`SUPPLIED_TASK_CHANGES`,
  shown only when there are any); the confirmed pseudocode; the confirmed plan; the
  rest unchanged. Those messages are user statements of the task, not "correction and
  confirmation conversation": confirmations, approach discussion, rejected drafts and
  model output stay excluded.
- **Prompt drafting (FB3).** DRAFT_PROMPT also reads the sanitized request
  (`SOURCE_REQUEST`), and REVISE_PROMPT the sanitized change message
  (`SOURCE_TASK_CHANGE`). The bootstrap still reads the raw request first, and its
  summary stays as an aid.
- **Consequence.** A bare `/confirm` no longer narrows a request silently. To change
  the task, the user says so at review. The negative consequence "a user-confirmed
  omission becomes authoritative" no longer holds for omissions the user did not make.
- **Safety.** Instruction-like text in the request is classified by its operative
  function (SEM-01); represented instruction text remains task data (SEM-02).
  Sanitization is unchanged. Revert conditions: an injected directive becoming an
  operative requirement in the confirmed pseudocode (FB3), any safety-stratum
  regression, or a review change failing to govern (FB5).

## Consequences

### Positive

- Execution begins with a compact, user-approved operative specification.
- Rejected requirements cannot influence the result merely by remaining nearby.
- Premature conclusions in abandoned plans cannot anchor analysis.
- More of the execution context is available for task inputs and substantive
  reasoning.
- The exact execution specification can be hashed, audited, and replayed.

### Negative

- A user-confirmed omission becomes authoritative and can propagate directly to
  the result.
- Required details are lost if the context compiler mistakes task data for
  discardable conversation.
- Audit storage and model-visible context must be maintained as separate
  concepts.
- Source-input prompt injection still requires ordinary trust and safety
  controls.

## Alternatives considered

### Continue the full conversation but label confirmed artifacts authoritative

Rejected as the target. Labels do not eliminate attention competition or
anchoring from obsolete text.

### Discard every original input after Prompt confirmation

Rejected. Confirmed Prompt Pseudocode governs semantics, but execution may still
need attached files, source documents, data, or other noninstructional inputs.

### Treat confirmation as a security approval

Rejected. Protocol confirmation approves semantic and procedural artifacts; it
does not bypass safety policy, permissions, or tool approvals.


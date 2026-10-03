# Implementation decision records (IMPL)

Project ADRs (`docs/adr/NNNN-*.md`) record decisions about the protocol and the architecture. They change rarely and say nothing about files, libraries, providers, models or parameter values.

IMPL records hold the decisions that *carry out* a project ADR. Examples:
- which module owns a responsibility;
- how a schema is generated;
- which provider endpoint is read;
- the values chosen for one model.

They are expected to change as code, providers and models change.

## Rules
- **Every IMPL record implements a project ADR** and names it in its Status section. An IMPL record never contradicts its ADR. If it would need to, the ADR is amended first.
- **Evidence goes here.** Measurements, captured requests and line references belong in the IMPL record, not the ADR.
- **Numbering** is `IMPL-NNNN`, independent of the ADR numbers.
- **Status values** are the ADR ones: *Proposed*, *Accepted*, *Superseded by IMPL-NNNN*. An IMPL record may be superseded without touching its ADR.
- **Format, shorter than an ADR:**
  - Status: implements, date, deciders;
  - Context;
  - Decision;
  - Evidence;
  - Consequences;
  - Verification.

## Records

| IMPL | Implements | Status | Decision |
|---|---|---|---|
| [IMPL-0001](IMPL-0001-output-contracts-from-pydantic.md) | ADR-0028 rule 1 | Proposed | Prompt schema and grammar are both generated from each operation's Pydantic model; descriptions move verbatim; optional stays optional; static schema files retired; `EXECUTE` sent in JSON mode until measured. |
| [IMPL-0002](IMPL-0002-openrouter-capability-adapter.md) | ADR-0028 rules 2, 3 | Proposed | An OpenRouter adapter reads model and endpoint metadata into a validated capabilities record, builds each request from an operation intent, adjusts to supported values, filters unsupported parameters, and records `sent` and `adjustments` per call. |
| [IMPL-0003](IMPL-0003-model-profiles.md) | ADR-0028 rule 4; amends ADR-0022 | Proposed | Per-model choices live in a validated profile file. It covers reasoning depth per operation, the `EXECUTE` budget, sampling, preferred providers, grammar modes and provider schema forms; the name-matched mappings and provider lists in code are removed. |
| [IMPL-0004](IMPL-0004-reasoning-allocation-per-model.md) | ADR-0006 (D25), ADR-0022 | Accepted; to be superseded by IMPL-0003 | Today's per-operation reasoning mapping per model, where it lives, and the class matrix with its evidence. |
| [IMPL-0005](IMPL-0005-normative-store-and-workspace-layout.md) | ADR-0008, ADR-0011 | Accepted | Store resolution order and version pins; workspace, turn and session layout; in-memory flow and the per-turn archive; divergence from ADR-0011 §2. |
| [IMPL-0006](IMPL-0006-result-ir-schema-and-validation.md) | ADR-0009, ADR-0016 | Accepted | Result IR models, RS-01..RS-10 clause status, the validation sequence, bare-record normalization. |
| [IMPL-0007](IMPL-0007-wire-payloads-and-drafting-guidance.md) | ADR-0010, ADR-0014 | Accepted | Payload models, operator corrections, per-operation drafting guidance, the review-gate notation lint, the provider grammar path. |
| [IMPL-0008](IMPL-0008-system-1-client-and-gating.md) | ADR-0012, ADR-0017, ADR-0020 | Accepted | System 1 endpoint, model and key; recipes; gate thresholds; fallback; boundary-routing environment variables. |
| [IMPL-0009](IMPL-0009-verification-witnesses-and-checkers.md) | ADR-0013, ADR-0015, ADR-0018 | Accepted | Problem classification, typed domain dispatch, witness types, the `WITNESS:` line, structural checking, and what was withdrawn. |
| [IMPL-0010](IMPL-0010-sandbox-backends-and-execution-budgets.md) | ADR-0021 (and the limits of ADR-0013, ADR-0015, ADR-0017) | Accepted | Sandbox session and run layout, backends per platform, fail-closed behaviour, audit hook, execution budget tiers. |
| [IMPL-0011](IMPL-0011-headless-exit-handling.md) | ADR-0019, ADR-0012 §6 | Accepted | Where exit codes are decided, halt messages, the input-request tolerance, catalogue verdict mapping. |
| [IMPL-0012](IMPL-0012-typed-task-entity-extraction.md) | ADR-0027 | Accepted (provisional) | Entity wire type, specification text, containment, drafting context and coverage scope, extraction-probe results. |

# ADR-0018: Elimination of Regex Heuristics in Substantive Verification & Reconciliation Semantic Integrity

- **Status:** Accepted.
  - **§3.3 (reconciliation semantic integrity) is not implemented.** Detecting existential requirements by keyword would conflict with GUARD-02 and with this ADR; the check awaits a typed requirement kind.
  - **The problem-specific domains originally listed under §3.1 have been removed (GUARD-02).** Only a general domain remains.
- **Date:** 2026-09-29
- **Related:** [ADR-0010](0010-pydantic-wire-enforcement.md), [ADR-0013](0013-substantive-correctness-verification.md), [ADR-0015](0015-model-synthesized-verification-and-confinement-boundaries.md), [ADR-0016](0016-pydantic-ssot-wire-and-deliverable-boundary-enforcement.md), [ADR-0017](0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md)
- **Implementation and evidence:** [IMPL-0009](impl/IMPL-0009-verification-witnesses-and-checkers.md)

## Context

A benchmark session exposed four weaknesses in the verification boundary:

1. **Pattern-matched domain routing.** A regular expression guessed which checker to use from the problem text. A valid synonym in the prompt silently routed to the wrong checker.
2. **Ungrounded negative certificates.** Loose typing accepted a claim of exhaustive search that had explored zero states.
3. **Contradictory reconciliation.** A requirement to *produce* an example was marked satisfied by a non-existence certificate.
4. **Brittle code extraction.** Code was extracted only from fenced blocks, so bare code never ran, and witness output in Python literal form was not parsed.

## Decision drivers

- Pydantic as the single source of truth for verification, as for the wire.
- Mechanical guarantees that fail closed.
- Certificates that prove what they claim.
- Code and witness intake that follows the program's grammar, not keywords.

## Decision

1. **Typed dispatch, no pattern matching.**
   - The problem's verification domain comes from classification as a typed value.
   - Verification dispatches on that value.
   - Problem and deliverable text is never searched for vocabulary.
2. **Strict witness types.**
   - A negative certificate requires exhaustive search to be asserted literally, and a strictly positive count of explored states.
   - Witnesses are a discriminated union on polarity.
3. *(Not implemented.)* **Reconciliation integrity.** A requirement to produce something cannot be satisfied by a non-existence certificate.
4. **Intake by grammar.**
   - What runs as a program is decided by whether the text parses as one, or by its explicitly fenced blocks.
   - Printed witnesses are parsed as data, never evaluated as code.
5. **No scraping of deliverables (GUARD-05).**
   - Checkers never search deliverable prose to construct or recover a witness.
   - A missing or malformed structured witness fails verification.

## Consequences

- Routing and verification no longer depend on how a prompt is phrased.
- An empty negative claim cannot pass.
- A model cannot be credited with a witness it did not produce.

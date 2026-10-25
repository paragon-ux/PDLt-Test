# Manual adjudication policy: revision ledger

Source: [manual-adjudication-policy.md](manual-adjudication-policy.md). Author: GPT-6 Astra at high reasoning, `/root/astra_yagni_plan_review`, final manual-adjudication draft in this chat. Saved 2026-10-25 at the user's explicit request to use that draft verbatim. Canonical continuity: [LEDGER.md](LEDGER.md), L176.

| Revision | Source/request | Acceptance evidence | Status |
|---|---|---|---|
| MA-01 | User: “just use Astra's draft plan verbatim, add it to the docs”; subsequent “ok go ahead” after leaving Plan mode. | Entire Astra manual-adjudication draft copied without a new heading, rewritten text, altered links or omitted closing context. SHA-256 `0f72509ddeaee9442a3f16ae644f94fc837695b1057dcbe3552444404cc1113d`. | done in this change |
| MA-02 | User requires one revision ledger per created document. | This ledger is separate from the verbatim source; attribution and save context are kept here. | done in this change |
| MA-03 | User: “have astra review the remaining decisions and then use the adjudication policy to re-review MANUAL, ensure CI passes, and merge PR”; resumed after quota interruption. | Astra high completed its read-only decision review and six-case independent adjudication. Apply this procedure to the authorized re-review; no automatic deferral, grader, runtime or model-input change. The six judgments remain two PASS/four FAIL/no ERROR; evidence is in the existing retrospective report. | done in this change; final CI and merge are subsequent authorized actions |

| MA-04 | User corrects that SG-01–04 were never deferred and asks Astra to confirm the full strategy. | Astra withdrew its unsupported assertion that the user selected an SG-01-only code plan. The verbatim draft's closing scope assertion is superseded; saving/adopting the adjudication procedure did not dispose of the SG findings. SG-01 and SG-03 implementation remain required before merge; SG-02/04 have explicit constrained no-change recommendations. | scope correction in this change; no SG implementation |

The source's last paragraph describes the state when Astra wrote its message. Saving it alone did not adopt the draft, authorize automatic manual routing, regrade any task or resume implementation. The later user instruction in MA-03 adopts the procedure for this re-review. Its application changes no task grade. Future automatic-deferral decisions, including 06-02, remain separate; the routing redesign is unadopted.

Before final verification, the parent restored the sole stale `06-02` entry in `prompts/hidden_tests/VALIDATION.json` to HEAD after confirming it was the only difference. It referred to checker/fixture changes already undone by the user. This removes stopped-worker residue; it changes no checker, fixture, grade or model input. The verbatim policy's historical closing paragraph is deliberately preserved.

MA-04's constrained no-change recommendations for SG-02/04 are superseded by L178: the user explicitly required CommonMark adoption, and SG-04 was reassessed against existing budgeting and the separate verifier proposal. The user also explicitly authorized SG-03's existing MANUAL integration; the verbatim source's earlier open-decision language is historical, not a current lack of authorization.

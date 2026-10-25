# PR #5 stage/regression diagnosis: revision ledger

Source: [pr5-stage-regression-diagnosis.md](pr5-stage-regression-diagnosis.md). This ledger records revisions to that document; SG-01 through SG-04 in the source remain the candidate implementation findings. Canonical continuity: [LEDGER.md](LEDGER.md), L175.

| Revision | Source/request | Acceptance evidence | Status |
|---|---|---|---|
| SR-01 | User: diagnose all anomalous stages | All 112 records checked; complete expected/actual matrix; all seven failed expectations individually traced to recorded outputs and current code. | done in initial report |
| SR-02 | Keep task grades separate from stages | Original ground truth, expected stage, actual verdict, refusal and provenance are distinguished; no grade or rule changes. | done in initial report |
| SR-03 | Review regressions | Both qualified regressions traced against immutable L161 artifacts; 06-02 historical timeout and name-dependent tests disclosed; 16-07 witness-form/repair sequence documented. | done in initial report |
| SR-04 | Persist findings and supporting evidence | SG-01–04 retained individually; offline probes and 761 artifact hashes archived outside Git; independent-review quota limit explicit. | done in initial report; independent implementation triage remains pending |
| SR-05 | Verify diagnosis without unnecessary live calls | 20 existing offline contract tests pass under `-W error`; bounded scripted/AST/adapter reproductions; zero provider calls and no runtime edits. | done in initial report |

| SR-06 | User authorizes SG-01/03, requires an actual SG-02 content format and corrects SG-04 scope; Astra independently reviews strategy/diff. | Persist cancellation, adopt CommonMark parsing, retire unsound automatic deadlock grading for existing MANUAL adjudication, and correct the operational-versus-semantic infeasibility diagnosis. Pin deleted-checker evidence to its original commit; preserve all raw history. | implemented locally; targeted/integrity checks pass; final offline/live/catalogue/CI pending |

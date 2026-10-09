# PDL vs Natural-Language IR: Confirmed-Route Pilot

This package defines a pre-registered pilot comparing two representations inside the same confirmed protocol. It is a plan and task set, not evidence that either arm has won.

## Package contents

- `EXPERIMENT_PLAN.md` — protocol, arms, run order, metrics, predicted outcomes, stopping rules, and cost estimate.
- `tasks/task-01-usage-reconciliation.md` — coding/data task with deterministic expected outputs.
- `tasks/task-02-queue-cutover.md` — rollout and configuration task with concrete operational constraints.
- `tasks/task-03-incident-postmortem.md` — incident reconstruction task with UTC-normalized evidence.
- `tasks/fixtures/task-01/` — exact account, pricing and event inputs for the reconciliation task.
- `scoring/acceptance-criteria.csv` — frozen requirement inventory and weights.
- `scoring/golden-expectations.json` — fixed expected task facts and machine-checkable outcomes.
- `scoring/SCORING_PROTOCOL.md` — outcome scoring, blind review, and analysis rules.
- `config/preregistration.yaml` — machine-readable study choices and decision thresholds.
- `config/arm-instructions.md` — exact shared stage instructions and the only intended representation-specific deltas.

## Important

The task packets are realistic, authored scenarios—not claims to be verbatim customer requests. For a later confirmatory study, replace or augment them with sanitized real work requests selected before observing any results. Do not alter these task texts after seeing outputs from either arm.

The six fixed-artifact replays require a way to restore the confirmed execution context with the artifacts frozen. Use the repository's session-branch/restore capability if available. Do not regenerate or edit the frozen artifacts before replay.

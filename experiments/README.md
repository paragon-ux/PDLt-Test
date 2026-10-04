# experiments/: Acceptance-Gate Tooling

This is the measurement code for the one-shot acceptance gate in [`docs/plans/protocol-vs-control-experiment-design.md`](../docs/plans/protocol-vs-control-experiment-design.md); the fixes it checks are in [`docs/plans/protocol-fixes-plan.md`](../docs/plans/protocol-fixes-plan.md).

It is evaluation plane, like `graders.py` and `run_catalogue.py`: it may know the benchmark. The harness (`src/pdl_taskmaster`) never imports it, and nothing here changes what a model sees in a protocol run.

| File | What it is |
|---|---|
| `generate.py` | The generated isomorph items: the **gate set** (decides acceptance) and the **dev set** (calibration only; never decides). Fixed seeds; every answer is solver-checked. |
| `prompts/{gate,dev}/` | The generated items, their solutions and a `MANIFEST.jsonl` per set. Frozen. |
| `prompt_set.py`, `PROMPT_SET.lock.json` | The gate's frozen prompt list (strata T, G, S, I, Q, and DEV), with a SHA-256 per file. |
| `graders_gen.py` | Graders for the generated families whose catalogue graders are not parametric (copies of 16-03's and 16-07's). |
| `grading.py` | Grading every arm the same way: one code budget (HEAVY_COMPUTE), P-first extraction, the derived headless outcome, BYPASS replies, blind adjudication export. |
| `controls.py` | The plain-call arms C0–C3, sent through the worker's own transport. |
| `runner.py` | The gate runner: `plan`, `run` (resumable, `--smoke`), `export`, `report`. |
| `schedule.py` | The seeded schedule, and the append-only ledger (an outage voids and re-runs the whole block). |
| `adjudicate.py` | The symmetric audit queue (every discordant pair, both directions, plus 20% of concordant pairs), and verdicts → audited score. |
| `analysis.py` | Prompt-level statistics (sign-flip test, BCa bootstrap) and the decision rules G1, G2, G4, U1 and U2. |
| `rubrics.md` | Adjudication rubrics, frozen with the lock. |
| `gate_config.example.json`, `gate_config.smoke.json` | Run configurations. |

## Commands

```bash
py -3.11 -m experiments.generate --check
```

```bash
py -3.11 -m experiments.prompt_set --check
```

```bash
py -3.11 -m experiments.runner plan --config experiments/gate_config.example.json
```

```bash
py -3.11 -m experiments.runner run --config experiments/gate_config.smoke.json --smoke
```

Use `py -3.11`. The `python` on PATH (3.14) lacks pydantic, and under the Microsoft Store `python3` (3.12) the sandbox cannot confine programs.

## Day-0 checklist (before the first gate block)

1. PRs 3, 4a and 4b are merged. PR 5 (ultrafast) is merged, or the P_unc arm is dropped; it is never added mid-run. Worktrees exist at the P_old and P_new SHAs.
2. A second rater confirms the famous tiers in `prompt_set.py`. A change is re-locked before Day 1, never after.
3. The grader stress test (design §12.1) has run on its answers.
4. The headless derivation is validated: 20 recorded force-confirmed sessions are replayed under `--fast` with no piped confirmations, and `grading.headless_stop` matches exit 2 every time (design §9.4).
5. Credits are topped up and the key cap is raised (decision D6).
6. `gate_config.example.json` is copied to a dated config with the worktree paths, and committed with the SHAs.
7. A smoke run of that config (`--smoke`) passes.
8. `runner run`, with no interim look at outcomes by arm.

**After the run:**
1. `runner export --seed <n>`, then two adjudicators fill the sheet;
2. `runner report --sheet ... --key ... --mechanism facts.json`.

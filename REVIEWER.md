# Reviewer & Auditor Guide: PDLt-Test

**Audience**: Independent auditors, adversarial reviewers (e.g. Claude Sonnet), and benchmark evaluators.
**Scope**: Repository structure, signal-to-noise ratio, ground truth vs. execution artifacts, and anti-gaming audit instructions for `PDLt-Test`.

---

## 1. Executive Summary & Design Invariant

`PDLt-Test` is an empirical evaluation testbed for the [PDL Standard REPL Harness (`pdl-taskmaster`)](https://github.com/paragon-ux/PDL-Standard-REPL-Harness).

### The Referee Invariant (GUARD-01 through GUARD-05)
The harness is strictly an **objective protocol governor and referee**, never an AI task solver.
- **Diagnostic Failure is Healthy**: If an LLM fails to solve a complex combinatorial puzzle (e.g., Schur triples or exact cover) at `reasoning: low`, that failure accurately reflects model capability boundaries.
- **Gaming is a Critical Defect**: Any test pass achieved via algorithmic coaching, injected keywords, or synthetic prompt rewriting in the harness is an integrity breach violating Goodhart's Law.

---

## 2. Directory Tree: Signal vs. Noise Breakdown

```
PDLt-Test/
├── prompts/                         # [SIGNAL - CRITICAL] Frozen Benchmark SSOT
│   ├── CATALOGUE_MANIFEST.jsonl     # [SIGNAL] Machine-readable index of all 105 prompts
│   ├── solutions/                   # [SIGNAL] Mathematical ground-truth witnesses
│   ├── 01_combinatorial_search/     # [SIGNAL] 7 raw prompt files (.txt)
│   ├── 02_data_structures/          # [SIGNAL] 7 raw prompt files (.txt)
│   ├── ...                          # [SIGNAL] Categories 03 through 14
│   └── 15_performance_and_scale/    # [SIGNAL] 7 raw prompt files (.txt)
├── run_catalogue.py                 # [SIGNAL] Deterministic test runner & harness coordinator
├── GOAL.md                          # [SIGNAL] Non-negotiable testing rules & execution contract
├── STEP5_SPOT_CHECK_REPORT.md       # [CONTEXT] Historical spot-check verification record
├── README.md                        # [CONTEXT] Overview and usage documentation
├── REVIEWER.md                      # [CONTEXT] This auditor guide
└── catalogue-runs/                  # [NOISE / RUN ARTIFACTS] Historical execution traces
    ├── run-20260928-085311/         # [NOISE] Timestamped run artifacts
    ├── run-20260930-010712/         # [NOISE] Timestamped run artifacts
    └── ...                          # [NOISE]
```

### What Matters (Signal)
1. **`prompts/CATALOGUE_MANIFEST.jsonl`**: The Single Source of Truth for test configurations. Defines ID, category, filename, difficulty, expected routing (`VERIFIED_EXECUTION`, `STANDARD_EXECUTION`, `BOUNDARY_REFUSAL`), expected stage, ground truth status, and rules stressed.
2. **`prompts/*/*.txt`**: The 105 raw prompt files. These must remain pure, realistic user requests without injected protocol directives or solver coaching.
3. **`prompts/solutions/*.json`**: Ground truth witness files. For instance, `solutions/01_combinatorial_search/schur_triples_n15.json` contains valid mathematical partitions against which solver outputs are verified.
4. **`run_catalogue.py`**: The driver script. Reviewers should check that it executes `pdlt` in clean subprocess environments without passing hidden cheat flags or prompt mutations.

### What Does NOT Matter (Noise / Secondary)
1. **`catalogue-runs/`**: This directory stores past execution runs. Each subdirectory contains `RUN_META.json`, `SCOREBOARD.json`, `SCOREBOARD.md`, and individual prompt `transcript.txt` and `result.json` files. **Do not confuse historical scoreboard snapshots with specification requirements.** They are empirical results from prior model runs and harness commits.

---

## 3. Adversarial Audit Checklist

When auditing `PDLt-Test` or evaluating test runs, verify the following 5 checkpoints:

### Checklist 1: Prompt Purity
Inspect any prompt in `prompts/`:
- Does it contain artificial hints like `"Use Knuth's Algorithm X"` or `"Use constraint propagation with MRV"`? **If yes, flag as contaminated.**
- Does it look like natural user input specifying a problem with its inputs and constraints? **If yes, it is valid.**

### Checklist 2: Manifest Consistency
Run the dry run validation:
```powershell
python run_catalogue.py --dry-run
```
- Total prompts must equal 105.
- Exactly 21 prompts should be marked `VERIFIED` ground truth.
- Manifest must parse cleanly with zero schema errors.

### Checklist 3: Runner Impartiality (`run_catalogue.py`)
Inspect `run_catalogue.py`:
- Command line constructed: `pdlt --non-interactive --exit-on-close --stage PROMPT_REVIEW ...`
- Confirm that no prompt pre-processing, regex stripping, or hint insertion occurs in `run_catalogue.py`.

### Checklist 4: Clean Stage Transitions
Check per-prompt `results/<prompt_id>/result.json` in a run directory:
- Exit code `0` (`CLOSED_SUCCESS`): Must transition through `PROMPT_REVIEW` -> `PLAN_REVIEW` -> `EXECUTION` -> `CLOSED_SUCCESS`.
- Exit code `1` (`CLOSED_CANCELLED`): Boundary refusal must complete cleanly in <2s without crashing.
- Exit code `2` (`UNCONFIRMED_GATE`): Model failed to produce a conforming prompt/plan review confirmation.
- Exit code `3` (`WAITING_INPUT`): Execution paused legitimately awaiting external input.

### Checklist 5: Ground Truth Verification
For categories marked `ground_truth_status: verified` (Categories 01, 13, 14):
- Confirm that the deliverable was verified against `prompts/solutions/` or host execution sandbox stdout, not LLM self-grading or regex scraping.

---

## 4. Execution Commands for Reviewers

```powershell
# 1. Verify manifest integrity (0s)
python run_catalogue.py --dry-run

# 2. Fast check of Negative & Impossible Tasks (boundary refusals, ~30s)
python run_catalogue.py --category 13 --fail-fast

# 3. Fast check of Combinatorial Search category (~3m)
python run_catalogue.py --category 01 --fail-fast
```

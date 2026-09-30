# PDLt Test Suite & System 2 Prompt Catalogue

Empirical benchmark testbed and protocol compliance suite for the [PDL Standard REPL Harness (`pdl-taskmaster`)](https://github.com/paragon-ux/PDL-Standard-REPL-Harness).

This repository houses the frozen **105-Prompt System 2 Catalogue**, designed to evaluate reasoning models under deterministic protocol governance without human intervention, algorithmic coaching, or prompt cheating.

---

## Mission & Purpose

The primary mission of `PDLt-Test` is to measure genuine model capability boundaries and protocol adherence:
1. **Protocol Fidelity**: Does the model adhere to the Prompt Pseudocode specification (`PDL-01` through `PDL-08`) across all review stages?
2. **Autonomous Execution**: Can the model produce executable solver scripts or analytical proofs that satisfy deterministic contract verifiers without prompt injections or harness crutches?
3. **Boundary Refusal**: Does the runtime correctly intercept and fail-closed out-of-scope, network-dependent, or contradictory tasks?

---

## Catalogue Taxonomy (15 Categories, 105 Prompts)

The suite is partitioned into 15 categories with 7 prompts each (105 total). 21 prompts have mathematically verified ground-truth solutions.

| # | Category | Focus Areas | Ground Truth Status |
|---|---|---|---|
| **01** | `combinatorial_search` | Schur triples, exact cover (DLX), graph coloring, subset sum, Latin square | Verified (20+ solutions) |
| **02** | `data_structures` | LFU cache O(1), persistent RB-tree, concurrent LRU, B+ tree | Not required |
| **03** | `systems_programming` | Async rate limiter, append-only WAL, lock-free SPSC queue, memory pools | Not required |
| **04** | `parsers_and_compilers` | Recursive descent calculator, streaming JSON, regex-to-NFA, LL(1) tables | Not required |
| **05** | `algorithm_design` | Interval merging, Kahn cycle detection, LCS reconstruction, A* grid search | Not required |
| **06** | `debugging_and_repair` | Off-by-one binary search, two-lock deadlocks, memory leaks, silent corruption | Not required |
| **07** | `refactoring_and_design`| God class decomposition, callback-to-async, inheritance-to-composition | Not required |
| **08** | `specification_extraction`| Vague CRM requirements, contradictory API specs, implicit ETL constraints | Not required |
| **09** | `adversarial_and_injection`| Fielded schema injection, system prompt overrides, nested fence escapes | Not required |
| **10** | `multi_turn_and_revision`| Scope revision, approach backtracking, cumulative ledger carry | Not required |
| **11** | `cross_domain_composition`| Log parsing & repair, schema migration & backfill, spec & implement | Not required |
| **12** | `domain_knowledge` | DNS resolution trace, git rebase conflicts, SQL indexing, OAuth2 PKCE | Not required |
| **13** | `negative_and_impossible`| Unsatisfiable constraints, NP-hard exact search, out-of-scope, stale cutoff | Verified |
| **14** | `formal_verification` | Loop invariants, type soundness, deadlock freedom, termination proofs | Verified |
| **15** | `performance_and_scale` | Eviction policies, DB sharding keys, stream vs batch, GC throughput tuning | Not required |

---

## Manifest Schema (`prompts/CATALOGUE_MANIFEST.jsonl`)

Every benchmark prompt is tracked in `prompts/CATALOGUE_MANIFEST.jsonl` with the following schema:

```json
{
  "id": "01-01",
  "category": "combinatorial_search",
  "file": "01_combinatorial_search/schur_triples_n15.txt",
  "difficulty": "hard",
  "expected_routing": "VERIFIED_EXECUTION",
  "expected_stage": "CLOSED_SUCCESS",
  "ground_truth_status": "verified",
  "solution_file": "solutions/01_combinatorial_search/schur_triples_n15.json",
  "pdl_rules_stressed": ["PDL-02", "PDL-07", "PDL-08"],
  "regression_ref": "REG-003",
  "tags": ["backtracking", "witness", "partition"]
}
```

---

## Test Execution & CLI Runner

The test runner `run_catalogue.py` orchestrates non-interactive, headless REPL runs.

### Quick Start: Dry Run
Verify that the 105 prompts, manifest, and solution references are valid:
```powershell
python run_catalogue.py --dry-run
```

### Running a Specific Category
Run only Category 13 (Negative & Impossible Tasks) or Category 01 (Combinatorial Search):
```powershell
python run_catalogue.py --category 13
python run_catalogue.py --category 01 --fail-fast
```

### Full Catalogue Benchmark Run
Execute all 105 prompts against a target model configuration:
```powershell
python run_catalogue.py --model openai/gpt-oss-120b --reasoning low
```

### CLI Options
- `--dry-run`: Validate manifest entries without executing `pdlt`.
- `--category <CAT>`: Run only prompts in specific categories (e.g. `01`, `01,02`, or `combinatorial_search`).
- `--fail-fast`: Immediately halt the test run on the first failure.
- `--timeout <SECS>`: Per-prompt execution timeout (default: 300 seconds).
- `--model <ID>`: Target model identifier (default: `openai/gpt-oss-120b`).
- `--reasoning <EFFORT>`: Reasoning effort level (`low`, `medium`, `high`).

---

## Exit Codes & Protocol Semantics

When running in headless mode (`--non-interactive --exit-on-close`), `pdlt` exits with standardized status codes (ADR-0019):

| Exit Code | Stage Name | Description |
|---|---|---|
| **0** | `CLOSED_SUCCESS` | Deliverable verified, contracts satisfied, clean protocol closure. |
| **1** | `CLOSED_CANCELLED` | Fail-closed error, intentional user cancellation, or boundary refusal. |
| **2** | `UNCONFIRMED_GATE` | Stalled at a review gate (Prompt Review or Plan Review). |
| **3** | `WAITING_INPUT` | Legitimate execution pause awaiting external user input. |

---

## Output Structure (`catalogue-runs/`)

Every execution run produces an isolated timestamped directory under `catalogue-runs/`:

```
catalogue-runs/run-<YYYYMMDD-HHMMSS>/
├── RUN_META.json           # Environment, model flags, and git commit
├── SCOREBOARD.json         # Raw aggregate statistics (pass/fail/stall)
├── SCOREBOARD.md           # Markdown scoreboard table
└── results/
    ├── 01-01_schur_triples_n15/
    │   ├── transcript.txt  # Full interactive REPL session output
    │   ├── stderr.txt      # Stderr capture
    │   └── result.json     # Exit code, stage transitions, duration
    └── ...
```

---

## Anti-Overfitting & Non-Negotiable Rules

1. **No Retries / No Cherry-Picking**: Prompts receive exactly one execution attempt. Manifest order is preserved.
2. **Immutable Prompts**: Benchmark prompt files are read-only inputs.
3. **The Referee Invariant**: The test harness is strictly an objective evaluator. It must never inject algorithmic advice, coach the model, or fabricate witnesses.
4. **Diagnostic Integrity**: A failed test is diagnostic of authentic model capability boundaries; gamed passes are critical integrity breaches.

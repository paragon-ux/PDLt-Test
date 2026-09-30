# Reviewer Navigation Guide: PDLt-Test

> **For LLM Reviewers & Auditors**: Read this file first. It is an index of where critical benchmark fixtures live and what files to **ignore** to save context tokens.

---

## 1. System in 30 Seconds

`PDLt-Test` is the empirical evaluation testbed for the [PDL Standard REPL Harness (`pdl-taskmaster`)](https://github.com/paragon-ux/PDL-Standard-REPL-Harness).

It executes the frozen **105-prompt System 2 Catalogue** through the live `pdlt` REPL in headless mode (`--non-interactive --exit-on-close`) to measure genuine model capability boundaries under deterministic protocol governance.

**Core Invariant**: Benchmark prompts are immutable inputs. If a model fails a prompt, that is valid diagnostic data. The harness must never be modified to inject hints or bypass gates.

---

## 2. File Map: What Matters (Read These)

| Path | Description |
|---|---|
| `prompts/CATALOGUE_MANIFEST.jsonl` | **SSOT Manifest**: Index of all 105 prompts with category, difficulty, expected routing, and rules stressed. |
| `prompts/<category>/*.txt` | **105 Raw Benchmark Prompts**: Read-only problem descriptions across 15 categories (7 prompts per category). |
| `prompts/solutions/*.json` | **Ground-Truth Witnesses**: Mathematical solutions for verifiable categories (Schur triples, exact cover, etc.). |
| `run_catalogue.py` | **Test Runner Engine**: Spawns `pdlt` subprocesses, enforces timeouts, captures transcripts, and computes scoreboards. |
| `GOAL.md` | **Testing Contract**: Non-negotiable execution rules (no retries, no cherry-picking, single model). |

---

## 3. What to Ignore (Skip - Do Not Waste Context)

| Path | Reason to Skip |
|---|---|
| `catalogue-runs/` | **Massive historical log dumps**. Contains timestamped runs (`transcript.txt`, `stderr.txt`, etc.). Do NOT load these into context unless diagnosing a specific historical run. |
| `STEP5_SPOT_CHECK_REPORT.md` | Historical spot-check notes from earlier development phases. |

---

## 4. Exit Codes & Protocol Semantics

`run_catalogue.py` evaluates headless `pdlt` exit codes (ADR-0019):

| Exit Code | Stage Name | Interpretation |
|---|---|---|
| **0** | `CLOSED_SUCCESS` | Deliverable verified, contracts satisfied, clean closure. |
| **1** | `CLOSED_CANCELLED` | Intentional refusal or fail-closed boundary enforcement. |
| **2** | `UNCONFIRMED_GATE` | Stalled at review gate (model failed to confirm or revise). |
| **3** | `WAITING_INPUT` | Paused awaiting external input. |

---

## 5. Quick Verification Commands

```powershell
# 1. Manifest dry run (<1s)
python run_catalogue.py --dry-run

# 2. Fast check of Negative & Impossible boundary refusals (~30s)
python run_catalogue.py --category 13 --fail-fast

# 3. Fast check of Combinatorial Search (~3m)
python run_catalogue.py --category 01 --fail-fast
```

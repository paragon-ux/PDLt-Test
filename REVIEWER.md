# Reviewer Navigation Guide: PDL Taskmaster (lean build) + PDLt catalogue

> **For LLM Reviewers & Auditors**: Read this file first. It indexes where critical logic lives and what to **ignore**.

## 1. System in 30 seconds

Two planes. The **harness** (`src/pdl_taskmaster/`) is a deterministic protocol referee: S1 routes (`providers/sys1/`), S2 drafts and executes (`providers/api_worker.py`), the verifier checks schemas and runs code in a sandbox. The **evaluation plane** (`run_catalogue.py`, `graders.py`, `prompts/`) drives the frozen 105-prompt catalogue and grades answers.

**Golden invariant:** the harness is a referee, never a solver. No algorithmic coaching, no keyword gates, no benchmark vocabulary in `src/`, no fabricated witnesses.

## 2. Read these

| Concern | Path |
|---|---|
| Guardrails (GUARD-01..05) | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` |
| Current design | `ARCHITECTURE.md` |
| Direction (not implemented) | `TARGET_ARCHITECTURE.md`, ADR-0023 to ADR-0026 |
| State machine, engine, witness authority | `src/pdl_taskmaster/runtime/session_engine.py` (`_draft_plan`, `_parse_sandbox_witness`, `_refuse`) |
| Result IR | `src/pdl_taskmaster/runtime/result_ir.py`, `wire_payloads.py` |
| Grammar lint (PDL-05/06/08 only) | `src/pdl_taskmaster/verification/plan_soundness.py` |
| Verifier + sandbox | `verification/output_verifier.py`, `verification/sandbox.py`, `verification/checkers/` |
| System 1 | `providers/sys1/` (Phase 0 route runs first via `session_engine._s1_activation`; `client.py`, `gating.py`, `recipes/activation_route.py`, `problem_class.py`, `confirmation_match.py`, `review_facets.py`) |
| System 2 client | `providers/api_worker.py` |
| Integrity gate | `tests/test_harness_anti_overfitting.py` |
| Viewer (evaluation plane) | `viewer/server.py`, `viewer/index.html` |
| Runner, graders, contract | `run_catalogue.py`, `graders.py`, `GOAL.md`, `prompts/CATALOGUE_MANIFEST.jsonl` |
| Agent rules | `AGENTS.md` |

## 3. Ignore

`catalogue-runs/` (run logs; load only to diagnose one run), `docs/adr/` (frozen history; the guardrail wins on conflict), `contracts/` and `src/pdl_taskmaster/contracts/` (hash-pinned data), `__pycache__/`, `.venv/`.

## 4. Invariants

- Retry feedback travels only via operator correction; `CARRIED_APPROACH_SOURCES` is user-originated only (`GUARD-01`).
- No benchmark IDs, prompt stems or problem vocabulary in `src/`; verifier never infers domain from text (`GUARD-02`).
- Sandbox witness is authoritative; unreproduced witnesses are provisional; no stdout scraping (`GUARD-03`).
- `is_prompt_pass` is unchanged; ground truth is graded separately (`graders.py`).

## 5. Quick checks

```bash
pytest tests/test_harness_anti_overfitting.py -v   # integrity gate (<1s)
pytest -q                                           # offline suite
python run_catalogue.py --dry-run                   # manifest: 105 prompts, 21 verified
```

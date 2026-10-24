# Reviewer Navigation Guide: PDL Taskmaster (lean build) + PDLt catalogue

> **For LLM Reviewers & Auditors**: Read this file first. It indexes where critical logic lives and what to **ignore**.

## 1. System in 30 seconds

Two planes. The **harness** (`src/pdl_taskmaster/`) is a deterministic protocol referee: S1 routes (`providers/sys1/`), S2 drafts and executes (`providers/api_worker.py`), the verifier checks schemas and runs code in a sandbox. The **evaluation plane** (`run_catalogue.py`, `graders.py`, `prompts/`) drives the 112-prompt catalogue and grades answers.

**Golden invariant:** the harness is a referee, never a solver. No algorithmic coaching, no keyword gates, no benchmark vocabulary in `src/`, no fabricated witnesses.

## 2. Read these

| Concern | Path |
|---|---|
| Setup, by host | `docs/getting-started.md`, `docs/hosts/` (Windows, Linux, macOS), `docs/reference.md` |
| Library API (the primary entry point) | `src/pdl_taskmaster/api/`, `docs/api.md` |
| Extensions SDK (task types, verifiers, providers) | `src/pdl_taskmaster/extensions/`, `docs/extensions.md` |
| REPL and headless runs | `src/pdl_taskmaster/host/repl.py`, `docs/repl.md` |
| MCP server | `src/pdl_taskmaster/host/mcp_server.py`, `docs/mcp/EXTERNAL_TOOLS.md` |
| Packaging and release | `pyproject.toml`, `.github/workflows/`, `docs/releasing.md` |
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

## 3. Follow affected contracts; skip unrelated material

Read the affected normative ADRs and operation/standard contracts in `docs/adr/`, `contracts/` and `src/pdl_taskmaster/contracts/` when they define the behavior under review. Follow their amendments and the canonical ledger; hash pinning does not make a contract irrelevant. Apply the guardrails when assessing a conflicting implementation. Unrelated historical decisions, `__pycache__/` and `.venv/` can be skipped.

## 4. Invariants

- Retry feedback travels only via operator correction; `CARRIED_APPROACH_SOURCES` is user-originated only (`GUARD-01`).
- No benchmark IDs, prompt stems or problem vocabulary in `src/`; verifier never infers domain from text (`GUARD-02`).
- Sandbox witness is authoritative; unreproduced witnesses are provisional; no stdout scraping (`GUARD-03`).
- `is_prompt_pass` is unchanged; ground truth is graded separately (`graders.py`).

## 5. Order of evidence

1. **Code first.** Cite `file:line`.
2. **Recorded artifacts.** Those in the catalogue runs archive (outside the repository: `$PDLT_CATALOGUE_RUNS`, else `PDLt-Catalogue-Archive` beside the checkout; load one run at a time) and session folders (`call-trace.jsonl`, `events.jsonl`, `compiled-projection.json`, `model-response.txt`).
3. **Offline tests.** These include recorded replays (`--worker recorded`).
4. **A live run.** Only for model, provider or System 1 behaviour that the above cannot settle.

A static conclusion about runtime behaviour stays a hypothesis until an artifact confirms it. See `AGENTS.md`, "Diagnosis and Verification Rule".

## 6. Quick checks

```bash
pytest tests/test_harness_anti_overfitting.py -v   # integrity gate (<1s)
pytest -q                                           # offline suite
python run_catalogue.py --dry-run                   # manifest: 112 prompts, 57 verified (29 by hidden tests)
```

# Release Audit: 2.6.0rc1 (first public release)

**Date:** 2026-10-02. **Scope:** the whole repository: source, tests, contracts and standards, ADRs, configuration, CLI behaviour, documentation and release artifacts (sdist and wheel). **Question:** what the project claims against what it implements, and what blocks a first public release.

Severity: **High** blocks release or misleads users about safety or behaviour; **Medium** is a visible defect or a misleading document; **Low** is cleanup. Each defect is either fixed in this release or deferred with a named home.

## 1. Fixed in this release

| ID | Severity | Area | Defect | Resolution |
|---|---|---|---|---|
| RA-01 | High | Docs | `ARCHITECTURE.md` described another repository (`PDL-Standard-REPL-Harness`): non-existent modules (`eval/`, `tracking/`, `docs/trd/`), stage names that do not exist (`UNINITIALIZED`, `PROMPT_DRAFTING`, `EXECUTING`), a stale test count, and commands that fail (`python -m pdl_taskmaster.eval.*`, `waymark`). | Rewritten as the current architecture, every claim checked against the code. |
| RA-02 | High | Docs | `TARGET_ARCHITECTURE.md` presented the current build as an "approved target v2.7.0" with `2.6.0` as baseline, while the package is `2.6.0rc1`. | Current content moved to `ARCHITECTURE.md`; `TARGET_ARCHITECTURE.md` now states only the future direction and marks what exists today. |
| RA-03 | Medium | Docs | 15 links in 13 ADRs pointed to requirement documents not in this repository (`docs/trd/`, `pdlt-docs/`). | Links turned into plain references marked as upstream documents; noted in the ADR index. |
| RA-04 | Medium | ADRs | ADR-0011 was "Accepted" though its microVM and MCP sandboxing clauses were never implemented. | Status "Accepted in part"; points to ADR-0021 and ADR-0025. |
| RA-05 | Medium | ADRs, docs | Exit codes `4` (harness or provider error) and `130` (interrupt) were returned but documented nowhere (README, ADR-0019, `AGENTS.md`). | Documented in all three and in `ARCHITECTURE.md`. |
| RA-06 | Medium | ADRs | ADR-0020 decision 2 (deterministic pattern fast paths) contradicts GUARD-02 and a test that asserts its absence; the ADR was silent on what happens without System 1. | Amendment in the status section. |
| RA-07 | Low | ADRs | ADR-0012 described the Laya and RLCD training pipeline as if present; ADR-0017's index row omitted that Pillar 2 is superseded. | Status notes and index rows corrected. |
| RA-08 | Medium | Docs | `LEAN_BUILD_PLAN.md` at the repository root was an internal first-person working plan for an old branch. | Removed (kept in git history). |
| RA-09 | Medium | Docs | `GOAL.md` cited regressions REG-001 to REG-004 (REG-002 and REG-004 do not exist; the manifest uses REG-001, REG-003, REG-011 to REG-014) and said they "should pass", against `AGENTS.md`; the file had a byte-order mark. | Corrected; BOM removed. |
| RA-10 | Medium | Docs | `REVIEWER.md` cited functions that no longer exist (`_s1_boundary_refusal`, `_verify_witness`); eight source and test docstrings cited sections of the old target document. | Names and section references updated. |
| RA-11 | Low | Docs | `docs/audits/NEGATIVE_CLAUSE_AUDIT.md` described since-fixed behaviour without saying it is a dated snapshot. | Marked as a historical snapshot. |
| RA-12 | Medium | Packaging | `pyproject.toml` declared "Production/Stable" for a release candidate. | "Beta". |
| RA-13 | High | Packaging | The sdist's unanchored include patterns (`README.md`) matched at any depth and pulled in another tool's local worktree (`.kilo/worktrees/...`); the sdist shipped `tests/` without the `prompts/`, `graders.py`, `run_catalogue.py`, `viewer/` and `scripts/` they import, so its test suite could not run. | Patterns anchored; evaluation plane and docs included. Verified: the suite passes from an unpacked sdist. |
| RA-14 | High | CI | No workflow ran the test suite or the integrity gate; only the path-filtered sandbox workflow existed, while the docs describe the gate as continuous. | `.github/workflows/ci.yml`: integrity gate, catalogue dry run and full suite on Linux (3.10, 3.12) and Windows (3.12), plus a build and wheel smoke test. |
| RA-15 | Medium | Tests | Two provider-schema regression tests skipped whenever `jsonschema` was absent, and it was not a test dependency, so they never ran. | `jsonschema` added to the `test` and `dev` extras. |
| RA-16 | Medium | CLI | With no API key on Windows, the error printed the whole PowerShell lookup script and a `WriteErrorException` dump. | The error names the variable to set; two tests. |
| RA-17 | Medium | REPL | `/transcript <path>` closed the current transcript before opening the new one: a bad path raised an unhandled `OSError` and left logging on a closed handle. | Opens the new file first; reports and keeps the old one on failure; test. |
| RA-18 | Medium | REPL | Typing `/confirm` at the "Pasted N lines" prompt appended `/confirm` to the pasted request. | `/confirm` submits like Enter, in both paste paths; two tests. |
| RA-19 | Low | Source | `runtime/semantic_observer.py` was unreferenced and read contracts from a repository-relative path (broken in an installed wheel). | Removed. |
| RA-20 | Low | Source | `observation/cli.py` carried another project's name and crashed on records without hashes. | Renamed and guarded. |
| RA-21 | Low | Docs | The packaged provider README did not mention `ApiWorker`, the default worker. | Worker table added. |
| RA-22 | Low | REPL | The start banner omitted `/cancel`. | Added. |
| RA-23 | Low | Config | `.gitignore` did not cover build output. | `dist/`, `build/` added. |
| RA-39 | Medium | CLI | A provider removed by OpenRouter for an unsupported parameter (SambaNova: no structured output) was reported as a possibly misspelled provider name. | The message names the unsupported parameter and suggests `--no-structured-output`; test. |
| RA-40 | High | Routing | Groq, first in the default provider order, rejects the `EXECUTE` and `EMIT_RESULT_IR` schemas (a union nested inside a union); the default order worked only because OpenRouter fell through to Baseten, and `--api-providers Groq` failed every task at `EXECUTE`. Flattening the union was tested and broke the default order (Groq then fails generations, and OpenRouter does not fall back on that). | Groq removed from the default order (now Baseten → Crusoe, one provider per default session). When a user configures Groq, those two operations are routed away from it (removed from the order, added to `ignore`) when the schema is sent; Groq alone stops with a clear message; tests, and live per-call verification in [`PROVIDERS.md`](../../PROVIDERS.md) §3. |

Fixed earlier on this branch, before this audit: `/cancel` rejected at review gates; `/paste` ending at the first blank line; blocking Windows console burst reads; two Windows-only test failures; a review command after closure restarting the closed task.

## 2. Documented, not changed in code

These are real, but changing them is a design decision rather than a release fix. Each is now stated plainly in `ARCHITECTURE.md` and assigned to a future ADR.

| ID | Severity | Defect | Where documented | Future home |
|---|---|---|---|---|
| RA-24 | High | Boundary refusal depends on System 1. When System 1 is absent, unconfigured, failing or unsure, no refusal is published and the request proceeds; `AGENTS.md` describes refusal as fail-closed. System 1 is OpenRouter's remote decisions endpoint, so local-only deployments always take this path. The sandbox's limits still apply. | `ARCHITECTURE.md` §3.3, README, ADR-0020 | ADR-0024 (declared absence behaviour) |
| RA-25 | Medium | `PDLT_SANDBOX_NETWORK=true` changes what System 1 is told, but the sandbox never grants network access. | `ARCHITECTURE.md` §10, README, `docs/SANDBOX.md` | ADR-0025 (capabilities derived from enforcement) |
| RA-26 | Medium | ADR-0018 §3.3 (`contradictory_reconciliation`) is not implemented. | ADR-0018 status, ADR index | Typed requirement kind (future requirement) |
| RA-27 | Medium | The Result IR `files` list is never materialized; nothing is written to the user's project. | `ARCHITECTURE.md` §5.3 | ADR-0025 |
| RA-28 | Medium | No domain checkers are registered; every non-reproduced witness is provisional. | `ARCHITECTURE.md` §4 | ADR-0026 (checkers in packs) |
| RA-29 | Medium | Results are text, review gates are prose, observation records are written only after a turn, and there is no session time or token budget. | `ARCHITECTURE.md` §8, §10 | ADR-0023, ADR-0024 |
| RA-30 | Medium | Contract overrides replace the whole set, are chosen by directory location (the candidate repo defaults to the current directory) and are validated for structure only; operation prompts are Python source. | `ARCHITECTURE.md` §7 | ADR-0026 |
| RA-31 | Low | `--sandbox auto` is identical to `native`; the name suggests a fallback to the container that does not exist. | `ARCHITECTURE.md` §5.2 | Implementation follow-up |

## 3. Deferred implementation follow-ups (not release blocking)

| ID | Severity | Defect |
|---|---|---|
| RA-32 | Low | Most anti-overfitting tests check that specific historical strings are absent; the contamination scan covers `.py` and `.txt` under `src/` but not the bundled `.json` and `.md` contracts (those are hash-pinned by `GUARD-05`). |
| RA-33 | Low | Settings changed during a session are lost on `/worker`, and runtime settings (`exit-on-close`) on every session switch. |
| RA-34 | Low | Slash commands run outside the REPL's exception boundary; an unexpected error in one ends the REPL with a traceback. |
| RA-35 | Low | Slash-command arguments are split without `shlex`, so quoted paths keep their quotes; backslash continuation strips indentation. |
| RA-36 | Low | `sandbox.py` and `confinement/backends.py` import each other (avoided at runtime by a deferred import); unused `import re` in `result_ir.py` and `operation_bridge.py`. |
| RA-37 | Low | The Windows API-key fallback interpolates the variable name into a PowerShell command; the name comes only from the user's own `--api-key-env`, so this is not a security boundary. |
| RA-38 | Low | The headless runner confirms review gates by piping `/confirm`; the catalogue therefore measures autonomous drafting under lint gates, not human review (recorded as `gate_policy`). |

## 4. Checked and found sound

- The viewer binds `127.0.0.1` only, rejects non-local `Host` headers (DNS rebinding), and confines every path parameter to its roots.
- API keys never reach model-authored code (environment allowlist), and confinement fails closed when a backend cannot apply.
- The wheel contains only the harness and its bundled contracts, installs cleanly, and runs from an empty directory using the bundled contracts.
- The contract manifest hashes match, and the bundled copy matches the repository copy.
- Documented defaults match the code (model, `--max-output-tokens` 16,384, call deadline 300 s, execution budgets, System 1 environment defaults, runner timeout 600 s).

# Comprehensive Architectural Audit & Claims Verification Matrix

**Investigation Scope**: Pull Request #1: "Add PDL Taskmaster Lean Build: Full CLI REPL & Comprehensive Architecture" on repository `paragon-ux/PDLt-Test`.  
**Auditor**: Explorer Subagent (Architecture, Claims Verification, and Guardrail Compliance).  
**Evaluation Targets**: Requirement R2 (Claims & Testing Verification Matrix), Requirement R4 (Lean Build & Architecture Assessment), ADR-0018 through ADR-0021 Conformance, and Guardrails GUARD-01 through GUARD-05.  
**Execution Environment**: Windows 11, Python 3.11.9, Pytest 9.0.3, Pydantic 2.12.5.  
**Audit Date**: 2026-10-02  

---

## 1. Executive Summary

An exhaustive evaluation of the PDL Taskmaster Lean Build codebase (`src/pdl_taskmaster/`), evaluation plane (`run_catalogue.py`, `graders.py`, `viewer/`), architecture specifications (`TARGET_ARCHITECTURE.md`, `ARCHITECTURE.md`, `docs/adr/`), and test suite (33 test files in `tests/`) was performed.

### Key Conclusions:
1. **Guardrail Invariants (GUARD-01 through GUARD-05)**: Strictly honored. The harness functions purely as a protocol referee with zero prescriptive algorithmic coaching, zero synthetic carried approaches, zero hardcoded benchmark tokens (`frostbitedb`), and full acceptance of symbolic/deductive reasoning deliverables. The mandatory anti-overfitting suite (`tests/test_harness_anti_overfitting.py`) passes 15/15 tests with zero warnings, failures, or skips.
2. **Session-Scoped Confinement (ADR-0021)**: Architecturally sound and properly wired. `ExecutionSandbox` is constructed once during `SessionEngine.__init__`, uses ephemeral per-run directories (`work/run-NNNN-*`), isolates secrets via an environment allowlist, and executes stale-root cleanup.
3. **Pydantic SSOT & Regex Elimination (ADR-0018)**: Verified across the substantive verification plane. Domain detection in `OutputVerifier` has eliminated regex heuristics, model text is parsed using exact string readers (`runtime/text_blocks.py`), and witnesses validate through discriminated union `WitnessPayload`. However, `OutputVerifier` itself is not a Pydantic model, and alias coercion is not implemented in `wire_payloads.py`.
4. **Specification & Implementation Divergence**:
   - **ADR-0018 §3.3**: The claimed `contradictory_reconciliation` check (rejecting existential requirements marked `"satisfied"` on a negative witness) is completely missing from `result_ir.py`.
   - **ADR-0018 §3.1**: `ProblemDomain` in `checkers/base.py` was truncated to `GENERAL = "general"` (stripping `PARTITION_SUM_TRIPLES`, `EXACT_COVER`, `SUBSET_SUM`) to satisfy GUARD-02, leaving ADR-0018 out of sync.
   - **ADR-0019**: `repl.py` introduces an undocumented exit code 4 (`EXIT_HARNESS_ERROR = 4`).
5. **Platform Test Failures on Windows**: Running the full offline test suite revealed **2 failing tests** (546 passed, 42 skipped, 2 failed):
   - `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]` in `tests/test_confinement.py`: Fails because Windows AppContainer blocks `_ctypes.pyd` DLL initialization (`ImportError: DLL load failed while importing _ctypes`).
   - `test_sandbox_blocks_startfile_on_windows` in `tests/test_sandbox.py`: Fails because `os.startfile('cmd.exe')` inside the execution sandbox raises `NotImplementedError: startfile not available on this platform` rather than `PermissionError` from the Python audit hook.

---

## 2. Claims Verification Matrix (Requirement R2)

Below is an exhaustive matrix of 24 distinct claims catalogued from PR #1, `TARGET_ARCHITECTURE.md`, `ARCHITECTURE.md`, `docs/adr/0001` through `0022`, and code comments.

Status classification strictly follows:
- **Verified**: Directly demonstrated by existing automated tests or reproducible implementation behavior.
- **Partially verified**: Some evidence exists, but key paths, platforms, or assumptions remain untested.
- **Unverified**: Claimed in docs/comments but not adequately demonstrated or wired.
- **Contradicted/broken**: Implementation or test execution shows the claim is incorrect or fails.

| Claim ID | Claim Description | Normative Source | Implementation Evidence | Test Evidence | Assigned Status | Limitations / Discrepancies |
|---|---|---|---|---|---|---|
| **CLM-01** | **Session-Scoped Sandbox Lifecycle**: `ExecutionSandbox` is instantiated once in `SessionEngine.__init__`, bound to session lifecycle, and closed via `close()` hook. | `TARGET_ARCHITECTURE.md:28-31, 192-205`; `ADR-0021:16-17` | `session_engine.py:359, 1595-1598`; `app.py:200-205` | `tests/test_confinement.py:33-46, 128-155` | **Verified** | Verified across session engine and host lifecycle. |
| **CLM-02** | **Ephemeral Run Isolation & Stale Root Sweeping**: Each program executes in an isolated `work/run-NNNN-*` directory deleted after run; stale roots whose owner PID is dead are swept on boot. | `TARGET_ARCHITECTURE.md:197, 203-204`; `ADR-0021:17-18` | `sandbox.py:440-525, 861-908` | `tests/test_confinement.py:48-60, 85-106` | **Verified** | Directory isolation verified; stale root sweeping tested. |
| **CLM-03** | **Elimination of Regex Heuristics in Verification Dispatch**: `OutputVerifier.detect_domain` does not regex-scan problem text; domain dispatch is strictly typed or falls back to `FallbackChecker`. | `ADR-0018:14-16, 38-47`; `TARGET_ARCHITECTURE.md:104-106` | `output_verifier.py:37-60`; `checkers/fallback.py:18-89` | `tests/test_output_verifier.py`; `tests/test_harness_anti_overfitting.py:263-270` | **Verified** | `OutputVerifier` itself is a standard class, not a Pydantic model. |
| **CLM-04** | **Discriminated Union WitnessPayload with Strict Validation**: `WitnessPayload` is discriminated on `polarity`; `NegativeWitness` strictly requires `search_exhausted=True` and `nodes_explored: PositiveInt` for search basis, or `argument` for proof basis. | `ADR-0018:48-65`; `TARGET_ARCHITECTURE.md:100-103` | `wire_payloads.py:330-369`; `result_ir.py:262-273` | `tests/test_pydantic_wire.py`; `tests/test_output_verifier.py` | **Verified** | Enforced at wire boundary and in Result IR validation. |
| **CLM-05** | **Reconciliation Semantic Integrity Invariant**: If `witness.polarity == "negative"`, `validate_result_ir` rejects existential requirements (`GENERATE`, `PROVIDE`) marked `"satisfied"` as `contradictory_reconciliation`. | `ADR-0018:68-72` | `result_ir.py:180-275` (completely missing) | None in `tests/test_pydantic_wire.py` or elsewhere | **Contradicted/broken** | The check was never implemented in `validate_result_ir`; keyword scanning was avoided to comply with GUARD-02/04, but ADR-0018 was not updated. |
| **CLM-06** | **Headless Automation Exit Codes (ADR-0019 amended)**: REPL exits 0 for `CLOSED_SUCCESS` or published refusal (`closure=REFUSED`), 1 for `CLOSED_CANCELLED`, 2 for unconfirmed review gates, 3 for `WAITING_INPUT`. | `ADR-0019:30-44, 61-64`; `TARGET_ARCHITECTURE.md:171-179` | `repl.py:1472-1507`; `cli.py:113-125` | `tests/test_repl_integration.py:103-111, 127-163, 226-234`; `tests/test_refusal_closure.py` | **Partially verified** | Exit codes 0, 2, and 3 are tested in automated tests; exit code 1 (`CLOSED_CANCELLED`) has no process-level integration test; exit code 4 (`EXIT_HARNESS_ERROR`) is implemented but undocumented. |
| **CLM-07** | **System 1 Phase 0 Boundary Refusal**: Tasks outside policy scope (`PDLT_POLICY_SCOPE`), requiring network (`PDLT_SANDBOX_NETWORK`), or post-cutoff (`PDLT_KNOWLEDGE_CUTOFF`) are intercepted by System 1 without regex/date matching and refused fail-closed as `closure=REFUSED` (exit 0). | `ADR-0020:17-33`; `TARGET_ARCHITECTURE.md:164, 234-242` | `activation_route.py:43-136`; `session_engine.py:593-628, 1134-1138` | `tests/test_phase0_routing.py`; `tests/test_refusal_closure.py`; `tests/test_harness_anti_overfitting.py:61-69, 162-169, 272-282` | **Verified** | Requires configured `sys1_client`; without System 1, falls through to System 2 by design. Advertised `<15ms` execution is contingent on local model vs network latency. |
| **CLM-08** | **Multi-OS Native Sandbox Backends**: Native OS isolation without third-party dependencies using Landlock on Linux, Seatbelt on macOS, and AppContainer on Windows. | `ADR-0021:19-30`; `TARGET_ARCHITECTURE.md:209-213` | `confinement/backends.py:187-201`; `landlock.py`; `seatbelt.py`; `appcontainer.py` | `tests/test_confinement.py` | **Partially verified / Broken on Windows edge-case** | On Windows, `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]` fails because AppContainer blocks `_ctypes.pyd` DLL initialization. Multi-OS backends skip on non-matching host OS. |
| **CLM-09** | **Opt-in Container Sandbox Mode**: `--sandbox container` provides Docker or Podman containment with read-only root, no network, and process limits. | `ADR-0021:27, 30`; `TARGET_ARCHITECTURE.md:212` | `confinement/container.py:1-120` | `tests/test_confinement.py:800-880` | **Partially verified** | Unit tests use mocks; full integration requires Docker/Podman daemon present. |
| **CLM-10** | **Fail-Closed Sandbox Selection**: When requested backend cannot apply (e.g. Linux <5.13 or missing AppContainer privileges), no code runs (`sandbox_unavailable:<reason>`). | `ADR-0021:31`; `TARGET_ARCHITECTURE.md:213` | `sandbox.py:850-860`; `confinement/backends.py:173-185` | `tests/test_confinement.py:272-300, 316-340` | **Verified** | Demonstrated by unit tests verifying fail-closed execution. |
| **CLM-11** | **Secret Isolation via Environment Variable Allowlist**: Environment is constructed strictly from an allowlist (`PATH`, `TEMP`, `TMP`, Windows system keys); API keys never enter the sandbox process. | `TARGET_ARCHITECTURE.md:210`; `ADR-0021:7, 19` | `sandbox.py:896`; `confinement/policy.py:20-60` | `tests/test_confinement.py:180-220` | **Verified** | API keys confirmed absent from child process environment. |
| **CLM-12** | **Python Audit Hook Defense-in-Depth**: An in-process `sys.addaudithook` prelude denies native code loading, unauthorized file access, network calls, signals, and process creation. | `TARGET_ARCHITECTURE.md:214`; `ADR-0021:32` | `sandbox.py:140-265, 876-879` | `tests/test_confinement.py:173-247` | **Partially verified** | Audit hook functions as defense-in-depth, but `test_sandbox_blocks_startfile_on_windows` fails because `os.startfile` raises `NotImplementedError` before the hook fires. |
| **CLM-13** | **Deterministic Bytecode Step Budget & Opcode Tracing**: Sandbox installs an opcode trace counting executed Python bytecode instructions of user code; exceeding the routed budget immediately terminates the process with `step_budget_exceeded=True`. | `TARGET_ARCHITECTURE.md:254-272` | `sandbox.py:350-405, 880-920` | `tests/test_execution_profile.py:200-280`; `tests/test_sandbox.py` | **Verified** | Validated across MINIMAL (100k), STANDARD (10M), and HEAVY_COMPUTE (100M) budgets. |
| **CLM-14** | **Tripartite System 1 Confidence Gating**: System 1 decisions must satisfy confidence $P \ge 0.85$, margin $\Delta p \ge 0.40$, and normalized entropy $H(p) \le 0.35$. Flatter distributions fallback cleanly. | `TARGET_ARCHITECTURE.md:232, 268-269`; `ADR-0012` | `sys1/gating.py:1-70` | `tests/test_sys1_foundation.py`; `tests/test_sys1_recipes.py` | **Verified** | Gating math and thresholds verified. |
| **CLM-15** | **First-Class Reasoning & Symbolic Deliverables (GUARD-03)**: Non-computational tasks, analytical derivations, word problems, and symbolic proofs are accepted as valid deliverables without forcing Python scripts or numeric fabrication. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-03); `TARGET_ARCHITECTURE.md:93, 290` | `plan_soundness.py:80-140`; `session_engine.py:1360-1420` | `tests/test_harness_anti_overfitting.py:110-125`; `tests/test_plan_soundness.py` | **Verified** | Tested by `test_plan_soundness_accepts_pure_deduction_plan`. |
| **CLM-16** | **Referee Invariant & Zero Algorithmic Coaching (GUARD-01, GUARD-04)**: Harness never injects algorithmic search methods (MRV, DLX, backtracking) into prompts, plans, or `CARRIED_APPROACH_SOURCES`. Feedback travels only via operator correction. | `AGENTS.md`; `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-01, 04); `TARGET_ARCHITECTURE.md:23-26` | `session_engine.py:1165-1215`; `api_worker.py:200-280` | `tests/test_harness_anti_overfitting.py:19-40, 127-144, 243-261` | **Verified** | Confirmed by static inspection and automated anti-overfitting tests. |
| **CLM-17** | **Automated Contract Manifest SHA-256 Synchronization (GUARD-05)**: Contract files in `contracts/` and bundled `src/pdl_taskmaster/contracts/` match `CONTRACT_MANIFEST.json` SHA-256 hashes under LF normalization across all OSs. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-05); `TARGET_ARCHITECTURE.md:292` | `tests/test_harness_anti_overfitting.py:72-108` | `test_guard05_contract_manifest_sha256_synchronized` | **Verified** | 0 hash divergences across repository and bundled copies. |
| **CLM-18** | **Automated Contamination Scan Across All 105 Prompt Stems (GUARD-05)**: Static inspection verifies `src/pdl_taskmaster/` contains zero benchmark IDs, prompt stems, or problem-class tags derived from `prompts/CATALOGUE_MANIFEST.jsonl`. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-05); `TARGET_ARCHITECTURE.md:40, 292` | `tests/test_harness_anti_overfitting.py:171-241` | `test_benchmark_contamination_scan` | **Verified** | Passes cleanly across all production files. |
| **CLM-19** | **REPL Bracketed Paste & Empty Enter Disambiguation**: Typed command after an empty Enter is never falsely classified as a paste; multiline inputs via bracketed paste or console burst are detected cleanly. | PR commit `c33ed3fd`; `tests/test_repl_paste.py` | `repl.py:1180-1320` | `tests/test_repl_paste.py:13-136` | **Verified** | Tested on both Windows (`msvcrt.kbhit`) and POSIX (`select.select`). |
| **CLM-20** | **Win32 Reserved Device Name Sanitization in REPL**: Session names matching Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`, trailing dots/spaces) are rejected fail-closed with `ValueError`. | PR commit `fd0c74c4`; `repl.py:80-100` | `repl.py:80-100` (`sanitize_session_name`) | `tests/test_repl_integration.py:249-262` | **Verified** | Parameterized unit tests confirm fail-closed rejection. |
| **CLM-21** | **Active Session Transcript Preservation on Pruning**: `/sessions prune` command never deletes the active session whose transcript file is open, preventing WinError 32 crashes on Windows. | PR commit `fd0c74c4`; `repl.py:720-750` | `repl.py:720-750` | `tests/test_repl_integration.py:235-247` | **Verified** | Integration test confirms active session remains untouched. |
| **CLM-22** | **Multi-tier Scaled Verification Repairs with Closed Error Registry**: Verification repairs scale with routed tier (1 for MINIMAL/STANDARD, 2 for HEAVY_COMPUTE); attempts running no code do not consume a repair; feedback comes from closed `error_registry.py`. | `TARGET_ARCHITECTURE.md:266-267`; `error_registry.py` | `error_registry.py:1-120`; `session_engine.py:1360-1430` | `tests/test_error_registry.py`; `tests/test_execution_profile.py` | **Verified** | Unmeasured repair preservation and registry codes verified. |
| **CLM-23** | **Evaluation Plane Local Browser Viewer**: Read-only, localhost-only viewer (`viewer/server.py`) operates strictly in evaluation plane, browsing catalogue runs and sessions with zero harness imports. | `README.md:39-44`; `LEAN_BUILD_PLAN.md:35-56` | `viewer/server.py`; `viewer/index.html` | `tests/test_viewer.py:1-249` | **Verified** | Tested via mock catalogue trees and endpoint tests. |
| **CLM-24** | **Dual Plane Architecture & Boundary Separation**: Harness plane (`src/pdl_taskmaster/`) never reads `prompts/` or solutions; evaluation plane (`run_catalogue.py`, `graders.py`) drives tests and scores deliverables. | `TARGET_ARCHITECTURE.md:33-42`; `REVIEWER.md:7-10` | `src/pdl_taskmaster/`; `graders.py:1-622`; `run_catalogue.py` | `tests/test_harness_anti_overfitting.py:202-241` | **Verified** | Mechanical boundary validated by static contamination scan. |

---

## 3. Architectural & ADR Conformance Audit

### 3.1 ADR-0018: Pydantic SSOT & Elimination of Regex Heuristics
- **Intent**: Eliminate heuristic regular expressions in domain detection, witness extraction, and wire verification, enforcing Pydantic models as the Single Source of Truth.
- **Verification Findings**:
  - **Domain Detection**: `OutputVerifier.detect_domain` does not use regular expressions. Domain dispatch occurs strictly via explicit dictionary key lookup or `ProblemDomain` enum match.
  - **Witness Extraction**: `src/pdl_taskmaster/runtime/text_blocks.py` replaces regex scraping with exact string operations (`startswith("WITNESS:")`, `startswith("```")`).
  - **Witness Validation**: `wire_payloads.WitnessPayload` is defined as an `Annotated[Union[PositiveWitness, NegativeWitness], Field(discriminator="polarity")]`. Negative witnesses strictly enforce `nodes_explored: PositiveInt` (>0) and `search_exhausted=True` under search basis, or a non-empty `argument` under proof basis.
  - **Discrepancy 1**: `OutputVerifier` itself is NOT a Pydantic model; it is a standard Python dispatcher class.
  - **Discrepancy 2**: `wire_payloads.py` does NOT implement alias coercion (`Field(alias=...)` or `AliasChoices`).
  - **Discrepancy 3**: ADR-0018 §3.3's `contradictory_reconciliation` check is missing in `result_ir.py`.
  - **Discrepancy 4**: ADR-0018 §3.1 lists `PARTITION_SUM_TRIPLES`, `EXACT_COVER`, `SUBSET_SUM` in `ProblemDomain`, but `checkers/base.py` only defines `GENERAL = "general"` (domain-specific checkers were stripped to satisfy GUARD-02).

### 3.2 ADR-0019: Headless Automation & Exit Codes
- **Intent**: Headless runs must communicate execution outcomes via deterministic process exit codes:
  - `0`: `CLOSED_SUCCESS` (deliverable verified) or published boundary refusal (`closure=REFUSED`).
  - `1`: `CLOSED_CANCELLED` / fail-closed error / verification failure after repair.
  - `2`: `UNCONFIRMED_GATE` (execution stalled at review gate).
  - `3`: `WAITING_INPUT` (legitimate pause awaiting external input).
- **Verification Findings**:
  - `src/pdl_taskmaster/host/repl.py:1472-1507` and `cli.py:113-125` implement these exit codes cleanly.
  - Non-interactive runs paused at `WAITING_INPUT` exit code 3 (`tests/test_repl_integration.py:127-163`).
  - Non-interactive runs halting at review gates exit code 2 (`tests/test_repl_integration.py:103-111`).
  - Boundary refusals publish `PROTOCOL_REFUSED` and exit code 0 (`tests/test_refusal_closure.py`).
  - **Discrepancy**: `repl.py:425, 1475-1476` introduces `EXIT_HARNESS_ERROR = 4` for harness/provider errors. This 5th code is not documented in ADR-0019 or `TARGET_ARCHITECTURE.md`. Furthermore, while code 1 is implemented in `repl.py:1492`, no test in `tests/test_repl_integration.py` verifies process exit code 1 end-to-end.

### 3.3 ADR-0020 & GUARD-02: System 1 Boundary Refusal
- **Intent**: Intercept out-of-scope, network-dependent, or post-cutoff tasks in Phase 0 using System 1 (`ActivationRouteRecipe`) conditioned on environment state variables (`PDLT_SANDBOX_NETWORK`, `PDLT_POLICY_SCOPE`, `PDLT_KNOWLEDGE_CUTOFF`), refusing fail-closed as `closure=REFUSED` (exit 0) before invoking System 2, with zero benchmark token regex traps.
- **Verification Findings**:
  - `ActivationRouteRecipe` evaluates environment state as recipe fields.
  - Phase 0 executes via `SessionEngine._s1_activation` on user requests.
  - Refusals publish standardized boundary notices and set `refused=True`, closing turn cleanly.
  - All hardcoded regex fast-paths (`classify_text_deterministic`, `frostbitedb`) were removed in commit `addf0fec` to satisfy GUARD-02.
  - Verified by `tests/test_phase0_routing.py`, `tests/test_refusal_closure.py`, and `tests/test_harness_anti_overfitting.py`.

### 3.4 ADR-0021: Session-Scoped Confinement
- **Intent**: Build `ExecutionSandbox` once per session in `SessionEngine.__init__`, execute code in ephemeral per-run directories under `<tempdir>/pdlt-sandboxes/<sid>/work/`, isolate secrets via allowlist, confine filesystem access using OS-native mechanisms (Landlock, Seatbelt, AppContainer) with audit hook defense-in-depth, and sweep stale roots.
- **Verification Findings**:
  - Lifecycle is correctly wired: `SessionEngine.__init__` instantiates the sandbox; `PDLtHost.close()` and `SessionEngine.close()` release native state; `sandbox.sweep_stale_roots()` cleans dead owner directories.
  - Windows AppContainer integration uses `winproc` launcher and Job Objects.
  - **Discrepancy / Test Failure**: On Windows, AppContainer prevents `_ctypes.pyd` DLL initialization, causing `tests/test_confinement.py::test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]` to fail. In addition, `test_sandbox_blocks_startfile_on_windows` fails due to `NotImplementedError`.

### 3.5 GUARD-01 through GUARD-05 Anti-Overfitting Compliance
- **GUARD-01 (No Synthetic Approaches)**: Confirmed. `session_engine._draft_plan` binds `CARRIED_APPROACH_SOURCES` strictly to user-originated `carried` list. No solver advice or strategy names are injected.
- **GUARD-02 (No Benchmark Token Targeting)**: Confirmed. No benchmark prompt IDs (`01-01`..`15-07`), prompt stems, or problem-class tags appear in `src/pdl_taskmaster/`.
- **GUARD-03 (First-Class Symbolic Reasoning)**: Confirmed. Analytical proofs and derivations are accepted by `plan_soundness.py` and `result_ir.py` without code keywords or fabricated numerical values.
- **GUARD-04 (Zero Algorithmic Coaching)**: Confirmed. Plan gates check only PDL syntax rules (PDL-05/06/08, PLAN-10); worker prompt instructions do not mandate code or name algorithms.
- **GUARD-05 (Automated Integrity Gate)**: Confirmed. `pytest tests/test_harness_anti_overfitting.py` executes 15 tests in 3.29s with 100% pass rate.

---

## 4. Lean Build & Architecture Assessment (Requirement R4)

### 4.1 Unnecessary Coupling and Cyclic Dependencies
1. **Cyclic Import Between `sandbox.py` and `backends.py`**:
   - `src/pdl_taskmaster/verification/sandbox.py:21-28` imports `select_backend`, `RunLimits`, etc., from `confinement.backends`.
   - `src/pdl_taskmaster/verification/confinement/backends.py:140` performs a lazy runtime import: `from pdl_taskmaster.verification import sandbox as _sb`.
   - **Impact**: Hidden cyclic coupling between the high-level sandbox facade and lower-level confinement backends.
2. **Coupling Between `session_engine.py` and Sandbox Internals**:
   - `session_engine.py:609` directly inspects internal sandbox state via `self.sandbox.decision_state()["execution_environment"]` to build System 1 recipe requests.
   - **Impact**: Changes to sandbox internal representation directly risk breaking session routing.

### 4.2 Abstraction Leaks & Monolithic Classes
1. **1,516-Line Monolithic `repl.py`**:
   - `repl.py` conflates command-line parsing, terminal formatting, bracketed paste detection, Windows `msvcrt` console hooks, session management on disk (`session.json`), dev-mode handlers, watchdog timers, and process exit code resolution.
   - **Impact**: High cognitive load, brittle maintenance, and difficulty isolating test scenarios.
2. **1,965-Line Monolithic `session_engine.py`**:
   - Orchestrates state machine transitions, System 1 dispatch, System 2 compilation, quarantine sanitization, Result IR schema validation, sandbox script execution, repair accounting, and telemetry event logging in a single file.

### 4.3 Duplicated Logic
1. **Fenced Code Block Extraction**:
   - Implemented in `src/pdl_taskmaster/runtime/text_blocks.py:16-38` as `fenced_blocks(text, languages)`.
   - Re-implemented in `src/pdl_taskmaster/runtime/session_engine.py:182-210` as `_python_blocks(body)` (which also handles AST module parsing).
   - Re-exported/wrapped in `graders.py:43-48`.

### 4.4 Dead or Unreachable Code Paths
1. **Unused `import re` Statements**:
   - `src/pdl_taskmaster/runtime/result_ir.py:21`: `import re` is completely unused.
   - `src/pdl_taskmaster/runtime/operation_bridge.py:8`: `import re` is completely unused.
2. **Ineffectual Matching in `OutputVerifier.detect_domain`**:
   - `output_verifier.py:51-58`:
     ```python
     text = " ".join(str(v) for v in context_or_text.values())
     direct = ProblemDomain.from_string(text)
     ```
     Because `ProblemDomain` only contains `GENERAL = "general"`, flattening dictionary values into a single string to test against `from_string` can only ever return `"general"` or `None`.

### 4.5 Inconsistencies Between Architecture Documentation and Code
1. **Version Divergence**: `TARGET_ARCHITECTURE.md` proclaims `v2.7.0` (Lean Build), but `src/pdl_taskmaster/__init__.py:3` declares `__version__ = "2.6.0rc1"`, and `pdlt --version` outputs `pdl-taskmaster 2.6.0rc1`.
2. **ADR-0018 Specification vs Code**: ADR-0018 §3.3 specifies `contradictory_reconciliation` validation, which is completely absent from `result_ir.py`. ADR-0018 §3.1 specifies multi-domain `ProblemDomain` enum members, which were stripped from `checkers/base.py`.
3. **ADR-0019 Exit Code 4**: `repl.py` implements exit code 4 (`EXIT_HARNESS_ERROR`), but ADR-0019, `TARGET_ARCHITECTURE.md`, and `README.md` only document codes 0, 1, 2, and 3.
4. **Outdated Lineage in `ARCHITECTURE.md`**: `ARCHITECTURE.md:3` lists lineage `v2.0.0 -> v2.3.0 -> v2.4.0` with references to `Laya / Jev 1.13 Decisions API`, conflicting with `TARGET_ARCHITECTURE.md` (`v2.6.0 -> v2.7.0`).

### 4.6 Hidden Assumptions & Platform Fragility
1. **Windows AppContainer DLL Loading Assumption**:
   - Tests assume Python inside Windows AppContainer can load `_ctypes.pyd` when the audit hook is detached. In reality, AppContainer security policy blocks `_ctypes.pyd` initialization, causing an unhandled `ImportError`.
2. **Windows `os.startfile` Implementation Assumption**:
   - `test_sandbox_blocks_startfile_on_windows` assumes `os.startfile` triggers the Python audit hook and raises `PermissionError`. In the sandbox interpreter environment, `os.startfile` raises `NotImplementedError: startfile not available on this platform`.

---

## 5. Actionable Findings by Severity

### [High] Architectural & Test Failures

#### FINDING-01: Windows AppContainer `_ctypes` DLL Initialization Failure Under Native Confinement
- **File**: `tests/test_confinement.py:509-526`
- **Location**: `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]`
- **Problem Statement**:
  The test asserts that when the in-process audit hook is disabled, native `ctypes` loads successfully so that native filesystem confinement can be verified. On Windows, executing Python under the native AppContainer backend results in:
  ```
  ImportError: DLL load failed while importing _ctypes: A dynamic link library (DLL) initialization routine failed.
  ```
  The test fails with `AssertionError: assert False where False = SandboxResult(...).success`.
- **Severity Rationale**: High. The test suite fails out-of-the-box on Windows in development mode, breaking CI guarantees.
- **Code Evidence**:
  ```python
  # tests/test_confinement.py:523-525
  with _open((mode, False)) as sandbox:
      result = sandbox.run_code(code)
  assert result.success, result.stderr  # FAILS on Windows: result.success is False
  ```

#### FINDING-02: Windows Sandbox `os.startfile` Raises `NotImplementedError` Instead of `PermissionError`
- **File**: `tests/test_sandbox.py:202-206`
- **Location**: `test_sandbox_blocks_startfile_on_windows`
- **Problem Statement**:
  The test asserts that executing `os.startfile('cmd.exe')` inside `ExecutionSandbox` raises `PermissionError` via the Python audit hook. In reality, `os.startfile` raises:
  ```
  NotImplementedError: startfile not available on this platform
  ```
  The assertion `assert "PermissionError" in result.stderr` fails.
- **Severity Rationale**: High. Direct test failure in `tests/test_sandbox.py` on Windows platforms.
- **Code Evidence**:
  ```python
  # tests/test_sandbox.py:203-206
  def test_sandbox_blocks_startfile_on_windows():
      result = ExecutionSandbox().run_code("import os\nos.startfile('cmd.exe')")
      assert not result.success
      assert "PermissionError" in result.stderr, result.stderr  # FAILS: contains NotImplementedError
  ```

---

### [Medium] Specification & Design Inconsistencies

#### FINDING-03: Missing Implementation of ADR-0018 §3.3 `contradictory_reconciliation`
- **Files**: `docs/adr/0018-elimination-of-regex-heuristics-in-verification-and-reconciliation-integrity.md:68-72`, `src/pdl_taskmaster/runtime/result_ir.py:180-275`
- **Problem Statement**:
  ADR-0018 §3.3 mandates that if a witness has `polarity == "negative"`, any requirement with existential instructions (`GENERATE`, `PROVIDE`, `CONSTRUCT`, etc.) marked `"satisfied"` must be rejected as `contradictory_reconciliation`. `validate_result_ir` in `result_ir.py` contains zero logic for this invariant.
- **Severity Rationale**: Medium. A documented normative decision record claims this mechanical invariant protects against false greens on negative witnesses, but the code does not enforce it.
- **Code Evidence**:
  ```markdown
  # docs/adr/0018 §3.3
  If a requirement contains existential or generative instructions (GENERATE, PROVIDE, CONSTRUCT, FIND, EXAMPLE), claiming "status": "satisfied" on a negative witness is rejected as a semantic contradiction (contradictory_reconciliation).
  ```

#### FINDING-04: Undocumented Headless Exit Code 4 (`EXIT_HARNESS_ERROR`)
- **Files**: `src/pdl_taskmaster/host/repl.py:424-425, 1472-1476`, `docs/adr/0019-headless-waiting-input-exit-and-wire-tolerance.md`, `TARGET_ARCHITECTURE.md:171-179`
- **Problem Statement**:
  `repl.py` defines and returns `EXIT_HARNESS_ERROR = 4` when execution terminates due to harness or provider errors. However, ADR-0019 and `TARGET_ARCHITECTURE.md` only define codes 0, 1, 2, and 3.
- **Severity Rationale**: Medium. Evaluator runners and external tooling integrating with PDLt exit codes face an undocumented exit code.
- **Code Evidence**:
  ```python
  # src/pdl_taskmaster/host/repl.py:424-425, 1475-1476
  EXIT_HARNESS_ERROR = 4
  ...
  print(f"[headless halt] Harness error (...). Exiting (code {EXIT_HARNESS_ERROR}).", file=sys.stderr, flush=True)
  return EXIT_HARNESS_ERROR
  ```

#### FINDING-05: Circular Module Dependency Between `sandbox.py` and `backends.py`
- **Files**: `src/pdl_taskmaster/verification/sandbox.py:21-28`, `src/pdl_taskmaster/verification/confinement/backends.py:140`
- **Problem Statement**:
  `sandbox.py` imports backend functions and types from `backends.py` at module top-level. `backends.py:140` performs a lazy runtime import `from pdl_taskmaster.verification import sandbox as _sb` inside `launch()` to access Win32 kernel structures.
- **Severity Rationale**: Medium. Circular dependencies obscure module hierarchy and impede refactoring.
- **Code Evidence**:
  ```python
  # src/pdl_taskmaster/verification/confinement/backends.py:140
  from pdl_taskmaster.verification import sandbox as _sb
  ```

---

### [Low] Code Cleanliness & Version Metadata

#### FINDING-06: Dead and Unused Imports in Runtime Modules
- **Files**: `src/pdl_taskmaster/runtime/result_ir.py:21`, `src/pdl_taskmaster/runtime/operation_bridge.py:8`
- **Problem Statement**:
  `import re` remains at the top of `result_ir.py` and `operation_bridge.py` even though neither module calls `re`.
- **Severity Rationale**: Low. Unused imports left over from regex-elimination refactoring.
- **Code Evidence**:
  ```python
  # src/pdl_taskmaster/runtime/result_ir.py:21
  import re  # Never referenced in file
  ```

#### FINDING-07: Package Version Inconsistency (`2.6.0rc1` vs `v2.7.0`)
- **Files**: `src/pdl_taskmaster/__init__.py:3`, `pyproject.toml:46`, `TARGET_ARCHITECTURE.md:1-5`
- **Problem Statement**:
  `TARGET_ARCHITECTURE.md` titles the architecture as `PDL Taskmaster v2.7.0 — Lean Build`. However, `src/pdl_taskmaster/__init__.py` declares `__version__ = "2.6.0rc1"`.
- **Severity Rationale**: Low. Version metadata desynchronization between documentation and build metadata.
- **Code Evidence**:
  ```python
  # src/pdl_taskmaster/__init__.py:3
  __version__ = "2.6.0rc1"
  ```

---

### [Informational] Architectural Observations

#### FINDING-08: Test Dependency on Sibling Repository Path
- **File**: `tests/test_repl_integration.py:22-24`
- **Problem Statement**:
  `_resolve_fixture_file()` looks for `ROOT.parent / "PDL-Standard-Archive" / "fixtures-r4-recorded-worker" / "recorded-cases.json"` as a fallback if local fixtures are missing.
- **Severity Rationale**: Informational. While harmless if local fixtures exist, referencing unversioned sibling directories outside the repo root can introduce non-deterministic test behavior.
- **Code Evidence**:
  ```python
  # tests/test_repl_integration.py:22-24
  archive = ROOT.parent / "PDL-Standard-Archive" / "fixtures-r4-recorded-worker" / "recorded-cases.json"
  if archive.is_file():
      return archive
  ```

---

## 6. Verification and Independent Reproduction

To independently reproduce all observations in this audit, execute the following commands from the repository root (`c:\Users\USER\Desktop\Frameworks\PDLt-Test`):

1. **Verify Anti-Overfitting & Guardrail Suite (GUARD-01 through GUARD-05)**:
   ```bash
   pytest tests/test_harness_anti_overfitting.py -v
   ```
   *Expected Result*: 15 passed in ~3.3s with 0 warnings, failures, or skips.

2. **Verify REPL Integration, Bracketed Paste, and Dev Mode**:
   ```bash
   pytest tests/test_repl_integration.py tests/test_repl_paste.py tests/test_dev_mode.py -v
   ```
   *Expected Result*: 37 passed, 3 skipped on Windows.

3. **Reproduce the 2 Windows Platform Test Failures**:
   ```bash
   pytest tests/test_confinement.py -k "test_escape_native_code_cannot_read_the_secret_without_the_audit_hook" -v
   pytest tests/test_sandbox.py -k "test_sandbox_blocks_startfile_on_windows" -v
   ```
   *Expected Result*: Both tests fail with the exact stack traces documented in Findings 01 and 02.

4. **Verify Dry-Run Catalogue Manifest Parsing**:
   ```bash
   python run_catalogue.py --dry-run
   ```
   *Expected Result*: Parses all 105 prompts cleanly, displaying 21 VERIFIED prompts.

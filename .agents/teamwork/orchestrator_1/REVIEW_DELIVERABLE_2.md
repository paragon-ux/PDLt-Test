# Comprehensive Review Deliverable: Pull Request #1
**Pull Request**: #1 — "Add PDL Taskmaster Lean Build: Full CLI REPL & Comprehensive Architecture"  
**Repository**: `paragon-ux/PDLt-Test` (https://github.com/paragon-ux/PDLt-Test/pull/1)  
**Review Target**: Full Codebase, Architecture Specifications, REPL Implementation, Test Suites, and Live Execution Behavior  
**Date of Audit**: 2026-10-02  
**Revision**: 3 — Live and Windows verification (2026-10-02)  
**Review Team**: Project Orchestrator & Multi-Track Specialist Review Team  

> **Revision 3 summary.** Open gates 1 and 2 from Revision 2 are now closed. All verification ran on `068e0a0c` on a Windows 11 host with Python 3.11.9. **(1) Live dev-mode REPL:** with `openrouter.ai` reachable (HTTP 200) and `OPENROUTER_API_KEY` set, "Compute the product of 7 and 8" with two `/confirm`s went `PROMPT_REVIEW → PLAN_REVIEW → CLOSED_SUCCESS`, gave witness `product: 56`, and exited 0. The same task with `/cancel` at `PROMPT_REVIEW` printed `Cancelled.` and reached `CLOSED_CANCELLED`, with no `unknown command`, then `[protocol closed]` and exit 1. **(2) Windows:** the remediated tests for fixes 4 and 5 pass on Windows. The full suite gives 550 passed, 44 skipped, 0 failed, and the anti-overfitting suite gives 15/15. The live run also turned up one new low-severity finding, **FINDING-19**: in headless mode without `--exit-on-close`, piped lines left over after closure start a new protocol. No code was changed in Revision 3. Revision 2 text is kept below, with updated status lines marked *Rev. 3*.
>
> **Revision 2 summary.** All 5 blocking items are fixed in commit `068e0a0c` on branch `claude/exciting-albattani-n2s3x8`. That branch is the PR head (`75b7dcbb`, branch `claude/compassionate-carson-kfafta`) plus one commit, and it has not yet been merged into the PR branch. Two gates are still open: **(1)** the live dev-mode REPL run that `AGENTS.md` requires (egress to `openrouter.ai` was blocked in the remediation session; a manual run is in progress), and **(2)** confirming fixes 4 and 5 on a Windows host. Revision 2 also corrects cross-reference numbering in §B, refines FINDING-07, and marks which open findings were re-verified. Line references in §B–§D are to the PR head `75b7dcbb` unless they say otherwise.

---

## A. Executive Summary

Pull Request #1 is a foundational greenfield-to-production implementation. It adds the complete PDL Taskmaster host runtime, CLI REPL, dual-plane execution architecture, and evaluation harness to `paragon-ux/PDLt-Test` (32,072 additions across 223 files relative to the `origin/main` merge-base `ddbd3be1`).

### Key Strengths & Achievements:
1. **Anti-Overfitting & Referee Neutrality (GUARD-01 through GUARD-05)**: The mandatory anti-overfitting suite (`pytest tests/test_harness_anti_overfitting.py`) passes 15/15 with 0 warnings, 0 failures, and 0 skips (3.77s at audit; 1.10s on Linux after remediation). Static audits found no algorithmic coaching keywords (e.g. MRV, DLX, backtracking), no hardcoded benchmark tokens (`frostbitedb`), no carried approach crutches, and matching SHA-256 contract manifests across the repository and bundled copies.
2. **Autonomous Dual-Plane Architecture & Headless Governance (ADR-0019, GUARD-03)**: The host cleanly separates protocol enforcement (`SessionEngine`, `MechanicalController`) from presentation (`repl.py`, `app.py`). Headless runs use fixed exit codes: `0` for success or a published refusal, `1` for cancellation, `2` for an unconfirmed review gate, `3` for waiting on input, and `130` for SIGINT. Reasoning deliverables (analytical proofs and derivations) are fully supported without forcing fabricated Python scripts.
3. **Session-Scoped OS Confinement (ADR-0021)**: The execution sandbox lives for the length of the session. It passes only allowlisted environment variables, runs user code in ephemeral directories (`work/run-NNNN-*`), and provides confinement backends for Windows (AppContainer), Linux (Landlock), and macOS (Seatbelt), plus an in-process Python audit hook.
4. **Live Interactive & Dev Mode Functionality**: At audit time, a live end-to-end task ran in dev mode with an active `OPENROUTER_API_KEY` against `openai/gpt-oss-120b`. The session passed through System 1 activation, profile prediction, the prompt review gate, the plan review gate, autonomous AppContainer sandbox execution, witness extraction (`product: 56`), and Result IR verification, then closed cleanly (`CLOSED_SUCCESS`) with exit code 0. *(This live run predates the remediation commit. Rev. 3: it was re-run live on `068e0a0c` on Windows with the same result: `CLOSED_SUCCESS`, `product: 56`, exit 0. See §H.)*

### Critical Findings & Required Remediation:
The audit found **5 High-severity defects**: 3 in REPL interaction logic and 2 platform-specific test failures on Windows. **Revision 2: all 5 are remediated in `068e0a0c` (see §H).**
1. **Broken `/cancel` Review Command (`repl.py:1396-1405`)** — ✅ *Fixed.* `SessionEngine` handles `/cancel` at review gates, but the review-command whitelist in `repl.py` left it out, so `/cancel` was rejected as an `unknown command`.
2. **Premature Paste Truncation on Blank Lines (`repl.py:572-573`)** — ✅ *Fixed (behavior change).* `/paste` mode stopped at the first blank line once anything was buffered, silently dropping the rest of multi-line code or prompts.
3. **Windows Console Burst Blocking Hang (`repl.py:525-526`)** — ✅ *Fixed.* Windows burst detection called the blocking `input()` inside `while msvcrt.kbhit()`, so the REPL hung on fast typing or on a paste without a trailing newline until the user pressed Enter again.
4. **Windows AppContainer `_ctypes` DLL Initialization Failure (`test_confinement.py:525`)** — ✅ *Fixed; confirmed on Windows (Rev. 3).* The native escape test assumed `_ctypes.pyd` loads under AppContainer with the audit hook off. Windows security policy blocks the DLL's initialization, so the test assertion failed.
5. **Windows Sandbox `os.startfile` Exception Divergence (`test_sandbox.py:206`)** — ✅ *Fixed; confirmed on Windows (Rev. 3).* Inside AppContainer, `os.startfile('cmd.exe')` raises `NotImplementedError` instead of the audit hook's `PermissionError`.

The audit also found several medium-severity divergences from the architecture and specification: the missing ADR-0018 §3.3 `contradictory_reconciliation` check, the undocumented headless exit code 4, a closed transcript handle left behind by `/transcript`, and operational settings lost on session or worker switches. These remain open as follow-ups.

---

## B. Complete REPL Functionality Audit

Each of the 14 REPL lifecycle areas was traced end to end through `src/pdl_taskmaster/host/repl.py`, `app.py`, `cli.py`, and the engine modules underneath them. *(Revision 2: cross-references in the last column were corrected to match the numbering in §D, and verdicts were updated after remediation.)*

| Dimension | Description & Traced Implementation | Verdict | Key Observations & Identified Line References |
|---|---|---|---|
| **1. Startup and Initialization** | Environment UTF-8 setup (`cli.py:12-19`, `repl.py:995-999`), repo root resolution (`repl.py:16-29`), session storage resolution (`repl.py:36-46`), banner display (`repl.py:1084-1090`), session selection menu (`repl.py:198-227`), session restoration fallback (`app.py:108-113`), confinement announcement (`repl.py:306-324`), initial prompt injection (`repl.py:1107-1116`). | **Verified** | Initialization is sound. `sanitize_session_name()` (`repl.py:94-121`) rejects Windows reserved names (`CON`, `NUL`, etc.) and fails closed. Corrupted sessions fall back cleanly to a fresh state. |
| **2. Command Parsing and Dispatch** | Input is read by `_read_repl_input()` and split with `line.split(maxsplit=1)` (`repl.py:1164`). Top-level slash commands are handled by the host; review commands go to `SessionEngine.handle_user_message()` (`repl.py:1396-1405`). Plain text is treated as a task prompt or as conversation at a review gate. | **Defective (High) → Remediated** | **FINDING-01**: `/cancel` is handled in `session_engine.py:1917` but was missing from the whitelist in `repl.py:1396-1405`. *Fixed:* there is now one shared `REVIEW_COMMANDS` set (`repl.py:477` @ `068e0a0c`). The lack of `shlex` parsing (`repl.py:602, 1164`) leaves literal quotes in arguments (**FINDING-12**, open). |
| **3. Argument and Option Handling** | The CLI parser defines 36 flags (`repl.py:805-992`). At runtime, `/dev set` changes provider order, fallback allowance, model by operation, reasoning effort, timeout, token limits, and `exit_on_close` (`repl.py:630-767`). | **Partially Verified (Medium)** | **FINDING-07** (refined in Rev. 2): settings changed on the worker survive `/new` and `/resume`, but are lost on `/worker` because it rebuilds the worker from the CLI `args`. Runtime-level settings (`exit_on_close`) reset on every switch. `/sandbox` sets the Codex worker's sandbox; there is no command for the host execution sandbox. |
| **4. Interactive Input/Output Behavior** | Bracketed paste mode (`\x1b[?2004h`, `repl.py:485-516`), Windows console burst detection (`msvcrt.kbhit()`, `repl.py:522-527`), POSIX burst detection (`select.select()`, `repl.py:528-534`), empty-Enter disambiguation (commit `c33ed3fd`, `repl.py:538-541`), multi-line `/paste` mode (`repl.py:558-575`), backslash continuation (`repl.py:578-590`), deliverable formatting (`repl.py:1434`). | **Defective (High) → Remediated** | **FINDING-02**: `/paste` stopped on a blank line once `lines_buf` was non-empty. *Fixed:* only `EOF` ends it. **FINDING-03**: `while msvcrt.kbhit(): lines.append(input())` could hang. *Fixed:* keys are read without blocking via `_drain_console_burst_win32()` (`repl.py:480` @ `068e0a0c`). **FINDING-08** (open): typing `/confirm` at the paste confirmation adds `\n/confirm` to the prompt. |
| **5. Command Execution & Orchestration** | Protocol entry point injection (`app.py:174-180`), observed turn dispatch (`observed_session.py:82-166`), controller stage routing (`session_engine.py:1830-1965`), review gate handling, autonomous sandbox execution, substantive verification, and a bounded repair loop. | **Verified** | Orchestration across both planes is robust. Telemetry records timing, token usage, and SHA-256 hashes, and observer failures never reach the protocol plane. |
| **6. State and Context Persistence** | Lazy session pointer `session.json` written after the first turn (`repl.py:161-179`), per-turn directories (`turns/turn_<n>`) with full state snapshots, session restoration via `SessionEngine.restore()`, sequential transcript logging (`transcript.log`). | **Partially Verified (Medium)** | **FINDING-06** (open, re-verified Rev. 2): `/transcript <path>` closes `runtime.transcript` before checking the new path (`repl.py:1297-1303` @ `068e0a0c`). An invalid path raises an unhandled `OSError` and leaves transcript logging permanently broken. |
| **7. Success, Failure, and Partial-Failure Paths** | Turn exception boundary (`repl.py:1408-1428`), clean recovery from `KeyboardInterrupt`, one-line error formatting (`_one_line_error()`, `repl.py:428-451`), provider error categories, return to the interactive prompt. | **Verified** | Errors don't crash the interactive session: the console shows a short one-line message and the full error goes to the transcript. |
| **8. Invalid Input and Unknown Commands** | Empty input is ignored (`repl.py:1120`), an empty prompt at a review gate gets a helpful reminder (`session_engine.py:1891-1897`), session names are sanitized (`repl.py:94-121`), and provider typos get `difflib` suggestions (`repl.py:692-770`). | **Verified** | Unknown commands print `unknown command: {cmd}`. Fuzzy-match suggestions for general slash commands would help. |
| **9. Help, Usage, and Command Introspection** | `/help` lists 20 commands (`repl.py:1135-1159`), `/dev help` lists dev options (`repl.py:606-623`), `/status` reports runtime state, `/dev status` prints detailed JSON telemetry, `/dev diagnose` runs a 4-point self-test, and `/session` and `/sessions` list session metadata. | **Verified** | All documented commands are implemented and work. *Rev. 2:* `/help` now lists `/stop \| /cancel`. |
| **10. Exit/Quit Behavior and Cleanup** | Interactive exit via `/quit`, EOF, or `KeyboardInterrupt`. Auto-exit via `runtime.exit_on_close` when the protocol closes. The `finally:` block (`repl.py:1463-1468`) turns off bracketed paste, closes transcripts, shuts down `ExecutionSandbox`, and flushes `JsonlSink`. Session pruning keeps the active session directory (`repl.py:1371-1372`). | **Verified** | Resources are released cleanly with no leaks. Keeping the active session's transcript avoids the Windows WinError 32 file-lock crash. |
| **11. Error Propagation, Reporting, & Recovery** | Structured error categories (`OUTPUT_MALFORMED`, `OUTPUT_LIMIT_REACHED`, `PROVIDER_REJECTED_REQUEST`), console messages capped at 240 characters, exceptions from the telemetry sink contained (`observed_session.py:89-166`). | **Verified** | Telemetry and error boundaries work as intended. Slash-command handlers (`repl.py:1163-1405`) run outside the try/except (**FINDING-13**, open). |
| **12. Integration with Underlying Components** | Protocol work is delegated strictly to `SessionEngine`, state is gated by `MechanicalController`, code runs in `ExecutionSandbox`, and provider calls are stateless (`ApiWorker`, `CodexWorker`). | **Verified** | Clean separation, consistent with ADR-0018, ADR-0020, and ADR-0021. |
| **13. Non-Interactive and CLI Compatibility** | Non-interactive mode (`--non-interactive`, piped stdin, `_is_interactive()` `repl.py:192-196`). Automated initial prompts (`--prompt`, `--prompt-file`). Headless exit codes (`0`, `1`, `2`, `3`, `4`, `130`) per ADR-0019 (`repl.py:1472-1507`). A 20-second faulthandler watchdog (`_arm_exit_watchdog()`). | **Verified** | Confirmed by live CLI runs and automated tests. *Rev. 2:* exit code 1 now has an end-to-end subprocess test (`/stop` and `/cancel`). Exit code 4 is still undocumented (**FINDING-10**). *Rev. 3:* exit codes 0 and 1 were confirmed live. Without `--exit-on-close`, piped lines left over after closure start a new protocol (**FINDING-19**, open). |
| **14. Extensibility & Command Architecture** | A 240-line `if/elif` chain in `main()` (`repl.py:1163-1405`) and a 200-line chain in `_handle_dev_command()` (`repl.py:601-802`). | **Suboptimal (Low)** | **FINDING-18** (renumbered in Rev. 2): there is no central command registry or decorator pattern, which makes the code hard to follow and directly caused the `/cancel` omission. The `REVIEW_COMMANDS` set is a first step toward one. |

---

## C. Claims Verification Matrix

As required by R2, 24 distinct claims about the architecture, REPL, and sandbox, drawn from PR #1, `TARGET_ARCHITECTURE.md`, `ARCHITECTURE.md`, and ADR-0001 through ADR-0022, were catalogued and classified. *(Rev. 2: CLM-06, CLM-08, CLM-12 and CLM-19 updated after remediation.)*

| Claim ID | Claim Description | Normative Source | Implementation Evidence | Automated Test Evidence | Assigned Status | Limitations / Discrepancies |
|---|---|---|---|---|---|---|
| **CLM-01** | **Session-Scoped Sandbox Lifecycle**: `ExecutionSandbox` is created once in `SessionEngine.__init__`, tied to the session lifecycle, and shut down via `close()`. | `TARGET_ARCHITECTURE.md:28-31, 192-205`; `ADR-0021:16-17` | `session_engine.py:359, 1595-1598`; `app.py:200-205` | `tests/test_confinement.py:33-46, 128-155` | **Verified** | Cleanly bound to the session lifecycle across host and engine. |
| **CLM-02** | **Ephemeral Run Isolation & Stale Root Sweeping**: Each program runs in its own `work/run-NNNN-*` directory, deleted after the run; roots left by dead owner PIDs are swept at startup. | `TARGET_ARCHITECTURE.md:197, 203-204`; `ADR-0021:17-18` | `sandbox.py:440-525, 861-908` | `tests/test_confinement.py:48-60, 85-106` | **Verified** | Directory isolation confirmed; stale-root sweeping tested. |
| **CLM-03** | **No Regex Heuristics in Verification Dispatch**: `OutputVerifier.detect_domain` never scans problem text with regexes; domain dispatch is strictly typed or falls back to `FallbackChecker`. | `ADR-0018:14-16, 38-47`; `TARGET_ARCHITECTURE.md:104-106` | `output_verifier.py:37-60`; `checkers/fallback.py:18-89` | `tests/test_output_verifier.py`; `tests/test_harness_anti_overfitting.py:263-270` | **Verified** | `OutputVerifier` is a plain class, not a Pydantic model. |
| **CLM-04** | **Discriminated-Union WitnessPayload**: `WitnessPayload` is discriminated on `polarity`. A `NegativeWitness` must have `search_exhausted=True` and `nodes_explored: PositiveInt` for a search basis, or an `argument` for a proof basis. | `ADR-0018:48-65`; `TARGET_ARCHITECTURE.md:100-103` | `wire_payloads.py:330-369`; `result_ir.py:262-273` | `tests/test_pydantic_wire.py`; `tests/test_output_verifier.py` | **Verified** | Enforced at the wire boundary and in Result IR schema validation. |
| **CLM-05** | **Reconciliation Semantic Integrity Invariant**: When `witness.polarity == "negative"`, `validate_result_ir` rejects existential requirements (`GENERATE`, `PROVIDE`) marked `"satisfied"` as `contradictory_reconciliation`. | `ADR-0018:68-72` | `result_ir.py:180-275` (completely absent) | None in test suite | **Contradicted/broken** | The check was dropped from `result_ir.py` during a refactor to avoid keyword regexes under GUARD-02/04, but ADR-0018 was not updated. *Rev. 2: re-confirmed; the string appears only in ADR-0018:71.* |
| **CLM-06** | **Headless Automation Exit Codes (ADR-0019 amended)**: The REPL exits 0 for `CLOSED_SUCCESS` or a published refusal (`closure=REFUSED`), 1 for `CLOSED_CANCELLED`, 2 for an unconfirmed review gate, and 3 for `WAITING_INPUT`. | `ADR-0019:30-44, 61-64`; `TARGET_ARCHITECTURE.md:171-179` | `repl.py:1472-1507`; `cli.py:113-125` | `tests/test_repl_integration.py:103-111, 127-163, 226-234`; `tests/test_refusal_closure.py`; *Rev. 2:* `test_repl_review_cancel_commands_close_cancelled[/stop,/cancel]` | **Partially verified** | Exit codes 0, 1, 2 and 3 are now covered by tests (exit 1 end to end with the recorded worker, Rev. 2). *Rev. 3:* exit codes 0 and 1 were confirmed live against OpenRouter. Exit code 2 was also seen live when piped lines left over after closure restarted the protocol (FINDING-19). Exit code 4 (`EXIT_HARNESS_ERROR`) is implemented but undocumented in ADR-0019, `TARGET_ARCHITECTURE.md` and `AGENTS.md`. |
| **CLM-07** | **System 1 Phase 0 Boundary Refusal**: Tasks outside policy scope (`PDLT_POLICY_SCOPE`), needing network access (`PDLT_SANDBOX_NETWORK`), or after the knowledge cutoff (`PDLT_KNOWLEDGE_CUTOFF`) are caught by System 1, without regex or date matching, and refused fail-closed (exit 0). | `ADR-0020:17-33`; `TARGET_ARCHITECTURE.md:164, 234-242` | `activation_route.py:43-136`; `session_engine.py:593-628, 1134-1138` | `tests/test_phase0_routing.py`; `tests/test_refusal_closure.py`; `tests/test_harness_anti_overfitting.py:61-69, 162-169, 272-282` | **Verified** | Verified with the System 1 client. The advertised `<15ms` depends on a local model rather than network latency. |
| **CLM-08** | **Multi-OS Native Sandbox Backends**: Native OS isolation with no third-party dependencies: Landlock on Linux, Seatbelt on macOS, AppContainer on Windows. | `ADR-0021:19-30`; `TARGET_ARCHITECTURE.md:209-213` | `confinement/backends.py:187-201`; `landlock.py`; `seatbelt.py`; `appcontainer.py` | `tests/test_confinement.py` | **Verified on Windows (Rev. 3)**; Linux/macOS backends per CI | On Windows, `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]` failed because AppContainer blocks `_ctypes.pyd` initialization. *Rev. 2:* that refusal now counts as native containment; the test still requires the secret to be absent. *Rev. 3:* `[native]` passes on Windows 11. Backends for other operating systems skip on the current OS. |
| **CLM-09** | **Opt-in Container Sandbox Mode**: `--sandbox container` provides Docker or Podman containment with a read-only root, no network, and process limits. | `ADR-0021:27, 30`; `TARGET_ARCHITECTURE.md:212` | `confinement/container.py:1-120` | `tests/test_confinement.py:800-880` | **Partially verified** | Unit tests use mocks; integration needs a Docker or Podman daemon. |
| **CLM-10** | **Fail-Closed Sandbox Selection**: When the requested backend can't be applied, no code runs (`sandbox_unavailable:<reason>`). | `ADR-0021:31`; `TARGET_ARCHITECTURE.md:213` | `sandbox.py:850-860`; `confinement/backends.py:173-185` | `tests/test_confinement.py:272-300, 316-340` | **Verified** | Unit tests confirm fail-closed behavior on unsupported systems. |
| **CLM-11** | **Secret Isolation via Environment Allowlist**: The child environment is built strictly from an allowlist (`PATH`, `TEMP`, `TMP`, Windows system keys); API keys never enter the sandbox. | `TARGET_ARCHITECTURE.md:210`; `ADR-0021:7, 19` | `sandbox.py:896`; `confinement/policy.py:20-60` | `tests/test_confinement.py:180-220` | **Verified** | API keys confirmed absent from the child process environment. |
| **CLM-12** | **Python Audit Hook as Defense in Depth**: An in-process `sys.addaudithook` blocks native code loading, unauthorized file access, network calls, signals, and process creation. | `TARGET_ARCHITECTURE.md:214`; `ADR-0021:32` | `sandbox.py:140-265, 876-879` | `tests/test_confinement.py:173-247` | **Verified on Windows (Rev. 3)** | *Rev. 3:* `test_sandbox_blocks_startfile_on_windows` passes on Windows 11. `os.startfile` checks for ShellExecute before raising its audit event, so in AppContainer it fails with `NotImplementedError` and the hook never sees it. *Rev. 2:* the test accepts either `PermissionError` or the exact `NotImplementedError: startfile not available` message. Either way nothing is launched. |
| **CLM-13** | **Deterministic Bytecode Step Budget & Opcode Tracing**: The sandbox installs an opcode trace that counts the Python bytecode instructions user code executes; going over budget ends the process with `step_budget_exceeded=True`. | `TARGET_ARCHITECTURE.md:254-272` | `sandbox.py:350-405, 880-920` | `tests/test_execution_profile.py:200-280`; `tests/test_sandbox.py` | **Verified** | Checked across the MINIMAL (100k), STANDARD (10M), and HEAVY_COMPUTE (100M) budgets. |
| **CLM-14** | **Three-Part System 1 Confidence Gating**: A System 1 decision must meet confidence $P \ge 0.85$, margin $\Delta p \ge 0.40$, and normalized entropy $H(p) \le 0.35$. Flatter distributions fall back cleanly. | `TARGET_ARCHITECTURE.md:232, 268-269`; `ADR-0012` | `sys1/gating.py:1-70` | `tests/test_sys1_foundation.py`; `tests/test_sys1_recipes.py` | **Verified** | Gating math and thresholds confirmed. |
| **CLM-15** | **Reasoning & Symbolic Deliverables Are First-Class (GUARD-03)**: Non-computational tasks, analytical derivations, word problems, and symbolic proofs are accepted as valid deliverables without forcing Python scripts or made-up numbers. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-03); `TARGET_ARCHITECTURE.md:93, 290` | `plan_soundness.py:80-140`; `session_engine.py:1360-1420` | `tests/test_harness_anti_overfitting.py:110-125`; `tests/test_plan_soundness.py` | **Verified** | Covered by `test_plan_soundness_accepts_pure_deduction_plan`. |
| **CLM-16** | **Referee Invariant & No Algorithmic Coaching (GUARD-01, GUARD-04)**: The harness never injects algorithmic search methods (MRV, DLX, backtracking) into prompts, plans, or `CARRIED_APPROACH_SOURCES`. Feedback travels only through operator correction. | `AGENTS.md`; `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-01, 04); `TARGET_ARCHITECTURE.md:23-26` | `session_engine.py:1165-1215`; `api_worker.py:200-280` | `tests/test_harness_anti_overfitting.py:19-40, 127-144, 243-261` | **Verified** | Confirmed by static inspection and the automated anti-overfitting tests. |
| **CLM-17** | **Contract Manifest SHA-256 Sync (GUARD-05)**: Contract files in `contracts/` and the bundled `src/pdl_taskmaster/contracts/` match the `CONTRACT_MANIFEST.json` SHA-256 hashes, with line endings normalized to LF on every OS. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-05); `TARGET_ARCHITECTURE.md:292` | `tests/test_harness_anti_overfitting.py:72-108` | `test_guard05_contract_manifest_sha256_synchronized` | **Verified** | No hash mismatches between the repository and bundled copies. |
| **CLM-18** | **Contamination Scan Across All 105 Prompt Stems (GUARD-05)**: Static inspection confirms `src/pdl_taskmaster/` contains no benchmark IDs, prompt stems, or problem-class tags derived from `prompts/CATALOGUE_MANIFEST.jsonl`. | `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (GUARD-05); `TARGET_ARCHITECTURE.md:40, 292` | `tests/test_harness_anti_overfitting.py:171-241` | `test_benchmark_contamination_scan` | **Verified** | Passes cleanly across all production files. |
| **CLM-19** | **REPL Bracketed Paste & Empty-Enter Disambiguation**: A command typed after an empty Enter is never mistaken for a paste, and multi-line input via bracketed paste or a console burst is detected cleanly. | PR commit `c33ed3fd`; `tests/test_repl_paste.py` | `repl.py:485-575` | `tests/test_repl_paste.py:13-136` | **Verified (Rev. 2: coverage extended)** | Originally the Windows (`msvcrt.kbhit`) tests were skipped on non-Windows CI. *Rev. 2:* they now use a fake `msvcrt` and run on every OS, and a burst without a trailing newline is covered. |
| **CLM-20** | **Windows Reserved Device Name Sanitization in REPL**: Session names matching Windows reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`, trailing dots/spaces) are rejected fail-closed with `ValueError`. | PR commit `fd0c74c4`; `repl.py:80-100` | `repl.py:80-100` (`sanitize_session_name`) | `tests/test_repl_integration.py:249-262` | **Verified** | Parameterized unit tests confirm fail-closed rejection. |
| **CLM-21** | **Active Session Transcript Kept During Pruning**: `/sessions prune` never deletes the active session whose transcript is open, preventing WinError 32 crashes on Windows. | PR commit `fd0c74c4`; `repl.py:720-750` | `repl.py:720-750` | `tests/test_repl_integration.py:235-247` | **Verified** | Integration test confirms the active session is left untouched. |
| **CLM-22** | **Tier-Scaled Verification Repairs with a Closed Error Registry**: The number of verification repairs scales with the routed tier (1 for MINIMAL/STANDARD, 2 for HEAVY_COMPUTE); attempts that run no code don't use up a repair; feedback comes from the closed `error_registry.py`. | `TARGET_ARCHITECTURE.md:266-267`; `error_registry.py` | `error_registry.py:1-120`; `session_engine.py:1360-1430` | `tests/test_error_registry.py`; `tests/test_execution_profile.py` | **Verified** | Repair accounting for runs that execute no code, and the registry codes, both confirmed. |
| **CLM-23** | **Evaluation-Plane Local Browser Viewer**: A read-only, localhost-only viewer (`viewer/server.py`) runs entirely in the evaluation plane, browsing catalogue runs and sessions without importing anything from the harness. | `README.md:39-44`; `LEAN_BUILD_PLAN.md:35-56` | `viewer/server.py`; `viewer/index.html` | `tests/test_viewer.py:1-249` | **Verified** | Tested with mock catalogue trees and endpoint tests. |
| **CLM-24** | **Dual-Plane Architecture & Boundary Separation**: The harness plane (`src/pdl_taskmaster/`) never reads `prompts/` or solutions; the evaluation plane (`run_catalogue.py`, `graders.py`) drives the tests and scores deliverables. | `TARGET_ARCHITECTURE.md:33-42`; `REVIEWER.md:7-10` | `src/pdl_taskmaster/`; `graders.py:1-622`; `run_catalogue.py` | `tests/test_harness_anti_overfitting.py:202-241` | **Verified** | The static contamination scan confirms the boundary. |

---

## D. Findings by Severity

Each finding gives exact file paths, line references, root cause, impact, and code evidence. **Status** lines were added in Rev. 2. "Re-verified" means the claim was checked against the code again during remediation; "Not re-verified" means it stands as originally reported.

### 1. High Severity Findings

#### FINDING-01: Broken Command Dispatch for `/cancel` Review Command
- **Status (Rev. 2)**: ✅ **Fixed in `068e0a0c`.** A shared `REVIEW_COMMANDS = {"/confirm", "/revise", "/stop", "/cancel"}` (`repl.py:477`) now drives both the dispatch and the guard, and `/help` lists `/stop | /cancel`. Regression test: `test_repl_review_cancel_commands_close_cancelled[/cancel]` fails on `75b7dcbb` and passes on `068e0a0c`. The `[/stop]` case passes on both and serves as a control.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:1396-1405`
- **Root Cause**: `session_engine.py:1917` explicitly handles `/cancel`:
  ```python
  if lower in {"/stop", "stop", "/cancel", "cancel"}:
      return self.handle_explicit_review(Intent.CANCEL)
  ```
  But the review command whitelist in `repl.py:1396-1405` allowed only `{"/confirm", "/revise", "/stop"}`:
  ```python
  elif cmd in {"/confirm", "/revise", "/stop"}:
      pass
  else:
      print(f"unknown command: {cmd}", flush=True)
      continue
  if cmd not in {"/confirm", "/revise", "/stop"}:
      continue
  ```
- **Impact**: Typing `/cancel` at a review gate printed `unknown command: /cancel` and dropped the turn, so the engine-supported command couldn't cancel the task.
- **Evidence**: Confirmed by comparing `session_engine.py:1917` with `repl.py:1396, 1401`. Re-verified in Rev. 2.

#### FINDING-02: Paste Ends Early on Internal Blank Lines in `/paste` Mode
- **Status (Rev. 2)**: ✅ **Fixed in `068e0a0c` (behavior change).** Only an explicit `EOF`/`eof`/`"""` marker now ends `/paste`, and blank lines are kept as content. Ending on a blank line was documented: the old prompt read "type 'EOF' or a blank line to finish". The prompt now reads "type 'EOF' on a new line to finish", and the one existing test that relied on the old behavior now ends with `EOF`. Regression test: `test_paste_mode_keeps_blank_lines_until_eof`.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:558-575`
- **Root Cause**: In `/paste` mode, line 572 checks:
  ```python
  if not raw.startswith('"""') and (sub.strip() in {"EOF", "eof", '"""'} or (not sub.strip() and lines_buf)):
      break
  ```
  Once the first line is buffered (`lines_buf` is non-empty), any blank line makes `not sub.strip() and lines_buf` true.
- **Impact**: Pasting Python scripts, markdown prompts, or text with paragraph breaks ended paste mode at the first blank line and silently lost the rest.
- **Evidence**: Reproduced: pasting `"def foo():\n\n    return 42\nEOF"` yielded only `"def foo():"`. Re-verified in Rev. 2.

#### FINDING-03: Blocking Hang in Windows Console Burst Detection
- **Status (Rev. 2)**: ✅ **Fixed in `068e0a0c`.** The new `_drain_console_burst_win32()` (`repl.py:480`) reads the keys already waiting with `msvcrt.getwch()` instead of calling `input()`. It handles CR/CRLF line endings, backspace, and function-key prefixes, keeps an unfinished last line as the final line, and echoes what it captured, since `getwch` doesn't echo. The Windows burst tests now use a fake `msvcrt` and run on every OS. Regression test: `test_console_burst_without_trailing_newline_does_not_block`. *Known limitation:* `getwch` reports arrow keys as `'\xe0'` followed by a scan code, and `'\xe0'` is also the character `à`, so it is treated as text. An arrow key pressed in the middle of a burst could insert stray characters.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:522-527`
- **Root Cause**: Lines 525-526 ran:
  ```python
  while msvcrt.kbhit():
      lines.append(input())
      time.sleep(0.02)
  ```
  `msvcrt.kbhit()` returns `True` as soon as any key is waiting in the console buffer, but `input()` blocks until a newline (`\r` or `\n`) arrives.
- **Impact**: Fast typing, or pasted text without a trailing newline, left the REPL stuck in the loop until the user pressed Enter.
- **Evidence**: Code reading of `msvcrt.kbhit()` vs `input()` semantics on Windows. Re-verified in Rev. 2 (verified on Linux with a fake console; not run on a real Windows console). *Rev. 3:* the fake-`msvcrt` burst tests also pass on Windows 11. A real interactive console burst still hasn't been exercised by hand.

#### FINDING-04: Windows AppContainer `_ctypes.pyd` DLL Load Failure in Native Confinement Test
- **Status (Rev. 3)**: ✅ **Confirmed on Windows.** `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]` passes on Windows 11 / Python 3.11.9.
- **Status (Rev. 2)**: ✅ **Fixed in `068e0a0c`; Windows confirmation pending.** The test still requires that `top-secret-value` never appears in stdout. On Windows, if stderr shows `DLL load failed while importing _ctypes`, the run must have failed, and that counts as the native layer stopping native code. Otherwise the original assertions apply unchanged (`success` and `denied`). Non-Windows behavior is unchanged.
- **File & Lines**: `tests/test_confinement.py:509-526` (`test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]`)
- **Root Cause**: The test turns off the in-process audit hook (`_policy_hooks = False`) and runs Python code with `import ctypes` to check that Windows AppContainer stops it reading a secret file via `ctypes.cdll.msvcrt._open`. But AppContainer security policy blocks the initialization of `_ctypes.pyd`, raising `ImportError: DLL load failed while importing _ctypes`.
- **Impact**: The test failed with `AssertionError: assert False where False = SandboxResult(...).success`, breaking the suite on Windows.
- **Evidence**: Verbatim pytest failure log at `tests/test_confinement.py:525` (from the original audit; not reproducible on Linux).

#### FINDING-05: Windows Sandbox `os.startfile` Exception Divergence
- **Status (Rev. 3)**: ✅ **Confirmed on Windows.** `test_sandbox_blocks_startfile_on_windows` passes on Windows 11 / Python 3.11.9.
- **Status (Rev. 2)**: ✅ **Fixed in `068e0a0c`; Windows confirmation pending.** The assertion accepts `PermissionError` (blocked by the audit hook) or the exact message `NotImplementedError: startfile not available`, not the bare exception name, so the check stays strict. `not result.success` is still required.
- **File & Lines**: `tests/test_sandbox.py:202-206` (`test_sandbox_blocks_startfile_on_windows`)
- **Root Cause**: The test runs `import os; os.startfile('cmd.exe')` inside `ExecutionSandbox` and asserts `assert "PermissionError" in result.stderr`. CPython's `os.startfile` checks that ShellExecute is available before raising its `os.startfile` audit event. Inside AppContainer that check fails, so it raises `NotImplementedError: startfile not available on this platform` and the audit hook never runs.
- **Impact**: The test in `tests/test_sandbox.py` failed on Windows.
- **Evidence**: Verbatim pytest failure log at `tests/test_sandbox.py:206` (from the original audit; not reproducible on Linux).

---

### 2. Medium Severity Findings

#### FINDING-06: Closed File Handle Left Behind by the `/transcript` Command
- **Status (Rev. 2)**: Open. Re-verified (`repl.py:1297-1303` @ `068e0a0c`).
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:1256-1265`
- **Root Cause**:
  ```python
  runtime.transcript.close()
  transcript_path = Path(arg)
  transcript_path.parent.mkdir(parents=True, exist_ok=True)
  runtime.transcript = transcript_path.open("a", encoding="utf-8", newline="\n")
  ```
  The current transcript handle is closed before the new path is checked. An invalid path raises an unhandled `OSError`, leaving `runtime.transcript` pointing at a closed file.
- **Impact**: The unhandled exception crashes the REPL, and later turns crash in `_write_transcript()`.
- **Evidence**: Code reading of lines 1258-1262.
- **Suggested fix**: open the new handle first, then close and swap the old one, inside a `try/except OSError` that reports the error and keeps the old transcript.

#### FINDING-07: Operational Settings Reset on Session/Worker Switching
- **Status (Rev. 2)**: Open. **Refined on re-verification.** `/new` and `/resume` pass the existing `worker` object to `switch_session()`, so settings changed on the worker (`/timeout`, `/model`, worker-level `/dev set` keys) **survive** them. Those settings are lost only on `/worker`, which builds a new worker from the CLI `args`. Runtime-level settings (`/dev set exit-on-close`) reset on **every** switch, because `open_session()` rebuilds the runtime from `args`.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:326-336` (`switch_session`), `/worker` handler (`repl.py:1315-1382` @ `068e0a0c`)
- **Root Cause**: `/worker` creates a new worker (`ApiWorker(model=args.model, timeout=args.worker_timeout, ...)`), and `switch_session()` → `open_session(args, ...)` rebuilds `SessionRuntime` from the CLI namespace.
- **Impact**: Settings changed during a session (`/dev set timeout`, `/dev set model`, `/model`, `/dev set provider`) are silently reset to the CLI defaults when the worker is switched, and `exit_on_close` resets on any session switch.
- **Evidence**: Code reading of `switch_session` and the `/worker`, `/new`, and `/resume` handlers.

#### FINDING-08: Typing `/confirm` at the Paste Confirmation Appends It to the Prompt
- **Status (Rev. 2)**: Open. Re-verified (both the bracketed-paste and console-burst branches).
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:514-515, 553-554`
- **Root Cause**:
  ```python
  if confirm == "/cancel":
      return ""
  if confirm:
      pasted = pasted + "\n" + confirm
  return pasted
  ```
  At the `[Pasted N lines. Press Enter to submit, or type /cancel to discard]` prompt, users often type `/confirm`. Because `/confirm` isn't `/cancel`, it gets appended to the prompt text.
- **Impact**: The user's prompt ends with an unwanted `\n/confirm`.
- **Evidence**: Code reading of `repl.py:514-515`.

#### FINDING-09: ADR-0018 §3.3 `contradictory_reconciliation` Not Implemented
- **Status (Rev. 2)**: Open. Re-verified: `contradictory_reconciliation` appears only in `docs/adr/0018-…:71`, nowhere in `src/`.
- **File & Lines**: `docs/adr/0018:68-72`, `src/pdl_taskmaster/runtime/result_ir.py:180-275`
- **Root Cause**: ADR-0018 §3.3 says that when a witness has `polarity == "negative"`, any existential requirement marked `"satisfied"` must be rejected as `contradictory_reconciliation`. `validate_result_ir` in `result_ir.py` has no code for this check.
- **Impact**: The code diverges from the specification, and an intended integrity invariant is not enforced.
- **Evidence**: `contradictory_reconciliation` is entirely absent from `result_ir.py`.
- **Note**: ADR-0018 detects these requirements by keyword (`GENERATE`, `PROVIDE`, `CONSTRUCT`, `FIND`, `EXAMPLE`). Re-implementing that as text matching would conflict with GUARD-02/04 and the AGENTS.md ban on heuristic regex. Either drive it from a typed requirement-kind field, or amend the ADR.

#### FINDING-10: Undocumented Headless Exit Code 4 (`EXIT_HARNESS_ERROR`)
- **Status (Rev. 2)**: Open. Re-verified: `EXIT_HARNESS_ERROR = 4` (`repl.py:425`) is returned on harness or provider failure. ADR-0019, `TARGET_ARCHITECTURE.md` and the exit-code list in `AGENTS.md` document only 0–3. It was observed live in Rev. 2: an egress block on OpenRouter ended the run with `PROVIDER_UNAVAILABLE at BOOTSTRAP_ANALYSIS … Exiting (code 4)`.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:424-425, 1475-1476`
- **Root Cause**: `repl.py` defines and returns `EXIT_HARNESS_ERROR = 4` on harness or provider infrastructure failure, but ADR-0019 and `TARGET_ARCHITECTURE.md` only document codes 0, 1, 2, and 3.
- **Impact**: Tools that integrate with PDLt exit codes per ADR-0019 receive an undocumented code.
- **Evidence**: `EXIT_HARNESS_ERROR = 4` in `repl.py:425`.

#### FINDING-11: Circular Module Dependency Between `sandbox.py` and `backends.py`
- **Status (Rev. 2)**: Open. Re-verified that the lazy import exists (`backends.py:140`). The import cycle is avoided at runtime by deferring the import, so this is a coupling and maintainability issue, not a defect.
- **File & Lines**: `src/pdl_taskmaster/verification/sandbox.py:21-28`, `src/pdl_taskmaster/verification/confinement/backends.py:140`
- **Root Cause**: `sandbox.py` imports from `confinement.backends` at the top of the module, while `backends.py:140` imports `from pdl_taskmaster.verification import sandbox as _sb` inside `launch()`.
- **Impact**: The coupling obscures which module sits above which and makes refactoring harder.
- **Evidence**: Import inspection of both files.

---

### 3. Low Severity Findings

#### FINDING-12: No `shlex` Argument Tokenization
- **Status (Rev. 2)**: Open. Not re-verified.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:602, 1164`
- **Root Cause**: Arguments are split with a plain `str.split(maxsplit=1)`, so quoted strings keep their quotes (e.g. `/workdir "C:\My Workspaces"`).
- **Impact**: Quoted paths or model names fail to resolve, or are stored with the quotes.
- **Evidence**: Code reading of `repl.py:1164`.

#### FINDING-13: Slash Commands Outside the Exception Boundary
- **Status (Rev. 2)**: Open. Not re-verified.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:1163-1405`
- **Root Cause**: The `try/except Exception` block wraps `runtime.handle(line)` (lines 1408-1428), but slash commands are processed outside any exception handler.
- **Impact**: An unhandled exception in any slash command crashes the REPL with a raw traceback (FINDING-06 is one example).
- **Evidence**: Loop structure in `repl.py:1118-1460`.

#### FINDING-14: Inconsistent Package Version Metadata (`2.6.0rc1` vs `v2.7.0`)
- **Status (Rev. 2)**: Open. Re-verified: `__init__.py` and `VERSION` say `2.6.0rc1`, while `TARGET_ARCHITECTURE.md` is titled "v2.7.0 — Lean Build". `TARGET_ARCHITECTURE.md` reads as a target document, so decide whether to bump the version or reword the title.
- **File & Lines**: `src/pdl_taskmaster/__init__.py:3`, `pyproject.toml:46`, `TARGET_ARCHITECTURE.md:1-5`
- **Root Cause**: `TARGET_ARCHITECTURE.md` describes the release as `PDL Taskmaster v2.7.0 — Lean Build`, while `__init__.py` declares `__version__ = "2.6.0rc1"`.
- **Impact**: Documentation, build metadata, and runtime banners disagree about the version.
- **Evidence**: `__version__ = "2.6.0rc1"` in `src/pdl_taskmaster/__init__.py:3`.

#### FINDING-15: Unused Imports in Runtime Modules
- **Status (Rev. 2)**: Open. Re-verified: both files import `re` and never use it.
- **File & Lines**: `src/pdl_taskmaster/runtime/result_ir.py:21`, `src/pdl_taskmaster/runtime/operation_bridge.py:8`
- **Root Cause**: `import re` is still at the top of both files even though all regexes were removed.
- **Impact**: Minor clutter.
- **Evidence**: Unused `import re` statements.

#### FINDING-18: No Central Command Registry *(added in Rev. 2; §B dimension 14 previously cited it as FINDING-10)*
- **Status (Rev. 2)**: Open. Partly addressed: review commands are now one shared set (`REVIEW_COMMANDS`).
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:1163-1405` (`main()`), `repl.py:601-802` (`_handle_dev_command()`)
- **Root Cause**: Commands are dispatched through long `if/elif` chains with no registry or decorator pattern, so the help text, dispatch, and whitelists can drift apart.
- **Impact**: The code is hard to follow, and this drift directly caused FINDING-01.

#### FINDING-19: Headless Lines Left Over After Closure Restart the Protocol *(added in Rev. 3)*
- **Status (Rev. 3, update)**: ✅ **Fixed in the working tree of `claude/compassionate-carson-kfafta` (uncommitted).**
  - **The fix:** the real defect was narrower than ending headless runs on closure. Plain requests after closure are a supported workflow (`test_repl_command_loop_full_deterministic_session` pipes two tasks through one REPL). The bug was that a *review command* with no open review got wrapped by `_ensure_protocol_entry()` and started a new task. `PDLtHost.handle()` (`src/pdl_taskmaster/host/app.py`) now answers `/confirm`, `/revise`, `/stop` and `/cancel` with a notice when no protocol instance is open. That covers interactive and headless runs, and covers runs before the first task as well as after closure.
  - **Regression tests:** `test_headless_review_commands_after_closure_do_not_restart_the_task` and `test_review_command_before_any_task_is_not_a_request` both fail without the fix and pass with it.
  - **Test results:** full suite 550 passed / 42 skipped / 0 failed; anti-overfitting 15/15.
  - **Live check:** `pdlt --sandbox container --dev` with four `/confirm`s and no `--exit-on-close` reached `CLOSED_SUCCESS` with `product: 56` and exit 0. The two leftover `/confirm`s each got the notice, and Docker events show a single sandbox exec with exit code 0.
  - **Merge note:** this branch still lacks `068e0a0c`, so `/cancel` at a gate is still `unknown command` here (FINDING-01).
- **Status (Rev. 3)**: Open. Seen live on `068e0a0c`. Not a regression from `068e0a0c`, which doesn't touch this path.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:1450, 1490-1492` @ `068e0a0c`; `exit_on_close` defaults to `False` (`repl.py:151, 302`).
- **Root Cause**: After `[protocol closed]`, the REPL exits only if `runtime.exit_on_close` is on. Otherwise it keeps reading stdin even in non-interactive mode, and the next piped line goes back to `runtime.handle()` as a new request. The headless loop already stops in this situation after an error (comment at `repl.py:1464`) and after an interrupt, but it doesn't stop after a successful or cancelled close.
- **Impact**: A piped script with more `/confirm`s than review gates turns a verified success into exit 2. The task in the prompt suggested from four `/confirm`s, but the run needed only two. Run without `--exit-on-close`, it reached `CLOSED_SUCCESS` (`product: 56`), then the third `/confirm` started a second protocol on the same task, and the run ended `[headless halt] Session ended at non-terminal stage 'PLAN_REVIEW'. Exiting fail-closed (code 2).` The same script with `--exit-on-close` exits 0. The second protocol also makes paid provider calls nobody asked for.
- **Scope**: `run_catalogue.py` passes `--non-interactive --exit-on-close` (`run_catalogue.py:332-333`), so catalogue results are not affected. ADR-0019 only describes headless runs with `--exit-on-close`, and nothing says the flag is required for exit codes to hold.
- **Suggested fix**: When the session isn't interactive, treat closure as the end of the run (stop reading stdin, or make `exit_on_close` default to on), the same way the error and interrupt paths already do. Alternatively, document `--exit-on-close` as required for headless runs in ADR-0019 and `AGENTS.md`.

---

### 4. Informational Findings

#### FINDING-16: Backslash Continuation Strips Indentation
- **Status (Rev. 2)**: Open. Not re-verified.
- **File & Lines**: `src/pdl_taskmaster/host/repl.py:582`
- **Root Cause**: The continuation loop calls `sub.strip()`, which removes leading whitespace.
- **Impact**: Indented code typed or pasted with `\` continuation loses its indentation.
- **Evidence**: `parts.append(sub.strip())` in `repl.py:582`.

#### FINDING-17: Test Fixture Depends on a Sibling Repository Path
- **Status (Rev. 2)**: Open (informational). The vendored `tests/fixtures/recorded-cases.json` exists and is resolved first, so the sibling path is only a last-resort fallback.
- **File & Lines**: `tests/test_repl_integration.py:22-24`
- **Root Cause**: `_resolve_fixture_file()` refers to `ROOT.parent / "PDL-Standard-Archive" / "fixtures-r4-recorded-worker" / "recorded-cases.json"`.
- **Impact**: Harmless when the local fixtures exist, but it points to an unversioned path outside the repository.
- **Evidence**: File path inspection in `test_repl_integration.py`.

---

## E. Missing Test Coverage

To close the coverage gaps found across the 14 lifecycle areas, the following 8 pytest scenarios are proposed with full test names and assertions. *(Rev. 2: each scenario now carries a status line.)*

### Scenario E1: CLI Rejection of Windows Reserved Session Names
*Status (Rev. 2): Proposed, not run. `cli.main(argv)` does accept an argv list.*
```python
def test_cli_rejects_windows_reserved_session_names(capsys):
    """Verify CLI immediately rejects Windows reserved device names with non-zero exit code and clear diagnostic."""
    from pdl_taskmaster.host import cli
    for name in ["CON", "NUL", "COM1", "LPT1", "aux"]:
        code = cli.main(["--non-interactive", "--session-id", name, "--prompt", "test"])
        assert code != 0
        captured = capsys.readouterr()
        assert "reserved device name" in captured.err.lower() or "invalid session name" in captured.err.lower()
```

### Scenario E2: Unknown Slash Command Suggestion & Exception Shielding
*Status (Rev. 2): Proposed, not run.*
```python
def test_repl_unknown_slash_command_provides_friendly_suggestion(tmp_path):
    """Typing an unknown slash command should notify user without crashing or dispatching to model."""
    proc = _run_repl(tmp_path, ["/statuss", "/quit"], "unknown_cmd_test")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0
    assert "unknown command: /statuss" in out.lower()
    assert "traceback" not in out.lower()
```

### Scenario E3: Incomplete Bracketed Paste EOF Graceful Recovery
*Status (Rev. 2): **Would fail as written.** In Rev. 2 these exact inputs returned `''`, not the pasted text. The multi-line paste reaches the "[Pasted 2 lines …]" confirmation, `input()` raises `EOFError` there, and the paste is discarded. The REPL doesn't crash, but the content is lost. Decide whether discarding on EOF is the intended behavior before adding this test.*
```python
def test_bracketed_paste_truncated_eof_handling(monkeypatch):
    """If bracketed paste starts but stdin reaches EOF before end marker, REPL must recover gracefully."""
    from pdl_taskmaster.host.repl import PASTE_START, _read_repl_input
    inputs = [f"{PASTE_START}def broken_paste():", "    line2"]
    monkeypatch.setattr("builtins.input", lambda prompt="": inputs.pop(0) if inputs else (_ for _ in ()).throw(EOFError))
    result = _read_repl_input()
    assert result == "def broken_paste():\n    line2"
```

### Scenario E4: Corrupted `session.json` Recovery on `/resume`
*Status (Rev. 2): Proposed, not run.*
```python
def test_resume_corrupted_session_json_fails_gracefully(tmp_path):
    """Corrupted session.json must output user-facing error and not crash with unhandled JSONDecodeError."""
    session_dir = tmp_path / "sessions" / "corrupt_session"
    session_dir.mkdir(parents=True)
    (session_dir / "session.json").write_text("{invalid_json: true", encoding="utf-8")
    proc = _run_repl(tmp_path, ["/resume corrupt_session", "/quit"], "active_session")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0
    assert "corrupted" in out.lower() or "cannot resume" in out.lower() or "not restorable" in out.lower()
    assert "jsondecodeerror" not in out.lower()
```

### Scenario E5: Headless Exit Code 1 on Review Cancellation (`/stop`)
*Status (Rev. 2): ✅ **Implemented** as `tests/test_repl_integration.py::test_repl_review_cancel_commands_close_cancelled`, parameterized over `/stop` and `/cancel`. It asserts exit code 1, `[protocol closed]`, and no `unknown command` output.*
```python
def test_repl_headless_exit_code_1_on_stop_cancellation(tmp_path):
    """Headless run halted via /stop at review gate must exit code 1 (CLOSED_CANCELLED)."""
    turns = _g06_turns()
    proc = _run_repl(tmp_path, [turns[0], "/stop"], "headless_cancel")
    assert proc.returncode == 1
    assert "CLOSED_CANCELLED" in (proc.stdout + proc.stderr)
```

### Scenario E6: AppContainer `os.startfile` Platform Containment Resilience
*Status (Rev. 2): ✅ **Implemented** by tightening the existing `tests/test_sandbox.py::test_sandbox_blocks_startfile_on_windows`. It matches the full `NotImplementedError: startfile not available` message rather than the bare exception name.*
```python
def test_sandbox_startfile_handles_not_implemented_as_denial():
    """On Windows AppContainer, startfile may raise NotImplementedError instead of PermissionError; both signify containment."""
    from pdl_taskmaster.verification.sandbox import ExecutionSandbox
    result = ExecutionSandbox().run_code("import os\nos.startfile('cmd.exe')")
    assert not result.success
    assert any(err in result.stderr for err in ["PermissionError", "NotImplementedError"])
```

### Scenario E7: AppContainer `_ctypes` Native Import Containment Handling
*Status (Rev. 2): ✅ **Covered** by the amended existing test `tests/test_confinement.py::test_escape_native_code_cannot_read_the_secret_without_the_audit_hook`. It uses the suite's own fixtures for `mode` and the secret rather than the separate test below.*
```python
def test_sandbox_native_ctypes_import_denial_in_appcontainer():
    """In native AppContainer without audit hooks, importing _ctypes fails at DLL initialization; verify secret remains protected."""
    import tempfile
    from pathlib import Path
    from pdl_taskmaster.verification.sandbox import ExecutionSandbox
    secret_path = Path(tempfile.gettempdir()) / "secret_probe.txt"
    secret_path.write_text("classified", encoding="utf-8")
    try:
        box = ExecutionSandbox(mode="native")
        box._policy_hooks = False
        with box:
            result = box.run_code(f"import ctypes\nprint(open({str(secret_path)!r}).read())")
            assert not result.success or "classified" not in result.stdout
    finally:
        secret_path.unlink(missing_ok=True)
```

### Scenario E8: Dev Mode Type Validation and Mutation Rejection
*Status (Rev. 2): Proposed, not run. A `dev_env` fixture would need to be written.*
```python
def test_dev_mode_rejects_invalid_mutations(capsys, dev_env):
    """Dev mode must validate types when mutating configuration."""
    from pdl_taskmaster.host.repl import _handle_dev_command
    runtime, worker, base = dev_env
    handled, _ = _handle_dev_command("/dev set timeout invalid_num", True, runtime, worker, base)
    assert handled is True
    out = capsys.readouterr().out
    assert "invalid" in out.lower() or "error" in out.lower()
    assert worker.timeout == 60.0  # unchanged default
```

### Additional tests added in Rev. 2 (not in the original proposal)
- `tests/test_repl_paste.py::test_paste_mode_keeps_blank_lines_until_eof` (FINDING-02)
- `tests/test_repl_paste.py::test_console_burst_without_trailing_newline_does_not_block` (FINDING-03)
- `tests/test_repl_paste.py::test_console_burst_paste_confirmed`, `test_console_burst_paste_discarded` and `test_console_typed_command_after_an_empty_enter_is_not_a_paste` now use a fake `msvcrt` and run on every OS (previously skipped outside Windows).

---

## F. Regression Analysis

### 1. Codebase Before PR #1 vs After
Before Pull Request #1, the repository at merge-base commit `ddbd3be1` contained:
- `prompts/`: 105 prompt text files and solution verification JSON files.
- `prompts/CATALOGUE_MANIFEST.jsonl`: Benchmark catalog metadata.
- `run_catalogue.py`: An evaluation driver that expected an external executable.
- Documentation: `README.md`, `GOAL.md`, `REVIEWER.md`, `STEP5_SPOT_CHECK_REPORT.md`.

There was **no implementation code in `src/`**, **no test suite in `tests/`**, and **no interactive REPL**. PR #1 therefore adds new code rather than refactoring existing Python packages in place.

### 2. Refactored Assets and De-Contamination
1. **Prompt Text De-Contamination (Commit `98004ff1`)**:
   - Several prompt files on `origin/main` had test-driver instructions embedded in the prompt body (e.g. `(This prompt is designed for multi-turn testing. After the model drafts...)`).
   - PR #1 removed these instructions from the raw prompt files and moved them into a `"multi_turn_script"` property in `CATALOGUE_MANIFEST.jsonl`. This stops models from treating evaluator instructions as task constraints.
2. **`run_catalogue.py` Modernization**:
   - Replaced the call to an external binary with direct calls to `pdl_taskmaster.host.cli` in non-interactive mode.
   - Wrapped prompt execution in `_Containment`, using Windows Job Objects and POSIX limits (4096MB memory limit).
   - Added `--fail-fast`, per-operation reasoning controls, and false-positive tracking.

### 3. Preserved Benchmark Capabilities & Historical Regression Guard
The catalogue links prompt failure modes to specific regression IDs (`REG-001` through `REG-014`):
- `REG-001`: Schema injection attacks.
- `REG-003`: Backtracking combinatorial search.
- `REG-011`: Exact cover DLX combinatorial recursion.
- `REG-012`: Latin square constraint propagation.
- `REG-013`: SQL query scope without execution.
- `REG-014`: Out-of-scope medical boundary refusal.

All 105 catalogue prompts remain intact and parse cleanly, with 21 verified ground-truth references. The anti-overfitting suite independently confirms that the harness does not cheat on these benchmarks.

### 4. Remediation Regression Check (Rev. 2)
Commit `068e0a0c` changes `src/pdl_taskmaster/host/repl.py` and four test files only. It touches no prompts, gates, checkers, the session engine, contracts, or graders. On Linux (Python 3.11.15):
- Full suite: **563 passed, 31 skipped, 0 failed** (69s).
- `tests/test_harness_anti_overfitting.py`: **15 passed** (0 warnings, 0 skips).
- Targeted run (`test_repl_paste.py`, `test_repl_integration.py`, `test_sandbox.py`, `test_confinement.py`): 141 passed, 29 skipped.
- Before/after proof: running the new tests against the original `repl.py` from `75b7dcbb` gives **6 failed, 5 passed**. The failures are the `/cancel` case, the blank-line paste, and four Windows burst tests; the passes include the `/stop` control.
- `run_catalogue.py` was not run, since it needs live provider access.

### 5. Windows and Live Verification (Rev. 3)
Windows 11 Pro (10.0.22000), Python 3.11.9, editable install of `068e0a0c` with `.[test]` in a clean venv:
- Full suite: **550 passed, 44 skipped, 0 failed** (170s). Every skip is environmental: no Docker or Podman, POSIX-only features (`select` burst detection, rlimits, process groups, rusage, `sendmsg`), Landlock and Seatbelt backends, ELF executables, and `jsonschema` not installed.
- `tests/test_harness_anti_overfitting.py`: **15 passed** (0 warnings, 0 skips).
- Remediated tests, all **passed on Windows**: `test_escape_native_code_cannot_read_the_secret_without_the_audit_hook[native]`, `test_sandbox_blocks_startfile_on_windows`, `test_console_burst_paste_confirmed`, `test_console_burst_paste_discarded`, `test_console_burst_without_trailing_newline_does_not_block`, `test_console_typed_command_after_an_empty_enter_is_not_a_paste`, `test_paste_mode_keeps_blank_lines_until_eof`, and `test_repl_review_cancel_commands_close_cancelled[/stop]` and `[/cancel]`.
- Live dev-mode REPL (`pdlt --new-session --dev`, OpenRouter reachable, key set):

| Run | Piped input | Exit | Final stage | Notes |
|---|---|---|---|---|
| Success | task, 2× `/confirm` | 0 | `CLOSED_SUCCESS` | Witness `{"polarity": "positive", "data": {"product": 56}}`, no Traceback |
| Success | task, 4× `/confirm`, `--exit-on-close` | 0 | `CLOSED_SUCCESS` | `product: 56` |
| Success | task, 4× `/confirm` (no flag) | 2 | `PLAN_REVIEW` | Closed successfully first, then restarted (FINDING-19) |
| Cancel | task, `/cancel` | 1 | `CLOSED_CANCELLED` | `Cancelled.`, `[protocol closed]`, no `unknown command` |

No provider or model errors occurred. Each call returned in about 2.5–5 s.

---

## G. Final Assessment & Recommendation

### Recommendation: **APPROVE WITH REQUIRED AMENDMENTS (BEFORE MERGE)**
**Rev. 2 status: the required code amendments are done. Approval depends on the two open gates below.**
**Rev. 3 status: both verification gates are closed (live REPL green on `068e0a0c`, Windows confirmed). The only step left is the merge path, gate 3 below.**

Pull Request #1 is high-quality, architecturally sound engineering work. It delivers a lean, dual-plane execution engine, a comprehensive CLI REPL, session-scoped confinement, and full referee integrity (`GUARD-01` through `GUARD-05`).

Because PR #1 adds user-facing CLI functionality, and its test suite failed out of the box on Windows development machines, these **5 Blocking Items** had to be resolved before merging into `main`:

### Blocking Items for Merge:
| # | Item | Status (Rev. 2) |
|---|---|---|
| 1 | Add `/cancel` to the review-command whitelist (`repl.py:1396, 1401`) | ✅ Fixed in `068e0a0c` (shared `REVIEW_COMMANDS`; `/help` updated) |
| 2 | Stop internal blank lines ending `/paste` mode (`repl.py:572-573`) | ✅ Fixed in `068e0a0c` (only `EOF` ends paste; prompt text updated) |
| 3 | Fix the Windows console burst hang (`repl.py:522-527`) | ✅ Fixed in `068e0a0c` (keys read without blocking via `getwch`) |
| 4 | Fix the Windows AppContainer `_ctypes` test failure (`test_confinement.py:523-526`) | ✅ Fixed in `068e0a0c`; ✅ passes on Windows (Rev. 3) |
| 5 | Fix the `os.startfile` test assertion on Windows (`test_sandbox.py:206`) | ✅ Fixed in `068e0a0c`; ✅ passes on Windows (Rev. 3) |

### Open Gates Before Approval (Rev. 2):
1. **Live dev-mode REPL verification (`AGENTS.md`, mandatory)**: ✅ *Closed in Rev. 3.* On `068e0a0c` (Windows, OpenRouter reachable), the success run reached `CLOSED_SUCCESS` with deliverable 56 and exit 0, and the `/cancel` run reached `CLOSED_CANCELLED` with exit 1 and no `unknown command`. See §F.5. *Rev. 2 text follows:* In the remediation session, and in a child session it launched, the egress proxy refused `openrouter.ai:443` (`403`, policy denial) even after the allowlist was updated, so no live run was done on `068e0a0c`. That attempt ended with exit code 4 (`PROVIDER_UNAVAILABLE`), which is not a pass. A manual live run is in progress. The expected results are `CLOSED_SUCCESS`, deliverable 56 and exit 0 for "Compute the product of 7 and 8", and `CLOSED_CANCELLED` with exit 1 and no `unknown command` when cancelled with `/cancel` at the prompt review gate. As an offline substitute, a dev-mode run with the recorded worker cancelled via `/cancel` reached `PROMPT_REVIEW → CLOSED_CANCELLED` with exit code 1.
2. **Windows confirmation of items 4 and 5**: ✅ *Closed in Rev. 3.* Both tests pass on Windows 11 / Python 3.11.9, and the full suite gives 550 passed, 44 skipped, 0 failed. *Rev. 2 text follows:* Run `pytest tests/test_confinement.py tests/test_sandbox.py` on a Windows host. The Rev. 2 changes rely on the failure logs from the original audit.
3. **Merge path**: the fixes are on `claude/exciting-albattani-n2s3x8` (PR head + 1 commit). Merge that branch into `claude/compassionate-carson-kfafta`, or open a PR from it into that branch, so the fixes become part of PR #1.

### Non-Blocking Items (Follow-up PR):
- Bring ADR-0018 §3.3 in line with the code, or implement `contradictory_reconciliation` in `result_ir.py` from a typed requirement kind, not keyword matching (FINDING-09).
- Document exit code 4 (`EXIT_HARNESS_ERROR`) in ADR-0019, `TARGET_ARCHITECTURE.md` and `AGENTS.md` (FINDING-10).
- Keep operational settings across `/worker` switches and keep runtime-level settings across all session switches (FINDING-07, refined).
- Make `/transcript` open the new file before closing the old one (FINDING-06), and put slash commands inside the exception boundary (FINDING-13).
- Stop appending `/confirm` to the paste payload (FINDING-08), and decide how a paste cut off by EOF should behave (Scenario E3).
- Break the circular import between `sandbox.py` and `backends.py` (FINDING-11).
- Make the version consistent: `2.6.0rc1` in `__init__.py`/`VERSION` vs "v2.7.0" in `TARGET_ARCHITECTURE.md` (FINDING-14).
- Remove the unused `import re` (FINDING-15). Consider a command registry (FINDING-18).
- In headless mode, end the run on closure instead of treating leftover piped lines as a new request, or document `--exit-on-close` as required (FINDING-19, Rev. 3).

---

## H. Remediation Log (Rev. 2)

| Field | Value |
|---|---|
| Remediation commit | `068e0a0c` — `fix(repl): resolve blocking review findings for PR #1` |
| Branch | `claude/exciting-albattani-n2s3x8` (`paragon-ux/PDLt-Test`), based on PR head `75b7dcbb` |
| Files changed | `src/pdl_taskmaster/host/repl.py`, `tests/test_repl_paste.py`, `tests/test_repl_integration.py`, `tests/test_sandbox.py`, `tests/test_confinement.py` (+119 / −35) |
| Pre-change verification | FINDINGS 01–03 confirmed against the code at `75b7dcbb`. FINDINGS 04–05 can't be reproduced on Linux; they were checked against CPython's `os.startfile` ordering and the audit's failure logs. |
| Test results (Linux, Py 3.11.15) | Full suite 563 passed / 31 skipped / 0 failed; anti-overfitting 15/15 |
| Fails-before / passes-after | 6 of the new or rewritten tests fail on `75b7dcbb` and pass on `068e0a0c` |
| Offline REPL run | Dev mode, recorded worker (G06), `/cancel` at the review gate → `CLOSED_CANCELLED`, exit 1 |
| Live REPL run | Rev. 2: not done, because the session egress policy blocked `openrouter.ai` (403). **Rev. 3: ✅ done on Windows.** Success run: `CLOSED_SUCCESS`, `product: 56`, exit 0. `/cancel` run: `CLOSED_CANCELLED`, exit 1, no `unknown command` (§F.5) |
| Windows run | Rev. 2: not done, because no Windows host was available. **Rev. 3: ✅ done.** Windows 11 / Py 3.11.9: 550 passed / 44 skipped / 0 failed; anti-overfitting 15/15; fixes 4 and 5 pass |
| New finding (Rev. 3) | FINDING-19 (Low): headless lines left over after closure restart the protocol unless `--exit-on-close` is set |
| Behavior changes for users | `/paste` no longer ends on a blank line (type `EOF`). `/cancel` now cancels at review gates. On Windows, bursts don't echo per keystroke; captured text is echoed once. |

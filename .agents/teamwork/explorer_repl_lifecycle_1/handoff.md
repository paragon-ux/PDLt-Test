# Handoff Report: REPL Lifecycle Audit (Requirement R1)

## 1. Observation
1. **Broken `/cancel` Review Command**:
   - In `src/pdl_taskmaster/runtime/session_engine.py` line 1917:
     ```python
     if lower in {"/stop", "stop", "/cancel", "cancel"}:
         return self.handle_explicit_review(Intent.CANCEL)
     ```
   - In `src/pdl_taskmaster/host/repl.py` lines 1396-1405:
     ```python
     elif cmd in {"/confirm", "/revise", "/stop"}:
         pass
     else:
         print(f"unknown command: {cmd}", flush=True)
         continue
     if cmd not in {"/confirm", "/revise", "/stop"}:
         continue
     ```
     Observed directly: `/cancel` is omitted from the whitelist in `repl.py:1396` and `repl.py:1401`.

2. **Premature Paste Truncation on Blank Lines**:
   - In `src/pdl_taskmaster/host/repl.py` lines 572-573:
     ```python
     if not raw.startswith('"""') and (sub.strip() in {"EOF", "eof", '"""'} or (not sub.strip() and lines_buf)):
         break
     ```
     Observed directly: `not sub.strip() and lines_buf` triggers on any blank line once `lines_buf` has at least one entry, truncating the pasted content at the first blank line.

3. **Windows Console Burst Blocking**:
   - In `src/pdl_taskmaster/host/repl.py` lines 525-526:
     ```python
     while msvcrt.kbhit():
         lines.append(input())
         time.sleep(0.02)
     ```
     Observed directly: `msvcrt.kbhit()` returns True for any keypress event in the console queue, but `input()` synchronously blocks until a newline is entered.

4. **Closed Stream Leak in `/transcript`**:
   - In `src/pdl_taskmaster/host/repl.py` lines 1258-1262:
     ```python
     runtime.transcript.close()
     transcript_path = Path(arg)
     transcript_path.parent.mkdir(parents=True, exist_ok=True)
     runtime.transcript = transcript_path.open("a", encoding="utf-8", newline="\n")
     ```
     Observed directly: The existing file handle is closed before attempting `open()`. An invalid path raises an unhandled `OSError` leaving `runtime.transcript` pointing to a closed stream.

5. **Operational Mutation Reset on Session/Worker Switching**:
   - In `src/pdl_taskmaster/host/repl.py` lines 1320-1340 and 326-336:
     When `/worker`, `/new`, or `/resume` is called, `switch_session` re-instantiates workers and runtimes using the initial command-line `args`. Live parameters mutated via `/dev set ...` are reset to CLI defaults.

6. **Paste Confirmation Appending `/confirm` to Prompt**:
   - In `src/pdl_taskmaster/host/repl.py` lines 514-515 and 553-554:
     `if confirm: pasted = pasted + "\n" + confirm`. If a user types `/confirm`, it is concatenated onto the prompt payload.

7. **Headless Execution Conformance**:
   - In `src/pdl_taskmaster/host/repl.py` lines 1477-1507:
     Exit codes `0` (success/refusal), `1` (cancelled), `2` (non-terminal stall), `3` (waiting input), `4` (harness error) and `cli.py:118` `130` (interrupted) conform to ADR-0012, ADR-0019, and ADR-0020.

## 2. Logic Chain
1. Step 1 (from Observation 1): `SessionEngine` provides explicit cancellation via `/cancel`, but `repl.py` intercepts all slash commands not in `{"/confirm", "/revise", "/stop"}` and outputs `unknown command: /cancel`. Therefore, user attempts to cancel tasks using `/cancel` at review gates fail completely.
2. Step 2 (from Observation 2): Prompts and source code regularly contain empty lines separating paragraphs or functions. Because `/paste` mode breaks upon encountering `not sub.strip() and lines_buf`, any multi-line paste with an internal blank line is silently truncated, discarding critical prompt context.
3. Step 3 (from Observation 3): `msvcrt.kbhit()` indicates keystroke presence, not line availability. Calling blocking `input()` inside the `kbhit()` loop causes the REPL to freeze until a manual Enter key is hit on incomplete lines.
4. Step 4 (from Observation 4): Closing `runtime.transcript` prior to validating the target path creates a state where failure in `open()` leaves the host with a closed file descriptor, breaking subsequent writes in `_write_transcript()`.
5. Step 5 (from Observation 5): `switch_session()` passes the unmodified CLI `args` namespace to `open_session()` and worker constructors. Because in-session mutations are stored only on the worker or runtime instance, switching workers or sessions silently wipes all configured overrides.

## 3. Caveats
- Windows-specific console burst behavior (`msvcrt.kbhit`) depends on terminal emulator implementation (Windows Terminal vs conhost.exe vs VS Code terminal). In modern Windows Terminal with bracketed paste active, branch 1 intercepts pastes before branch 2 is reached.
- Non-interactive tests were validated through existing automated test fixtures (`tests/test_repl_integration.py`, `tests/test_repl_paste.py`, `tests/test_dev_mode.py`); no live LLM API keys (`OPENROUTER_API_KEY`) were invoked during this read-only inspection.

## 4. Conclusion
The REPL implementation exhibits strong architectural discipline in protocol decoupling and headless exit code governance (ADR-0019). However, it contains two High-severity functional defects that must be resolved:
1. Fix the review dispatch whitelist in `repl.py:1396, 1401` to include `"/cancel"`.
2. Fix `/paste` mode in `repl.py:572` so that internal blank lines do not trigger termination (only `"EOF"`, `"eof"`, or `"""` should terminate).
Additionally, five Medium/Low defects (burst detector hang, `/transcript` stream leak, mutation wipe on worker switch, `/confirm` append bug, and missing `shlex` parsing) require remediation to ensure robustness.

## 5. Verification Method
1. Inspect `src/pdl_taskmaster/host/repl.py` lines 1396-1405 and `session_engine.py` line 1917 to confirm the `/cancel` dispatch discrepancy.
2. Inspect `src/pdl_taskmaster/host/repl.py` lines 572-573 to confirm the premature termination condition on blank lines.
3. Inspect `src/pdl_taskmaster/host/repl.py` lines 525-526 to confirm `input()` blocking under `msvcrt.kbhit()`.
4. Run existing test suites:
   - `pytest tests/test_repl_paste.py`
   - `pytest tests/test_repl_integration.py`
   - `pytest tests/test_dev_mode.py`
5. Invalidation conditions: If `/cancel` is demonstrated to reach `SessionEngine` through `repl.py`, or if `/paste` mode successfully accepts internal blank lines without terminating, these findings are invalidated.

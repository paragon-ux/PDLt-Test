# PDLt CLI REPL Lifecycle Audit Report (Requirement R1)

**Audit Subject**: Pull Request #1: "Add PDL Taskmaster Lean Build: Full CLI REPL & Comprehensive Architecture"  
**Repository**: `paragon-ux/PDLt-Test`  
**Auditor**: Explorer Subagent (`explorer_repl_lifecycle_1`)  
**Audit Scope**: Requirement R1: Complete CLI REPL Lifecycle Audit across all 14 Dimensions  
**Key Modules Inspected**:
- `src/pdl_taskmaster/host/repl.py` (70,460 bytes, 1,516 lines)
- `src/pdl_taskmaster/host/app.py` (8,186 bytes, 208 lines)
- `src/pdl_taskmaster/host/cli.py` (4,141 bytes, 126 lines)
- `src/pdl_taskmaster/runtime/session_engine.py` (100,600 bytes, 1,965 lines)
- `src/pdl_taskmaster/observation/observed_session.py` (8,682 bytes, 223 lines)
- `src/pdl_taskmaster/providers/api_worker.py` (59,816 bytes, 1,131 lines)
- `src/pdl_taskmaster/providers/codex_worker.py` (14,671 bytes, 349 lines)
- `tests/test_repl_paste.py` (5,779 bytes, 172 lines)
- `tests/test_repl_integration.py` (9,327 bytes, 262 lines)
- `tests/test_dev_mode.py` (7,845 bytes, 220 lines)

---

## Executive Summary

The PDL Taskmaster REPL system is an interactive terminal interface designed to bridge user intent, review gates, and the underlying dual-plane execution architecture (`MechanicalController`, `SessionEngine`, and `ExecutionSandbox`). The REPL architecture adheres to core architectural mandates:
- **Clean Protocol Separation**: Protocol authority resides strictly within `SessionEngine` and `MechanicalController`. The REPL layer (`SessionRuntime`) performs host bookkeeping only and never functions as a parallel protocol state machine.
- **Fail-Closed Headless Governance (ADR-0012, ADR-0019)**: Headless execution adheres to strict exit code specifications (`0` for success/refusal, `1` for cancelled, `2` for non-terminal stall, `3` for input pause, `4` for harness error, `130` for user interrupt), backed by a 20-second faulthandler watchdog.
- **Agentic Dev Mode**: A comprehensive `/dev` command suite provides runtime inspection, self-diagnostics (`/dev diagnose`), and live operational parameter mutation.

However, an exhaustive lifecycle audit across all 14 dimensions reveals critical functional defects, broken review command dispatch, data loss bugs in paste handling, race conditions in console burst detection, state mutation leaks across session switching, and architectural dispatch coupling.

---

## Dimension-by-Dimension Audit (14 Dimensions)

### Dimension 1: Startup and Initialization
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/cli.py`: Lines 12-19, 77-122
  - `src/pdl_taskmaster/host/repl.py`: Lines 16-46, 229-304, 805-1117
  - `src/pdl_taskmaster/host/app.py`: Lines 55-140
- **Detailed Mechanics**:
  - **Environment Configuration**: On Windows (`sys.platform == "win32"`), `cli.py` (lines 12-19) and `repl.py` (lines 995-999) reconfigure `sys.stdin`, `sys.stdout`, and `sys.stderr` to UTF-8 with `errors="replace"`. This prevents ANSI codepage corruption on Windows when piping UTF-8 prompt text.
  - **Repository & Storage Root**: `_resolve_repo_root()` (repl.py:16-29) checks for `pyproject.toml` or `setup.py` up to three parent levels. For editable installations, session data defaults to `<repo>/runs/live-sessions`; for wheel installations, it resolves to `~/.pdlt/runs/live-sessions` (repl.py:36-46).
  - **Banner & Startup Output**:
    - Lines 1084-1086 print the version header: `PDLt REPL started (v{__version__}).`, instructions for review gates (`/confirm`, `/revise <feedback>`, `/stop`), and command discovery pointers.
    - If `--dev` is active, line 1088 outputs `[dev] Dev Mode: ON (agentic diagnostic and mutation plane active)`.
    - If `--allow-bypass` is active, line 1090 issues a prominent security warning that bypass mode is outside the Phase 0-5 security seal.
  - **Session Selector**: `_select_session()` (repl.py:198-227) displays the 10 most recent sessions sorted by modification time. Sanitization is strictly enforced by `sanitize_session_name()` (repl.py:94-121), rejecting directory traversal, control characters, and reserved Windows device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
  - **Host & Engine Initialization**: `open_session()` (repl.py:229-304) instantiates `PDLtHost` in `app.py`. If `session.json` exists, it resolves the prior workspace and invokes `SessionEngine.restore()`. If restoration fails, `PDLtHost.start()` catches the exception gracefully (app.py:108-113), prints `[warn] session state not restorable...`, and falls back to a clean engine.
  - **Confinement Announcement**: `_announce_sandbox()` (repl.py:306-324) queries `engine.sandbox`. If `--sandbox audit-only` was selected or if OS-native confinement cannot apply on the host, a warning is printed before the first user turn.
  - **Initial Prompt Handling**: If `--prompt` or `--prompt-file` is passed, `main()` reads it before the REPL loop (repl.py:1107-1116) and injects it as the first turn.
- **Assessment**: **Sound**, with robust graceful degradation on corrupted session restore.

---

### Dimension 2: Command Parsing and Dispatch
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 601-802, 1118-1405
  - `src/pdl_taskmaster/runtime/session_engine.py`: Lines 1871-1965
- **Detailed Mechanics**:
  - **Command Tokenization**:
    - REPL input is read via `line = _read_repl_input("> ").strip()`.
    - Top-level commands are checked with `line.startswith("/")` (line 1163).
    - Splitting is performed via `parts = line.split(maxsplit=1)` (line 1164) and `cmd = parts[0].lower()`.
    - Arguments are extracted via `arg = parts[1].strip() if len(parts) > 1 else ""`.
  - **Command Routing vs Engine Messages**:
    - REPL commands (`/help`, `/status`, `/dev`, `/timeout`, `/model`, `/config`, `/sandbox`, `/workdir`, `/transcript`, `/session`, `/tokens`, `/worker`, `/new`, `/resume`, `/sessions`) execute directly host-side and execute `continue` to restart the loop.
    - Review gate commands (`/confirm`, `/revise`, `/stop`) pass through the whitelist (repl.py:1396-1405) and are forwarded to `runtime.handle(line)` -> `SessionEngine.handle_user_message(line)`.
    - Plain text (no leading slash) bypasses the slash-command block and flows directly to `runtime.handle(line)` as task prompts, follow-ups, or plain-text review responses (`yes`, `lgtm`, `proceed`).
- **Critical Findings & Deficiencies**:
  - **FINDING-01 (High)**: **Broken Review Command `/cancel`**. In `session_engine.py` line 1917, the engine explicitly implements:
    ```python
    if lower in {"/stop", "stop", "/cancel", "cancel"}:
        return self.handle_explicit_review(Intent.CANCEL)
    ```
    However, in `repl.py` lines 1396-1405:
    ```python
    elif cmd in {"/confirm", "/revise", "/stop"}:
        pass
    else:
        print(f"unknown command: {cmd}", flush=True)
        continue
    if cmd not in {"/confirm", "/revise", "/stop"}:
        continue
    ```
    `/cancel` is omitted from the REPL whitelist! When a user enters `/cancel` at a review gate, the REPL outputs `unknown command: /cancel` and drops the turn.
  - **FINDING-07 (Medium)**: **Lack of `shlex` Tokenization**. `repl.py` does not import or use `shlex`. Naive `str.split()` retains literal quotes in user input (e.g. `/workdir "C:\My Workspaces"` or `/dev set model EXECUTE "deepseek/deepseek-r1"`), corrupting file paths and configuration values.
  - **Synonym Discrepancies**: While plain words (`confirm`, `yes`, `y`, `proceed`, `approved`, `ok`) work at review gates, prepending them with a slash (e.g. `/proceed`, `/yes`, `/accept`) causes `unknown command: ...`.

---

### Dimension 3: Argument and Option Handling
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 344-422, 601-802, 805-992
- **Detailed Mechanics**:
  - **CLI Parser**: `_build_parser()` (lines 805-992) defines 36 flags covering repository layout, worker backend (`api`, `codex`, `recorded`), timeout, token limits, provider pinning (`--api-providers`), reasoning effort (`--api-reasoning-effort`, `--api-reasoning-operation`), model mapping (`--api-model-operation`), render compactness (`--render-compact`), structured outputs (`--api-structured-output`), sandboxing (`--sandbox`, `--worker-sandbox`), and execution controls (`--dev`, `--exit-on-close`).
  - **Runtime Dev Plane (`/dev set`)**:
    - `/dev set provider <p1,p2...>`: parses comma-separated providers, canonicalizes names (e.g. `amazon-bedrock` -> `Amazon Bedrock`), issues warnings on unknown provider names, and mutates `worker.provider_pinning["order"]` (lines 702-720).
    - `/dev set fallbacks <true|false>`: mutates `worker.provider_pinning["allow_fallbacks"]` (lines 721-727).
    - `/dev set model [<op>] <name>`: mutates default or per-operation model (lines 728-741).
    - `/dev set reasoning [<op>] <effort>`: mutates default or per-operation reasoning effort (lines 742-755).
    - `/dev set timeout <seconds>`: mutates `worker.timeout` (lines 756-761).
    - `/dev set max_tokens <int>`: mutates `worker.max_output_tokens` (lines 762-767).
    - `/dev exit-on-close [on|off]`: mutates `runtime.exit_on_close` (lines 630-636).
- **Critical Findings & Deficiencies**:
  - **FINDING-05 (Medium)**: **Mutation Reset on Worker/Session Switch**. When `/worker`, `/new`, or `/resume` is called, `switch_session` re-instantiates workers and runtimes directly from initial CLI `args` (lines 1320-1335). All runtime operational mutations applied via `/dev set` or slash commands are silently discarded.
  - **FINDING-08 (Low)**: **Host Sandbox vs Worker Sandbox Ambiguity**. CLI exposes `--sandbox` (ADR-0021 execution sandbox) and `--worker-sandbox` (Codex worker sandbox). The REPL slash command `/sandbox` operates exclusively on `worker.sandbox_mode`. There is no command or `/dev` inspection property for the host execution sandbox.

---

### Dimension 4: Interactive Input/Output Behavior
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 453-594
  - `tests/test_repl_paste.py`: Lines 1-172
- **Detailed Mechanics**:
  Input reading is implemented in `_read_repl_input(prompt: str = "> ") -> str` across four distinct branches:
  1. **Bracketed Paste Mode**:
     - `_enable_bracketed_paste()` writes ANSI escape sequence `\x1b[?2004h` to stdout at session start (line 1103); `_disable_bracketed_paste()` writes `\x1b[?2004l` at shutdown (line 1464).
     - Lines 485-516 detect `PASTE_START` (`\x1b[200~`) and assemble lines until `PASTE_END` (`\x1b[201~`).
     - Single-line pastes return immediately without confirmation (tested by `test_single_line_bracketed_paste`).
     - Multi-line pastes prompt: `\n[Pasted {line_count} lines. Press Enter to submit, or type /cancel to discard]`. An empty Enter confirms; `/cancel` discards.
  2. **Console Burst Detection** (when bracketed paste is inactive/unsupported):
     - On Windows: `while msvcrt.kbhit(): lines.append(input()); time.sleep(0.02)` (lines 522-527).
     - On POSIX: `select.select([sys.stdin], [], [], 0.0)` with 20ms timeout (lines 528-534).
     - Commit `c33ed3fd`: Lines 538-541 trim empty lines from bursts. If `len(lines) > 1 and len(content) <= 1`, it recognizes that typing Enter on an empty prompt followed by a typed command is not a paste.
  3. **Explicit Multi-line Mode**:
     - Triggered by `/paste`, `"""`, or unclosed `"""...` (lines 558-575).
     - Terminates on matching `"""` (for triple-quotes) or `EOF` / blank line (for `/paste`).
  4. **Backslash Continuation**:
     - Triggered if `raw.endswith("\\")` (lines 578-590). Loops reading `... ` until a line without trailing `\` is received.
  5. **Output Rendering**:
     - In standard mode, deliverables are formatted via `format_friendly_deliverable()` (repl.py:1434), suppressing raw JSON Result IR and highlighting status tags (`[+] R1: satisfied`) and witness reproduction provenance.
     - In Dev Mode, `turn.text` is printed unformatted, accompanied by stage telemetry and per-operation call traces (`repl.py:1431, 1438-1447`).
- **Critical Findings & Deficiencies**:
  - **FINDING-02 (High)**: **Premature Paste Truncation on Blank Lines in `/paste` Mode**. Line 572 checks:
    ```python
    if not raw.startswith('"""') and (sub.strip() in {"EOF", "eof", '"""'} or (not sub.strip() and lines_buf)):
        break
    ```
    Once the first line is buffered (`lines_buf` is non-empty), ANY blank line causes `not sub.strip() and lines_buf` to evaluate to True! The paste mode abruptly breaks, silently truncating code or prompts containing empty lines.
  - **FINDING-03 (High)**: **Console Burst Hang on Windows**. In lines 525-526, `while msvcrt.kbhit(): lines.append(input())`. `msvcrt.kbhit()` returns True when any keypress is buffered, but `input()` blocks until a newline is entered. If a user types quickly or if a paste lacks a trailing newline, `input()` hangs until the user manually presses Enter.
  - **FINDING-06 (Medium)**: **Confirmation Trap with `/confirm`**. Lines 514-515 and 553-554:
    ```python
    if confirm == "/cancel":
        return ""
    if confirm:
        pasted = pasted + "\n" + confirm
    return pasted
    ```
    When prompted `[Pasted N lines. Press Enter to submit...]`, users frequently type `/confirm`. Because `/confirm != "/cancel"`, it is concatenated onto the prompt payload.
  - **FINDING-11 (Informational)**: Backslash continuation line 582 calls `.strip()`, stripping all leading indentation on multi-line continuation lines.

---

### Dimension 5: Command Execution and Task Orchestration
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/app.py`: Lines 141-187
  - `src/pdl_taskmaster/observation/observed_session.py`: Lines 82-166
  - `src/pdl_taskmaster/runtime/session_engine.py`: Lines 1830-1965
- **Detailed Mechanics**:
  - **Protocol Entry Point Injection**: `PDLtHost._ensure_protocol_entry()` (app.py:174-180) checks if the controller is in an initial or closed state. If so, it prepends `$confirm-with-pseudocode ` to trigger protocol compilation rather than direct conversational bypass.
  - **Observed Turn Dispatch**: `ObservedSession.handle_user_message()` (observed_session.py:82-166) wraps every turn:
    - Snapshots controller state before and after.
    - Records events delta from `WorkspaceRun`.
    - Captures model calls, latency, token usage, and sha256 checksums.
    - Emits structured turn records to `JsonlSink`.
  - **SessionEngine Orchestration**:
    - Stage routing: `SessionEngine.handle_user_message()` routes incoming messages based on controller state:
      - Closed/None: evaluates System 1 gating (`ActivationRouteRecipe`). If blocked, halts fail-closed. If direct query, returns bypass answer. If protocol-eligible, creates workspace and initializes controller.
      - Review gates (`PROMPT_REVIEW`, `PLAN_REVIEW`, `WAITING_INPUT`): routes fast-path review decisions (`/confirm`, `/revise`, `/stop`) directly via `handle_explicit_review()`, or dispatches to LLM review interpretation (`INTERPRET_PROMPT_REVIEW`, `INTERPRET_PLAN_REVIEW`, `INTERPRET_EXECUTION_INPUT`).
      - Execution: `_execute()` triggers `EXECUTE`, executes deliverable Python code inside `ExecutionSandbox`, performs Phase 5 substantive verification, and conducts bounded repair loops up to `max_repairs`.
- **Assessment**: **Sound**, compliant with dual-plane governance and ADR-0018/ADR-0020.

---

### Dimension 6: State and Context Persistence Across Commands
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 134-190, 246-289
  - `src/pdl_taskmaster/host/app.py`: Lines 96-125
  - `src/pdl_taskmaster/runtime/session_engine.py`: Lines 405-499
- **Detailed Mechanics**:
  - **Lazy Session Pointer (`session.json`)**:
    - `SessionRuntime._refresh_pointer()` (repl.py:161-179) writes `session.json` containing `session_id`, `workspace_path`, and `workspace_relpath`.
    - Pointers are written lazily only after a workspace materializes on the first protocol turn (verified by `test_new_session_is_lazy_no_fabricated_workspace`).
  - **Session Restoration**:
    - `open_session()` checks for `session.json`. If present, it restores the previous workspace path.
    - `SessionEngine.restore()` inspects turn directories (`turns/turn_<n>`) in descending order to locate the last committed controller state, ensuring chained or interrupted sessions resume accurately.
  - **Transcripts**: `transcript.log` records sequential user messages, assistant deliverables, protocol closure markers, and error events.
- **Critical Findings & Deficiencies**:
  - **FINDING-04 (Medium)**: **Closed File Handle Leak in `/transcript`**. Lines 1256-1265 close `runtime.transcript` before attempting `open()`. An invalid path raises an unhandled `OSError` and permanently disables transcript logging for subsequent turns.

---

### Dimension 7: Success, Failure, and Partial-Failure Paths
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 428-451, 1408-1428
  - `src/pdl_taskmaster/observation/observed_session.py`: Lines 89-166
- **Detailed Mechanics**:
  - **Turn Exception Boundary**: Lines 1408-1428 wrap `runtime.handle(line)`:
    ```python
    try:
        turn = runtime.handle(line)
    except KeyboardInterrupt:
        print("\n[operation interrupted by user]", flush=True)
        _write_transcript("USER_INTERRUPTED")
        if not _is_interactive(args):
            raise
        continue
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        print(f"[error] {_one_line_error(exc)}", flush=True)
        _write_transcript("ERROR> " + message)
        if not _is_interactive(args):
            harness_error = message
            harness_record = _harness_error_record(exc)
            break
        continue
    ```
  - **Provider Error Reporting**: `_one_line_error()` formats concise, non-leaking diagnostic lines (e.g. `PROVIDER_REJECTED_REQUEST at BOOTSTRAP_ANALYSIS: HTTP 404...`) without dumping raw stack traces.
  - **Interactive Recovery**: In interactive mode, errors do not crash the session; the loop continues and permits corrective input.
- **Critical Findings & Deficiencies**:
  - **FINDING-09 (Low)**: **Slash Commands Unprotected by Exception Boundary**. The `try/except` block covers only `runtime.handle(line)`. Slash commands (lines 1163-1405) execute outside any exception wrapper. An unhandled error in a slash command crashes the REPL with a raw traceback.

---

### Dimension 8: Invalid Input and Unknown-Command Handling
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 94-121, 692-770, 1399
  - `src/pdl_taskmaster/runtime/session_engine.py`: Lines 1891-1897
- **Detailed Mechanics**:
  - **Empty / Whitespace Input**: In REPL loop, empty input is ignored (`if not line: continue`). In `SessionEngine` lines 1891-1897, empty input at review gates prompts: `Please confirm the {artifact} (type /confirm...) or specify revisions (/revise <feedback>)`.
  - **Session Name Validation**: `sanitize_session_name()` strictly rejects path traversal, Windows reserved names, and non-ASCII control characters.
  - **Provider Typos**: `unknown_provider_warnings()` uses `difflib.get_close_matches` to suggest corrections (e.g. `"Cerebrus: did you mean Cerebras?"`).
- **Deficiencies**:
  - When an unknown slash command is entered (e.g. `/status` or `/exit`), `repl.py:1399` outputs `unknown command: {cmd}` without providing fuzzy suggestions, despite having `difflib` imported in the project.

---

### Dimension 9: Help, Usage, Discovery, and Command Introspection
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 606-623, 1135-1159
- **Detailed Mechanics**:
  - `/help`: prints the 20-entry command roster.
  - `/dev help`: prints the developer diagnostic and control plane instructions.
  - `/dev status`: outputs a comprehensive JSON snapshot of the session runtime, controller stage, workspace path, and worker settings.
  - `/dev diagnose`: performs a 4-point self-test: Standards Store integrity, API transport credentials, provider pinning configuration, and SessionEngine readiness.
  - `/status`: outputs read-only host status (`active`, `workspace_id`, `workspace_path`, `controller_state`, `refused`).
  - `/session`: prints active session directory.
- **Audit of Roster vs Implementation**:
  - All commands in `/help` correspond to implemented handlers in `repl.py`.
  - However, `/sandbox` in help is described as `show/set worker sandbox mode (codex worker only)`, leaving users without a command to inspect the host execution sandbox (`--sandbox`).

---

### Dimension 10: Exit/Quit Behavior and Cleanup
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 1133-1134, 1361-1380, 1451-1452, 1463-1468
  - `src/pdl_taskmaster/host/app.py`: Lines 200-208
  - `src/pdl_taskmaster/runtime/session_engine.py`: Lines 1595-1598
- **Detailed Mechanics**:
  - Interactive exit via `/quit`, EOF, or `KeyboardInterrupt`.
  - Auto-exit via `runtime.exit_on_close`: breaks loop upon protocol closure (`turn.closed`).
  - Resource cleanup in `finally:` block (repl.py:1463-1468):
    - `_disable_bracketed_paste()`.
    - `runtime.close()` writes `=== PDLt session ended ===\n` and closes transcript.
    - `host.close()` delegates to `engine.close()`, which calls `ExecutionSandbox.close()` to tear down execution environments, followed by `JsonlSink.close()`.
  - Session pruning via `/sessions prune <days>` deletes aged session folders while explicitly preserving `runtime.session_dir` to prevent Windows file-locking crashes (repl.py:1371-1372, tested by `test_sessions_prune_keeps_the_active_session`).
- **Assessment**: **Sound and robustly tested**.

---

### Dimension 11: Error Propagation, Reporting, and Recovery
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 428-451, 1417-1428
  - `src/pdl_taskmaster/observation/observed_session.py`: Lines 89-166
- **Detailed Mechanics**:
  - Provider and wire errors carry structured categories (`OUTPUT_MALFORMED`, `OUTPUT_LIMIT_REACHED`, `PROVIDER_REJECTED_REQUEST`).
  - `_one_line_error()` caps console output at 240 characters.
  - `ObservedSession` isolates observer parsing failures so telemetry parsing glitches never corrupt protocol execution.
- **Assessment**: **Sound**, compliant with telemetry and wire standards.

---

### Dimension 12: Integration with Underlying Components
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`
  - `src/pdl_taskmaster/host/app.py`
  - `src/pdl_taskmaster/runtime/session_engine.py`
  - `src/pdl_taskmaster/verification/sandbox.py`
- **Detailed Mechanics**:
  - Clear architectural boundaries: REPL delegates all protocol transitions to `SessionEngine`, which gates state through `MechanicalController`.
  - Program execution is dispatched to session-scoped `ExecutionSandbox` (ADR-0021), isolating model code from the host filesystem.
  - Semantic worker calls (`ApiWorker`, `CodexWorker`) are strictly decoupled and stateless.
- **Assessment**: **Sound**, cleanly aligned with ADR-0018, ADR-0020, and ADR-0021.

---

### Dimension 13: Non-Interactive and CLI Compatibility
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/cli.py`: Lines 77-122
  - `src/pdl_taskmaster/host/repl.py`: Lines 192-196, 1453-1507
  - `tests/test_repl_integration.py`: Lines 103-165, 215-234
- **Detailed Mechanics**:
  - `_is_interactive(args)` identifies non-interactive runs (`--non-interactive` or piped stdin).
  - Skips interactive session selection menus.
  - Supports automated initial prompt execution via `--prompt` and `--prompt-file`.
  - Enforces ADR-0019 Headless Exit Code Invariants:
    - Code `0`: Completed deliverable (`CLOSED_SUCCESS`) or published boundary refusal (`closure=REFUSED`).
    - Code `1`: Cancelled session (`CLOSED_CANCELLED`).
    - Code `2`: Stalled at non-terminal review gate (e.g. `PROMPT_REVIEW`, `PLAN_REVIEW`).
    - Code `3`: Legitimate pause awaiting external input (`WAITING_INPUT`).
    - Code `4`: Harness or provider infrastructure failure (`EXIT_HARNESS_ERROR`).
    - Code `130`: Interrupted by user (`KeyboardInterrupt`).
  - Headless watchdog (`_arm_exit_watchdog()`): Arms a 20-second faulthandler timer to abort hung shutdown processes with diagnostic thread dumps.
- **Assessment**: **Exemplary**, verified by comprehensive automated tests in `test_repl_integration.py`.

---

### Dimension 14: Extensibility and Architecture for Future Commands
- **Primary Source Files**:
  - `src/pdl_taskmaster/host/repl.py`: Lines 601-802, 1163-1405
- **Detailed Mechanics**:
  - Command handling is implemented as a 240-line `if/elif` ladder in `main()`, paired with a 200-line `if/elif` ladder in `_handle_dev_command()`.
  - There is no command registry, decorator pattern, or modular command handler abstraction.
  - Adding a command requires editing three separate locations (roster string, ladder, and fall-through whitelist), directly causing the `/cancel` omission bug.
- **Assessment**: **Suboptimal maintainability and extensibility**.

---

## Detailed Identification of Stubbed, Mock-Only, or Dead Commands

Acceptance Criteria Check #2 requires identifying any stubbed, mock-only, or dead commands:

1. **Dead / Blocked Command: `/cancel`**:
   - **Location**: `src/pdl_taskmaster/host/repl.py`: Lines 1396-1405.
   - **Backing Implementation**: `src/pdl_taskmaster/runtime/session_engine.py`: Line 1917 (`if lower in {"/stop", "stop", "/cancel", "cancel"}: return self.handle_explicit_review(Intent.CANCEL)`).
   - **Defect**: While fully implemented in `SessionEngine`, `/cancel` is omitted from `repl.py` line 1396 (`elif cmd in {"/confirm", "/revise", "/stop"}: pass`). As a result, entering `/cancel` at a review gate outputs `unknown command: /cancel` and drops the turn.
2. **Missing Host Sandbox Introspection Command**:
   - **Location**: `src/pdl_taskmaster/host/repl.py`: Lines 1226-1240.
   - **Defect**: The command `/sandbox` is documented as `show/set worker sandbox mode (codex worker only)` and only accesses `worker.sandbox_mode`. There is no command (`/sandbox` or `/dev status`) to query or modify the host execution sandbox (`--sandbox auto|native|container|audit-only`).
3. **Unimplemented Review Synonyms**:
   - **Location**: `src/pdl_taskmaster/host/repl.py`: Lines 1396-1405.
   - **Defect**: `SessionEngine` line 1903 implements `proceed`, `yes`, `y`, `looks good`, `lgtm`, `approved`, `ok`, `okay`, `accept`. When typed without a slash, they pass. When typed with a slash (`/proceed`, `/yes`, `/accept`), they are blocked by the REPL as unknown commands.

---

## Paste Detection Deep Dive (`tests/test_repl_paste.py` & `repl.py`)

Acceptance Criteria Check #3 requires an exhaustive evaluation of paste detection, multiline input, and empty Enter handling:

### 1. How Paste Detection Works
- **Bracketed Paste**: At REPL start, `_enable_bracketed_paste()` transmits `\x1b[?2004h`. Supported terminals frame pasted text between `PASTE_START` (`\x1b[200~`) and `PASTE_END` (`\x1b[201~`). If `\n` is present, it displays `[Pasted N lines. Press Enter to submit, or type /cancel to discard]`.
- **Console Burst Detection**: On terminals without bracketed paste, the REPL checks if input lines arrive within 20 milliseconds:
  - Windows: `msvcrt.kbhit()` loop.
  - POSIX: `select.select([sys.stdin], [], [], 0.0)` loop.

### 2. Empty Enter Handling & Commit `c33ed3fd`
- In prior versions, pressing Enter on an empty prompt followed by typing ahead `/confirm` while a turn ran caused the burst detector to buffer two lines (`["", "/confirm"]`), holding the command as `[Pasted 1 lines. Press Enter to submit...]`.
- Commit `c33ed3fd` fixed this via lines 538-541:
  ```python
  content = "\n".join(lines).replace("\r", "").strip().splitlines()
  if len(lines) > 1 and len(content) <= 1:
      raw = content[0].strip() if content else ""
  ```
  Edge blank lines are trimmed. If only one non-empty line exists, it is treated as immediate typed input rather than a paste.

### 3. Edge Cases, Flaws, and Bugs in Paste Handling
1. **The Blank Line Trap in `/paste` Mode (Finding-02)**:
   Lines 572-573: `if not raw.startswith('"""') and (sub.strip() in {"EOF", "eof", '"""'} or (not sub.strip() and lines_buf)): break`.
   Any blank line in a pasted code block or markdown prompt prematurely aborts `/paste` mode, discarding the rest of the text.
2. **Synchronous Hang in Windows Burst Detection (Finding-03)**:
   Lines 525-526: `while msvcrt.kbhit(): lines.append(input())`.
   `msvcrt.kbhit()` triggers on any character, but `input()` blocks until a newline. Incomplete lines or fast typing will hang the REPL until Enter is pressed.
3. **Confirmation Prompt Append Bug (Finding-06)**:
   Typing `/confirm` to submit the paste at the confirmation prompt (`confirm = input("> ")`) results in `\n/confirm` being appended to the prompt payload (lines 515, 554).
4. **Burst Timing Race Condition**:
   A 20ms fixed sleep can fragment large pastes over high-latency SSH relays. Unbuffered lines spill over and are interpreted as confirmation input or subsequent commands.

---

## Actionable Findings by Severity

| ID | Severity | Module & Line Range | Title & Problem Statement | Impact |
|---|---|---|---|---|
| **FINDING-01** | **High** | `src/pdl_taskmaster/host/repl.py`: 1396-1405 | Broken command dispatch for `/cancel` review command | Users cannot cancel a task at review gates using `/cancel` |
| **FINDING-02** | **High** | `src/pdl_taskmaster/host/repl.py`: 558-575 | Premature paste termination on blank lines in `/paste` mode | Pasting code or prompts containing blank lines truncates text |
| **FINDING-03** | **High** | `src/pdl_taskmaster/host/repl.py`: 522-527 | Synchronous blocking hang in Windows burst detection | REPL hangs waiting for extra Enter on incomplete lines |
| **FINDING-04** | **Medium** | `src/pdl_taskmaster/host/repl.py`: 1256-1265 | Unhandled exception and closed stream leak in `/transcript` | Invalid path crashes REPL and breaks transcript logging |
| **FINDING-05** | **Medium** | `src/pdl_taskmaster/host/repl.py`: 1274-1359, 326-336 | Operational mutations silently wiped on `/worker`, `/new`, `/resume` | Model overrides, provider pinning, and timeouts reset to CLI defaults |
| **FINDING-06** | **Medium** | `src/pdl_taskmaster/host/repl.py`: 506-516, 545-555 | Paste confirmation prompt appends `/confirm` into prompt payload | Prompt payload corrupted when user confirms paste with `/confirm` |
| **FINDING-07** | **Medium** | `src/pdl_taskmaster/host/repl.py`: 602, 1164 | Absence of `shlex` argument tokenization | Quoted paths and model names retain literal quotation marks |
| **FINDING-08** | **Low** | `src/pdl_taskmaster/host/repl.py`: 952-969, 1226-1240 | Ambiguity between host execution sandbox and worker sandbox | No REPL command to inspect host execution sandbox status |
| **FINDING-09** | **Low** | `src/pdl_taskmaster/host/repl.py`: 1163-1405 | Slash command handlers execute outside top-level exception boundary | Unexpected errors in slash commands crash REPL with raw traceback |
| **FINDING-10** | **Low** | `src/pdl_taskmaster/host/repl.py`: 601-802, 1163-1405 | Monolithic `if/elif` command ladder | High maintenance burden and fragile command extension |
| **FINDING-11** | **Informational** | `src/pdl_taskmaster/host/repl.py`: 582 | Backslash line continuation strips leading indentation | Multi-line indented Python or YAML loses indentation |

---

## Proposed Remediation and Concrete Test Scenarios

### Concrete Test Scenarios to Add

1. `test_repl_cancel_command_dispatched_at_review_gate`:
   - Simulate a review gate (`PROMPT_REVIEW`).
   - Feed `/cancel` into `_read_repl_input`.
   - Verify that `/cancel` is forwarded to `SessionEngine.handle_user_message` and transitions to `CLOSED_CANCELLED`, without printing `unknown command: /cancel`.
2. `test_paste_mode_preserves_internal_blank_lines`:
   - Feed `"/paste\ndef foo():\n\n    return 42\nEOF\n"` into `_read_repl_input`.
   - Assert `result == "def foo():\n\n    return 42"`.
3. `test_paste_confirm_ignores_typed_confirm_keyword`:
   - Feed a multi-line bracketed paste followed by `"/confirm"` at the confirmation prompt.
   - Assert that the returned text does NOT contain `"\n/confirm"`.
4. `test_worker_switch_preserves_dev_mutations`:
   - Set `/dev set timeout 45.0` and `/dev set model EXECUTE custom/model`.
   - Execute `/worker api`.
   - Verify that `new_worker.timeout == 45.0` and `new_worker.model_by_operation["EXECUTE"] == "custom/model"`.
5. `test_transcript_command_invalid_path_graceful_handling`:
   - Execute `/transcript /invalid\0/path/test.log`.
   - Verify that REPL prints a warning, does not crash with a raw traceback, and preserves the active transcript file handle.

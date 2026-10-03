# IMPL-0010: Sandbox Backends and Execution Budgets

## Status
**Accepted.** Implements [ADR-0021](../0021-session-scoped-os-native-confinement.md), and the execution limits of [ADR-0013](../0013-substantive-correctness-verification.md) P1, [ADR-0015](../0015-model-synthesized-verification-and-confinement-boundaries.md) §1 and [ADR-0017](../0017-dual-plane-runtime-realignment-and-mrv-solver-governance.md) Pillar 4, which ADR-0021 and the budgets below supersede. Recorded 2026-10-03 from the 2.6.0rc1 code. The user guide is `docs/SANDBOX.md`.

## Decision (as implemented)
- **Session layout.**
  - There is one sandbox session per `SessionEngine` (and per grader call), at `<tempdir>/pdlt-sandboxes/<sid>/`, with `owner.json` and `work/`.
  - It is recorded as a `SANDBOX_SESSION` event, and released by `close()` on every REPL exit path.
  - Roots whose owner process is dead are swept when the next session is built.
- **Per-run layout.**
  - Each program gets a fresh `work/run-NNNN-*`, with `TMP`/`TEMP`/`TMPDIR` pointed at its `tmp/`.
  - `work/` is emptied after each run.
  - The interpreter is always `sys._base_executable`.
- **Backends:**

  | Mode | Backend | Mechanism |
  |---|---|---|
  | `native` on Linux | Landlock | Raw syscalls 444/445/446, `PR_SET_NO_NEW_PRIVS`; one ruleset per session; ABI 4+ denies TCP bind and connect; ABI 6+ scopes abstract UNIX sockets and signals. |
  | `native` on macOS | Seatbelt | `/usr/bin/sandbox-exec`, deny-by-default profile, realpath'd `-D` parameters. |
  | `native` on Windows | AppContainer | Per-session profile with modify rights on `work/` only; a `ctypes` `CreateProcessW` launcher with no capabilities, inside the run's Job Object; no child processes. |
  | `container` (opt-in) | docker / podman | One container per session: no network, read-only root, no capabilities, no privilege gain, a process cap, only `work/` mounted. |
  | `audit-only` (opt-out) | none | Audit hook and resource limits only. |

  The mode is chosen by `--sandbox {auto,native,container,audit-only}` (REPL and catalogue runner), defaulting to `PDLT_SANDBOX`; `auto` means `native`.
- **Fail closed.** `run_code` returns `sandbox_unavailable:<reason>`, the engine records `SANDBOX_UNAVAILABLE`, and no repair is spent on it.
- **Audit hook (defense in depth):**
  - denies `ctypes`, `_ctypes`, `cffi`, `_cffi_backend` and sqlite extension loading;
  - confines paths by `realpath` and `commonpath`;
  - denies signals, network and process creation.
- **Execution budgets** (`verification/sandbox.py:402-406`). Steps are executed bytecode instructions of the script's own code; the wall clock is a safety net.

  | Tier | Steps | Wall clock | Memory | Repairs |
  |---|---|---|---|---|
  | `MINIMAL` | 100,000 | 30 s | 256 MB | 1 |
  | `STANDARD` | 10,000,000 | 30 s | 256 MB | 1 |
  | `HEAVY_COMPUTE` | 100,000,000 | 120 s | 512 MB | 2 |

  System 1's `execution_profile` recipe chooses the tier; `--max-repairs` overrides repairs. The engine's sandbox object is built with a 15 s default (`session_engine.py:361`); each run uses its tier's limit.
- **Model-facing text** states capabilities only (`AVAILABLE_EXECUTION_TOOLS`): directory, file, network and process limits, the step budget and how it counts.

## Superseded limits
- ADR-0013 P1 and ADR-0015: Job Objects or rlimits with a 5.0 s timeout and 256 MB.
- ADR-0017 Pillar 4: 15 s for verified-execution tasks.
- The filesystem clause of ADR-0013 P1, which no code enforced before ADR-0021.

## Evidence and platform notes
- **Linux:** Landlock setup costs about 3 ms per session, and per-run medians are within noise of `audit-only`.
- **Container mode:** about 0.3–2 s per session and 100–300 ms per run.
- **Coverage gaps:**
  - Landlock needs Linux 5.13+ and does not cover UDP, pathname UNIX sockets or `fork` (the audit hook covers those);
  - macOS does not enforce `RLIMIT_AS`.
- **Windows:**
  - a per-user Python install needs a one-time ALL APPLICATION PACKAGES grant, recorded with a marker under `~/.pdlt/`;
  - the Microsoft Store Python fails closed;
  - AppContainers cannot open `NUL`.
- **REG-006 (ADR-0017):** naive backtracking over 3,000,000+ states exceeded the old 5 s ceiling.

## Verification
- `tests/test_confinement.py`: an escape suite per backend, with the hook on and off.
- `tests/test_sandbox.py`.
- The CI sandbox matrix: Linux, macOS and Windows, on 3.10–3.14.

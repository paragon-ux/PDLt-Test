# ADR-0021: Session-Scoped OS-Native Confinement

## Status
Accepted. Supersedes the filesystem clause of ADR-0013 P1 ("file writes strictly restricted to an ephemeral scratchpad directory"), which no code enforced.

## Context
`ExecutionSandbox` ran model-authored code in a fresh `python -I -S` process with resource limits, an environment allowlist and an in-process audit hook that denied network and process creation. Nothing confined the filesystem: a program could read and write any file the user could, including `~/.ssh`, `.env` files, the repository and other sessions' workspaces. `ctypes` gets past any audit hook.

Two facts constrain where the sandbox may write:

- The graders, the catalogue runner and the viewer search session and result trees recursively for `current.md`, `current.json`, `events.jsonl` and `controller-state.json`, and the newest file wins; `validate_result_ir` accepts any file under `W-*` as evidence. A model-writable directory inside a session or workspace could plant a deliverable or evidence.
- One engine can span several `W-*` workspaces, so a workspace is not a stable anchor.

ADR-0013 requires zero third-party dependencies.

## Decision
1. **One sandbox session per `SessionEngine`** (and per grader call), built lazily on the first program run: `<tempdir>/pdlt-sandboxes/<sid>/` with `owner.json` (pid, host, backend, and the profile or container to release) and `work/`. The root sits outside every tree the referee reads and is recorded in a `SANDBOX_SESSION` workspace event. `close()` releases it (`SessionEngine.close()` → `PDLtHost.close()`, reached from the REPL's every exit path). Roots whose owner process is dead are swept when the next session is built; `atexit` is not used.
2. **A fresh, empty run directory per program** (`work/run-NNNN-*`, with `TMP`/`TEMP`/`TMPDIR` pointed at its `tmp/`). Everything under `work/` is deleted after each run, so no run sees an earlier one.
3. **One policy per session** (`SandboxPolicy`): write only `work/`; read `work/`, the base interpreter's installation and standard library, and what the OS loader needs; execute only the base interpreter (and its ELF loader); no network; no new processes. Every backend launches `sys._base_executable`, never a virtual-environment shim.
4. **OS-native backends, standard library and `ctypes` only:**

   | Mode | Backend | Mechanism |
   |---|---|---|
   | `native` on Linux | Landlock | Raw syscalls (444/445/446) and `PR_SET_NO_NEW_PRIVS`. The ruleset handles every right the kernel's ABI knows and is built once per session; each child restricts itself after its rlimits and before `exec`. ABI 4+ denies TCP bind/connect; ABI 6+ scopes abstract UNIX sockets and signals. |
   | `native` on macOS | Seatbelt | `/usr/bin/sandbox-exec` with a deny-by-default profile built once per session; paths are realpath'd and passed as `-D` parameters. |
   | `native` on Windows | AppContainer | A per-session AppContainer profile with modify rights on `work/` only, started through a `ctypes` `CreateProcessW` launcher with no capabilities, inside the run's Job Object (created in it), and unable to create child processes. |
   | `container` (opt-in) | docker / podman | One container per session: no network, read-only root, no capabilities, no privilege gain, a process cap, only `work/` mounted. |
   | `audit-only` (opt-out) | none | Today's behaviour: the audit hook and resource limits only. |

   `--sandbox {auto,native,container,audit-only}` (REPL and catalogue runner) selects the mode; `PDLT_SANDBOX` is the default and `auto` means `native`.
5. **Fail closed.** When the selected backend cannot apply, no program runs: `run_code` returns `sandbox_unavailable:<reason>`, the engine records a registered `SANDBOX_UNAVAILABLE` finding and spends no repair on it, `describe()` and `decision_state()` state that no program runs, and the REPL says so at session start. `audit-only` is the only way to run without OS-native confinement, and the REPL warns loudly when it is chosen.
6. **The audit hook stays, as defense in depth**, built from the same policy: it denies native-code imports (`ctypes`, `_ctypes`, `cffi`, `_cffi_backend`, sqlite extension loading), confines file paths by `realpath` and `commonpath`, denies signals, and keeps network and process denial as separate flags.
7. **Model-facing text states capabilities only** (GUARD-01/02): each program runs in its own empty directory and may read and write only there; other files, network access and starting processes are denied.

## Consequences
- **Positive:** a program can no longer read the user's secrets or the repository, or write a deliverable, evidence or another session's files, even with the audit hook defeated. The escape suite (`tests/test_confinement.py`) checks each backend with the hook on and off.
- **Positive:** each run already starts a fresh interpreter, so native confinement adds no measurable per-run cost on Linux (Landlock: setup ~3 ms per session, per-run medians within noise of `audit-only`). The container mode costs ~0.3–2 s per session and ~100–300 ms per run.
- **Negative:** Landlock needs Linux 5.13+ with Landlock enabled; older kernels fail closed (the message names `--sandbox container` and `audit-only`). Landlock does not cover UDP or pathname UNIX sockets and cannot deny `fork`; the audit hook covers those, and exec of anything but the interpreter is denied natively.
- **Negative:** `sandbox-exec` is deprecated by Apple but still supported (Codex CLI, Chromium and Bazel use it). macOS does not enforce `RLIMIT_AS`, so the memory limit is not enforced there.
- **Negative:** on Windows, a per-user Python install is not readable by AppContainers; read and execute are granted to ALL APPLICATION PACKAGES on its prefix once (the Program Files default), with a notice and a marker under `~/.pdlt/`. The Microsoft Store Python cannot be used (it is already packaged) and fails closed.
- **Neutral:** stdlib modules that read system files outside the read set (`/etc/mime.types`, the system time-zone database through `zoneinfo`) fail with `PermissionError`.
- **Neutral:** this is not a VM boundary: CPU and memory side channels and kernel exploits are out of scope; the container mode exists for stronger isolation, and a microVM (ADR-0011) remains roadmap.

# Sandbox guide

This guide explains how PDLt confines the programs that models write: what runs where, what is enforced, how to choose a mode, and how to check it on your machine. The design decision is recorded in [ADR-0021](adr/0021-session-scoped-os-native-confinement.md).

## Is it always on?

Yes, by default. A program either runs confined or it does not run at all. The only way to run without the OS-native sandbox is to opt out explicitly.

| Situation | What happens |
|---|---|
| Default (no flag, `PDLT_SANDBOX` unset) | Mode `auto`, which means native confinement: Landlock on Linux, Seatbelt on macOS, AppContainer on Windows. |
| `--sandbox container` | A docker or podman container. Opt-in. |
| Native confinement cannot apply (Linux before 5.13, no `sandbox-exec`, AppContainer setup failed, Microsoft Store Python, unknown mode) | **Fails closed.** No program runs. The deliverable gets a `SANDBOX_UNAVAILABLE` finding, which is never repaired, because a repair cannot fix the machine. The model is told that code execution is unavailable, and the REPL prints `[warn] code execution unavailable: ...` at session start. |
| `--sandbox audit-only` or `PDLT_SANDBOX=audit-only` | **The only opt-out.** Programs run under the in-process audit hook and the resource limits only. The REPL prints a loud `WARNING`. |

### What it covers

- Every Python block the harness runs from a deliverable (`SessionEngine._run_deliverable_code`).
- The grader's re-run of deliverable code (`graders.py`).
- `run_catalogue.py --sandbox <mode>` passes the mode to both and records it in `RUN_META.json`.

### What it does not cover

- **The codex worker's own commands.** Those run under Codex's own sandbox (`--worker-sandbox`, default `read-only`). The REPL's `/sandbox` command controls that Codex setting, not this sandbox.
- **The harness process itself**, provider API calls, and the test suite.
- **The model's words.** The model has no file or shell tool. It can only touch files through a program the harness runs, and that program is confined.

### When it is built, and the network

- A session that never runs a program never builds a sandbox. The sandbox is built on the first run.
- Network access is always off for programs. `PDLT_SANDBOX_NETWORK` is System 1 routing state only and never opens network access.

## Session lifecycle

One `ExecutionSandbox` belongs to each `SessionEngine` (`session_engine.py`, `self.sandbox = ExecutionSandbox(..., mode=sandbox_mode)`).

### On the first program run

`ExecutionSandbox._ensure_session()` does five things:

1. **Sweeps stale sessions.** It removes session roots whose owner process is dead, for example a harness the catalogue runner killed. It reads each root's `owner.json`. `atexit` is not used, because it does not run when a process is killed.
2. **Creates the session root** at `<system temp>/pdlt-sandboxes/<label>-<random>/`, containing `owner.json` and `work/`. The base directory is private (mode 0700) and must be owned by the current user, so a shared `/tmp` cannot be used to hijack it.
3. **Builds the policy once** (`verification/confinement/policy.py`):
   - Write: `work/` only.
   - Read: `work/`, the base Python install and its standard library, and what the OS loader needs. On Linux that is `/usr`, `/lib*`, `/etc/ld.so.cache`, `/etc/localtime`, `/dev/null` and `/dev/urandom`. Never the home directory, the repository, or `/proc`.
   - Execute: the base interpreter (never a virtual-environment shim) and, on Linux, its ELF loader.
   - Network and process creation: denied.
4. **Prepares the backend.** `backend.prepare(policy)` builds the backend's native state once: the Landlock ruleset, the Seatbelt profile, the AppContainer profile, or the container.
5. **Records it.** A `SANDBOX_SESSION` event is logged in the workspace, and whatever must be released later goes into `owner.json`.

### Each run

`ExecutionSandbox.run_code`:

1. Creates a fresh `work/run-NNNN-xxxxxx/` with its own `tmp/`, and points `TMP`, `TEMP` and `TMPDIR` at that `tmp/`.
2. Writes the model's code to `program.py`. It also writes `_entry.py`, which installs, in order:
   - any limits the backend sets inside the program;
   - the audit hook;
   - the step budget;
   - then runs `program.py` with `exec(compile(...))`, so tracebacks cite the program's own line numbers.
3. Launches `<base python> -I -S -X utf8 -u _entry.py` through the backend, with:
   - empty stdin;
   - an environment allowlist, so API keys are never passed;
   - memory and CPU limits.
4. Deletes everything under `work/` afterwards, so the next run never sees this run's files.

### At session end

`close()` deletes the session root and releases the backend's state (the AppContainer profile or the container). It is called through `PDLtHost.close()` → `SessionEngine.close()` on REPL exit, `/new`, `/resume`, and at the end of a headless run.

### Why the root is not inside the session workspace

The graders, the runner's accounting and the viewer search session directories recursively for files such as `current.md` and `events.jsonl`, and the newest file wins. If a model-writable directory sat inside those trees, a program could plant a fake deliverable or fake evidence. So the sandbox lives under the system temp directory instead. Turns and stages stay owned by the harness, and the sandbox cannot write to them.

## Two layers

### Layer 1: OS-native confinement (the boundary)

This layer holds on its own. The escape tests disable the audit hook and check that every escape is still blocked.

| Backend | How it is applied | What it enforces |
|---|---|---|
| **Landlock** (Linux 5.13+) | The ruleset is built once per session in the host, through raw syscalls via `ctypes`. Each program's forked child sets `no_new_privs` and restricts itself just before `exec`, so the interpreter starts confined. | Filesystem rights from the policy. Exec only of the interpreter, so `/bin/sh` is denied. ABI 4+: TCP bind and connect are denied. ABI 6+: abstract UNIX sockets and signals are scoped to the program. |
| **Seatbelt** (macOS) | A deny-by-default profile, built once per session and self-tested on the first run. Programs run as `sandbox-exec -p <profile> -D ...`. Paths are passed as parameters, never pasted into the profile. | Exec only of the interpreter, and no `fork`. Read only the read set; read and write only `work/`. No network. |
| **AppContainer** (Windows) | One profile per session, `PDLt.Sandbox.<sid>`, with modify rights on `work/` only. Programs start through a `ctypes` `CreateProcessW` launcher (`confinement/winproc.py`) that sets: no capabilities; the run's Job Object at creation; only the pipe handles inherited; no child processes. A per-user Python install gets a one-time read grant, which is announced and recorded under `~/.pdlt/`. | Reads and writes confined by the kernel: the user profile, the repository and other sessions are invisible. No network, including loopback. |
| **Container** (opt-in) | One container per session, started on the first run with no network, a read-only root, `--cap-drop ALL`, `no-new-privileges` and `--pids-limit 64`. Only `work/` is mounted, at `/work`. Each run is an `exec` under `timeout -s KILL`. | The strongest isolation (separate namespaces). It costs about 0.3–2 s once per session and about 100–300 ms per run. Meant for CI and unattended catalogue runs. |

### Layer 2: the audit hook (defense in depth)

The hook runs inside the program's own interpreter and cannot be removed once installed (`verification/sandbox.py`, `_POLICY_PRELUDE`). It:

- denies network access, process creation and signals (`os.kill`, `os.killpg`);
- denies loading native code: `ctypes`, `cffi` and sqlite extensions;
- checks every file operation (`open`, remove, rename, mkdir, chmod, symlink, `shutil.*`, sqlite paths) using `realpath` plus `commonpath`, never a string prefix:
  - writes must stay inside the run directory;
  - reads may also reach the standard library;
  - a path that still contains `..` after resolution is refused;
  - a symlink that points outside the run directory is refused.

Native code can step around an audit hook. That is why the hook is only a backstop and the OS layer is the boundary.

## Limits and outcomes

The per-tier budgets are unchanged: the step budget, the wall-clock limit and the memory limit.

- **Memory:** a Windows Job Object or `RLIMIT_AS`. macOS does not enforce memory limits.
- **CPU-time backstop:** twice the wall-clock limit. It stops a program that a killed host left behind.
- **Timeouts:** they kill the whole process tree.
- **Ctrl-C:** it kills the running program before the interrupt propagates.

Each outcome becomes a finding: `STEP_BUDGET_EXCEEDED`, `WALL_CLOCK_EXCEEDED`, `MEMORY_EXCEEDED`, `PROGRAM_FAILED` or `SANDBOX_UNAVAILABLE`. Every run logs a `SANDBOX_RUN` event that includes the backend.

## Checking it on your machine

**At REPL start:**
- No sandbox line means native confinement is available.
- `[warn] code execution unavailable: ...` means it fails closed on this machine.
- `WARNING: --sandbox audit-only ...` means you opted out.

**After a turn that ran code:** open the workspace's `events.jsonl`.
- `SANDBOX_SESSION` shows the backend, the mode, the session root, and the Landlock ABI or OS version.
- `SANDBOX_RUN` appears once per program, with its outcome and the backend.

**The escape suite:** `pytest tests/test_confinement.py -v` runs it against every backend your machine supports.

**A live check from the REPL.** Asking the model to edit a file directly does not test the sandbox. The model has no file tool, so it will ask you for the file's contents instead. To exercise the sandbox, ask for a program, for example:

> Write a Python program that appends ":)" to the file C:\path\to\README.md and prints the new last line.

Expected result: the file is unchanged, and the run fails with `PermissionError` (finding `PROGRAM_FAILED`). The workspace events show `SANDBOX_SESSION` with your backend and a `SANDBOX_RUN` with a non-zero exit code.

## Known gaps

- **Landlock:** UDP, pathname UNIX sockets and `fork` are blocked by the audit hook only. Kernels before 5.13 fail closed.
- **macOS:** relies on `sandbox-exec`, which is deprecated but still supported, and Apple's `system.sb`. Memory limits are not enforced.
- **Windows:** programs cannot open `NUL`. Each session creates an AppContainer profile, which is deleted at close or by the sweep. A per-user Python install gets a one-time read grant.
- **Python 3.12+:** the step budget is not enforced. This predates the sandbox.
- **Not covered:** CPU and memory side channels, and kernel exploits. Use `--sandbox container` when stronger isolation is needed.
